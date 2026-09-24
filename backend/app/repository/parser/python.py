"""
SVA Python Parser
=================

Extracts structural entities from Python code using Tree-sitter.

Uses tree_sitter 0.26.x API:
    tree_sitter.Query(lang, query_str)
    tree_sitter.QueryCursor(query).matches(node)
"""

from __future__ import annotations

import re
from typing import Sequence

import tree_sitter

from app.repository.parser.base import LanguageParser
from app.repository.parser.models import CodeEntity, EntityType, generate_entity_id
from app.repository.parser.tree_sitter_engine import parse_content, run_query

# Route decorator patterns: @app.get("/path"), @router.post("/path"), etc.
_ROUTE_DECORATOR_PATTERN = re.compile(
    r'\.(?:get|post|put|delete|patch|head|options|route)\s*\(',
    re.IGNORECASE,
)
# Extract HTTP method from decorator text
_HTTP_METHOD_PATTERN = re.compile(
    r'\.(?P<method>get|post|put|delete|patch|head|options|route)\s*\(',
    re.IGNORECASE,
)
# Extract route path from decorator text
_ROUTE_PATH_PATTERN = re.compile(r'["\']([^"\']+)["\']')

# ORM base class patterns for database model detection
_ORM_BASE_PATTERN = re.compile(r'\b(Base|Model|Document|db\.Model|DeclarativeBase)\b')


class PythonParser(LanguageParser):
    """Parses Python source code into structural code entities."""

    @property
    def supported_languages(self) -> frozenset[str]:
        return frozenset({"Python"})

    def parse(
        self,
        repository_id: str,
        analysis_id: str,
        file_path: str,
        language: str,
        content: bytes,
    ) -> Sequence[CodeEntity]:

        tree = parse_content(language, content)
        if not tree:
            return [_parse_error(repository_id, analysis_id, file_path, language, "TREE_SITTER")]

        entities: list[CodeEntity] = []
        node_to_entity_id: dict[int, str] = {}
        seen_node_ids: set[int] = set()

        root = tree.root_node

        # --- Phase 1: Collect decorated_definition nodes for route detection ---
        # We capture decorators first so we can cross-reference when processing functions.
        decorated_nodes: dict[int, str] = {}  # inner_node.id -> decorator_text

        for node, tag in run_query(language, "(decorated_definition (decorator) @dec) @decorated", root):
            if tag == "dec":
                dec_text = node.text.decode("utf-8", errors="replace") if node.text else ""
                # The decorated_definition is the parent of the decorator
                parent = node.parent
                if parent:
                    # Find the actual definition inside the decorated_definition
                    for child in parent.children:
                        if child.type in ("function_definition", "async_function_definition", "class_definition"):
                            decorated_nodes[child.id] = dec_text

        # --- Phase 2: Extract all entities ---
        # Queries: functions, async functions, classes, imports
        queries = [
            "(function_definition name: (identifier) @name) @func",
            "(class_definition name: (identifier) @name superclasses: (argument_list)? @sc) @class",
            "(import_statement) @import",
            "(import_from_statement) @import_from",
        ]

        all_captures: list[tuple[tree_sitter.Node, str]] = []
        for q in queries:
            all_captures.extend(run_query(language, q, root))

        # Sort by byte position for deterministic parent resolution
        all_captures.sort(key=lambda x: (x[0].start_byte, x[0].end_byte))

        def get_parent_entity_id(node: tree_sitter.Node) -> str | None:
            curr = node.parent
            while curr:
                if curr.id in node_to_entity_id:
                    return node_to_entity_id[curr.id]
                curr = curr.parent
            return None

        # Map: node.id -> group's captures
        # We'll process by matching the outer (@func, @class, @import) and inner (@name, @sc) together
        # Since run_query flattens, we pair them by position.
        
        # Re-run to get structured matches
        self._extract_functions(
            repository_id, analysis_id, file_path, language, root,
            decorated_nodes, entities, node_to_entity_id, seen_node_ids,
            get_parent_entity_id
        )
        self._extract_classes(
            repository_id, analysis_id, file_path, language, root,
            decorated_nodes, entities, node_to_entity_id, seen_node_ids,
            get_parent_entity_id
        )
        self._extract_imports(
            repository_id, analysis_id, file_path, language, root,
            entities, seen_node_ids, get_parent_entity_id
        )
        self._extract_routes_from_decorators(
            repository_id, analysis_id, file_path, language, root,
            entities, seen_node_ids, node_to_entity_id
        )

        return entities

    def _extract_functions(
        self,
        repository_id: str,
        analysis_id: str,
        file_path: str,
        language: str,
        root: tree_sitter.Node,
        decorated_nodes: dict[int, str],
        entities: list[CodeEntity],
        node_to_entity_id: dict[int, str],
        seen_node_ids: set[int],
        get_parent_entity_id,
    ) -> None:
        """Extract function and async function definitions."""
        query_str = "(function_definition name: (identifier) @name) @func"
        
        # Re-run as structured matches
        import tree_sitter as ts
        from app.repository.parser.tree_sitter_engine import get_language
        lang = get_language(language)
        if not lang:
            return

        q = ts.Query(lang, query_str)
        cursor = ts.QueryCursor(q)
        for _pat, caps in cursor.matches(root):
            func_nodes = caps.get("func", [])
            name_nodes = caps.get("name", [])
            if not func_nodes or not name_nodes:
                continue
            
            func_node = func_nodes[0]
            name_node = name_nodes[0]
            
            if func_node.id in seen_node_ids:
                continue
            seen_node_ids.add(func_node.id)

            name = name_node.text.decode("utf-8") if name_node.text else "anonymous"
            start_line = func_node.start_point[0] + 1
            end_line = func_node.end_point[0] + 1
            is_async = func_node.parent and func_node.parent.type == "async_function_definition"

            # Is it a method?
            parent = func_node.parent
            if parent and parent.type == "async_function_definition":
                parent = parent.parent  # skip async wrapper
            is_method = (
                parent and parent.type == "block"
                and parent.parent and parent.parent.type == "class_definition"
            )

            # Determine entity type
            if name.startswith("test_") or name == "test":
                e_type = EntityType.TEST
            elif is_method:
                e_type = EntityType.METHOD
            else:
                e_type = EntityType.FUNCTION

            evidence: dict = {}
            if is_async:
                evidence["is_async"] = True

            # Check for decorator evidence
            dec_text = decorated_nodes.get(func_node.id, "")
            if dec_text:
                evidence["decorator"] = dec_text

            e_id = generate_entity_id(repository_id, file_path, e_type, name, start_line)
            node_to_entity_id[func_node.id] = e_id

            entities.append(CodeEntity(
                entity_id=e_id,
                repository_id=repository_id,
                analysis_id=analysis_id,
                file_path=file_path,
                entity_type=e_type,
                name=name,
                start_line=start_line,
                end_line=end_line,
                language=language,
                extraction_method="TREE_SITTER",
                parent_entity_id=get_parent_entity_id(func_node),
                evidence=evidence,
            ))

    def _extract_classes(
        self,
        repository_id: str,
        analysis_id: str,
        file_path: str,
        language: str,
        root: tree_sitter.Node,
        decorated_nodes: dict[int, str],
        entities: list[CodeEntity],
        node_to_entity_id: dict[int, str],
        seen_node_ids: set[int],
        get_parent_entity_id,
    ) -> None:
        """Extract class definitions, detecting database model candidates."""
        import tree_sitter as ts
        from app.repository.parser.tree_sitter_engine import get_language
        lang = get_language(language)
        if not lang:
            return

        q = ts.Query(lang, "(class_definition name: (identifier) @name) @class")
        cursor = ts.QueryCursor(q)
        for _pat, caps in cursor.matches(root):
            class_nodes = caps.get("class", [])
            name_nodes = caps.get("name", [])
            if not class_nodes or not name_nodes:
                continue

            class_node = class_nodes[0]
            name_node = name_nodes[0]

            if class_node.id in seen_node_ids:
                continue
            seen_node_ids.add(class_node.id)

            name = name_node.text.decode("utf-8") if name_node.text else "anonymous"
            start_line = class_node.start_point[0] + 1
            end_line = class_node.end_point[0] + 1

            # Determine entity type
            evidence: dict = {}

            if name.startswith("Test"):
                e_type = EntityType.TEST
            else:
                e_type = EntityType.CLASS
                # Check for database model candidate via superclasses
                sc_node = class_node.child_by_field_name("superclasses")
                if sc_node:
                    sc_text = sc_node.text.decode("utf-8") if sc_node.text else ""
                    if _ORM_BASE_PATTERN.search(sc_text):
                        e_type = EntityType.DATABASE_MODEL
                        evidence = {
                            "inheritance_pattern": sc_text,
                            "source": "class_definition",
                            "note": "Static model declaration detected — not verified at runtime",
                        }

            e_id = generate_entity_id(repository_id, file_path, e_type, name, start_line)
            node_to_entity_id[class_node.id] = e_id

            entities.append(CodeEntity(
                entity_id=e_id,
                repository_id=repository_id,
                analysis_id=analysis_id,
                file_path=file_path,
                entity_type=e_type,
                name=name,
                start_line=start_line,
                end_line=end_line,
                language=language,
                extraction_method="TREE_SITTER",
                parent_entity_id=get_parent_entity_id(class_node),
                evidence=evidence,
            ))

    def _extract_imports(
        self,
        repository_id: str,
        analysis_id: str,
        file_path: str,
        language: str,
        root: tree_sitter.Node,
        entities: list[CodeEntity],
        seen_node_ids: set[int],
        get_parent_entity_id,
    ) -> None:
        """Extract import statements as IMPORT entities."""
        for node, tag in run_query(language, "(import_statement) @import (import_from_statement) @import_from", root):
            if node.id in seen_node_ids:
                continue
            seen_node_ids.add(node.id)

            raw_text = node.text.decode("utf-8", errors="replace") if node.text else ""
            name = raw_text.split("\n")[0].strip()
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1

            e_id = generate_entity_id(repository_id, file_path, EntityType.IMPORT, name, start_line)

            entities.append(CodeEntity(
                entity_id=e_id,
                repository_id=repository_id,
                analysis_id=analysis_id,
                file_path=file_path,
                entity_type=EntityType.IMPORT,
                name=name,
                start_line=start_line,
                end_line=end_line,
                language=language,
                extraction_method="TREE_SITTER",
                parent_entity_id=get_parent_entity_id(node),
                evidence={"raw_import": name},
            ))

    def _extract_routes_from_decorators(
        self,
        repository_id: str,
        analysis_id: str,
        file_path: str,
        language: str,
        root: tree_sitter.Node,
        entities: list[CodeEntity],
        seen_node_ids: set[int],
        node_to_entity_id: dict[int, str],
    ) -> None:
        """Extract API route candidates from route decorators."""
        import tree_sitter as ts
        from app.repository.parser.tree_sitter_engine import get_language
        lang = get_language(language)
        if not lang:
            return

        q = ts.Query(lang, "(decorated_definition (decorator) @dec) @decorated")
        cursor = ts.QueryCursor(q)
        for _pat, caps in cursor.matches(root):
            dec_nodes = caps.get("dec", [])
            decorated_nodes = caps.get("decorated", [])
            if not dec_nodes or not decorated_nodes:
                continue

            dec_node = dec_nodes[0]
            decorated_node = decorated_nodes[0]

            dec_text = dec_node.text.decode("utf-8", errors="replace") if dec_node.text else ""

            # Check if it looks like a route decorator
            if not _ROUTE_DECORATOR_PATTERN.search(dec_text):
                continue

            # Use decorated node id to avoid duplicate route entities
            route_node_id = dec_node.id * 10000 + 99  # synthetic unique ID
            if route_node_id in seen_node_ids:
                continue
            seen_node_ids.add(route_node_id)

            # Extract HTTP method
            method_match = _HTTP_METHOD_PATTERN.search(dec_text)
            http_method = method_match.group("method").upper() if method_match else "UNKNOWN"

            # Extract route path
            path_match = _ROUTE_PATH_PATTERN.search(dec_text)
            route_path = path_match.group(1) if path_match else "UNKNOWN"

            start_line = dec_node.start_point[0] + 1
            end_line = decorated_node.end_point[0] + 1

            name = f"{http_method} {route_path}"
            e_id = generate_entity_id(repository_id, file_path, EntityType.API_ROUTE, name, start_line)

            entities.append(CodeEntity(
                entity_id=e_id,
                repository_id=repository_id,
                analysis_id=analysis_id,
                file_path=file_path,
                entity_type=EntityType.API_ROUTE,
                name=name,
                start_line=start_line,
                end_line=end_line,
                language=language,
                extraction_method="TREE_SITTER",
                evidence={
                    "decorator": dec_text,
                    "http_method": http_method,
                    "route_path": route_path,
                    "source": "decorator",
                    "note": "Static route discovery — not verified at runtime",
                },
            ))


def _parse_error(
    repository_id: str,
    analysis_id: str,
    file_path: str,
    language: str,
    method: str,
) -> CodeEntity:
    return CodeEntity(
        entity_id=generate_entity_id(repository_id, file_path, EntityType.MODULE, "__parse_error__", 0),
        repository_id=repository_id,
        analysis_id=analysis_id,
        file_path=file_path,
        entity_type=EntityType.MODULE,
        name="__parse_error__",
        start_line=0,
        end_line=0,
        language=language,
        extraction_method=method,
        extraction_status="PARSE_ERROR",
    )
