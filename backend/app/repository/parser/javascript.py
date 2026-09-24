"""
SVA JavaScript/TypeScript Parser
================================

Extracts structural entities from JS/TS code using Tree-sitter.

Uses tree_sitter 0.26.x API.
"""

from __future__ import annotations

import re
from typing import Sequence

import tree_sitter

from app.repository.parser.base import LanguageParser
from app.repository.parser.models import CodeEntity, EntityType, generate_entity_id
from app.repository.parser.tree_sitter_engine import get_language, parse_content

_HTTP_METHOD_PATTERN = re.compile(
    r'\.(?P<method>get|post|put|delete|patch|all|route)\s*\(',
    re.IGNORECASE,
)
_ROUTE_PATH_PATTERN = re.compile(r'["\']([^"\']+)["\']')


class JavaScriptParser(LanguageParser):
    """Parses JavaScript and TypeScript source code."""

    @property
    def supported_languages(self) -> frozenset[str]:
        return frozenset({"JavaScript", "TypeScript"})

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
            return [_parse_error(repository_id, analysis_id, file_path, language)]

        entities: list[CodeEntity] = []
        node_to_entity_id: dict[int, str] = {}
        seen_node_ids: set[int] = set()

        root = tree.root_node
        lang = get_language(language)
        if not lang:
            return [_parse_error(repository_id, analysis_id, file_path, language)]

        def get_parent_entity_id(node: tree_sitter.Node) -> str | None:
            curr = node.parent
            while curr:
                if curr.id in node_to_entity_id:
                    return node_to_entity_id[curr.id]
                curr = curr.parent
            return None

        # --- Functions ---
        q = tree_sitter.Query(lang, "(function_declaration name: (identifier) @name) @func")
        cursor = tree_sitter.QueryCursor(q)
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
            e_id = generate_entity_id(repository_id, file_path, EntityType.FUNCTION, name, start_line)
            node_to_entity_id[func_node.id] = e_id
            entities.append(CodeEntity(
                entity_id=e_id,
                repository_id=repository_id,
                analysis_id=analysis_id,
                file_path=file_path,
                entity_type=EntityType.FUNCTION,
                name=name,
                start_line=start_line,
                end_line=end_line,
                language=language,
                extraction_method="TREE_SITTER",
                parent_entity_id=get_parent_entity_id(func_node),
            ))

        # --- Arrow functions assigned to variables ---
        q = tree_sitter.Query(lang, "(variable_declarator name: (identifier) @name value: (arrow_function) @arrow) @decl")
        cursor = tree_sitter.QueryCursor(q)
        for _pat, caps in cursor.matches(root):
            arrow_nodes = caps.get("arrow", [])
            name_nodes = caps.get("name", [])
            if not arrow_nodes or not name_nodes:
                continue
            arrow_node = arrow_nodes[0]
            name_node = name_nodes[0]
            if arrow_node.id in seen_node_ids:
                continue
            seen_node_ids.add(arrow_node.id)
            name = name_node.text.decode("utf-8") if name_node.text else "anonymous"
            start_line = arrow_node.start_point[0] + 1
            end_line = arrow_node.end_point[0] + 1
            e_id = generate_entity_id(repository_id, file_path, EntityType.FUNCTION, name, start_line)
            node_to_entity_id[arrow_node.id] = e_id
            entities.append(CodeEntity(
                entity_id=e_id,
                repository_id=repository_id,
                analysis_id=analysis_id,
                file_path=file_path,
                entity_type=EntityType.FUNCTION,
                name=name,
                start_line=start_line,
                end_line=end_line,
                language=language,
                extraction_method="TREE_SITTER",
                parent_entity_id=get_parent_entity_id(arrow_node),
                evidence={"is_arrow": True},
            ))

        # --- Classes ---
        # TypeScript uses type_identifier for class names; JS uses identifier.
        # Try both patterns and deduplicate by node ID.
        class_queries = [
            "(class_declaration name: (identifier) @name) @class",
            "(class_declaration name: (type_identifier) @name) @class",
        ]
        for class_query_str in class_queries:
            try:
                q = tree_sitter.Query(lang, class_query_str)
            except tree_sitter.QueryError:
                continue
            cursor = tree_sitter.QueryCursor(q)
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
                e_id = generate_entity_id(repository_id, file_path, EntityType.CLASS, name, start_line)
                node_to_entity_id[class_node.id] = e_id
                entities.append(CodeEntity(
                    entity_id=e_id,
                    repository_id=repository_id,
                    analysis_id=analysis_id,
                    file_path=file_path,
                    entity_type=EntityType.CLASS,
                    name=name,
                    start_line=start_line,
                    end_line=end_line,
                    language=language,
                    extraction_method="TREE_SITTER",
                    parent_entity_id=get_parent_entity_id(class_node),
                ))

        # --- Methods ---
        q = tree_sitter.Query(lang, "(method_definition name: (property_identifier) @name) @method")
        cursor = tree_sitter.QueryCursor(q)
        for _pat, caps in cursor.matches(root):
            method_nodes = caps.get("method", [])
            name_nodes = caps.get("name", [])
            if not method_nodes or not name_nodes:
                continue
            method_node = method_nodes[0]
            name_node = name_nodes[0]
            if method_node.id in seen_node_ids:
                continue
            seen_node_ids.add(method_node.id)
            name = name_node.text.decode("utf-8") if name_node.text else "anonymous"
            start_line = method_node.start_point[0] + 1
            end_line = method_node.end_point[0] + 1
            e_id = generate_entity_id(repository_id, file_path, EntityType.METHOD, name, start_line)
            node_to_entity_id[method_node.id] = e_id
            entities.append(CodeEntity(
                entity_id=e_id,
                repository_id=repository_id,
                analysis_id=analysis_id,
                file_path=file_path,
                entity_type=EntityType.METHOD,
                name=name,
                start_line=start_line,
                end_line=end_line,
                language=language,
                extraction_method="TREE_SITTER",
                parent_entity_id=get_parent_entity_id(method_node),
            ))

        # --- Imports ---
        q = tree_sitter.Query(lang, "(import_statement) @import")
        cursor = tree_sitter.QueryCursor(q)
        for _pat, caps in cursor.matches(root):
            import_nodes = caps.get("import", [])
            if not import_nodes:
                continue
            imp_node = import_nodes[0]
            if imp_node.id in seen_node_ids:
                continue
            seen_node_ids.add(imp_node.id)
            raw = imp_node.text.decode("utf-8", errors="replace") if imp_node.text else ""
            name = raw.split("\n")[0].strip()
            start_line = imp_node.start_point[0] + 1
            end_line = imp_node.end_point[0] + 1
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
                evidence={"raw_import": name},
            ))

        # --- Exports ---
        q = tree_sitter.Query(lang, "(export_statement) @export")
        cursor = tree_sitter.QueryCursor(q)
        for _pat, caps in cursor.matches(root):
            export_nodes = caps.get("export", [])
            if not export_nodes:
                continue
            exp_node = export_nodes[0]
            if exp_node.id in seen_node_ids:
                continue
            seen_node_ids.add(exp_node.id)
            raw = exp_node.text.decode("utf-8", errors="replace") if exp_node.text else ""
            name = raw.split("\n")[0].strip()
            start_line = exp_node.start_point[0] + 1
            end_line = exp_node.end_point[0] + 1
            e_id = generate_entity_id(repository_id, file_path, EntityType.EXPORT, name, start_line)
            entities.append(CodeEntity(
                entity_id=e_id,
                repository_id=repository_id,
                analysis_id=analysis_id,
                file_path=file_path,
                entity_type=EntityType.EXPORT,
                name=name,
                start_line=start_line,
                end_line=end_line,
                language=language,
                extraction_method="TREE_SITTER",
            ))

        # --- API routes: app.get("/path", ...) / router.post("/path", ...) ---
        q = tree_sitter.Query(lang, """
            (call_expression
                function: (member_expression
                    object: (identifier) @obj
                    property: (property_identifier) @prop
                )
                arguments: (arguments . (_) @first_arg)
            ) @call
        """)
        cursor = tree_sitter.QueryCursor(q)
        for _pat, caps in cursor.matches(root):
            call_nodes = caps.get("call", [])
            prop_nodes = caps.get("prop", [])
            first_arg_nodes = caps.get("first_arg", [])
            if not call_nodes or not prop_nodes:
                continue
            call_node = call_nodes[0]
            prop_node = prop_nodes[0]
            if call_node.id in seen_node_ids:
                continue

            prop_name = prop_node.text.decode("utf-8") if prop_node.text else ""
            if prop_name not in ("get", "post", "put", "delete", "patch", "all", "route"):
                continue

            # Get the first argument as the route path
            route_path = "UNKNOWN"
            if first_arg_nodes:
                arg_text = first_arg_nodes[0].text.decode("utf-8") if first_arg_nodes[0].text else ""
                path_match = _ROUTE_PATH_PATTERN.search(arg_text)
                if path_match:
                    route_path = path_match.group(1)

            seen_node_ids.add(call_node.id)
            http_method = prop_name.upper()
            name = f"{http_method} {route_path}"
            start_line = call_node.start_point[0] + 1
            end_line = call_node.end_point[0] + 1
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
                    "http_method": http_method,
                    "route_path": route_path,
                    "source": "call_expression",
                    "note": "Static route discovery — not verified at runtime",
                },
            ))

        # --- Jest test blocks: describe/test/it ---
        q = tree_sitter.Query(lang, """
            (call_expression
                function: (identifier) @call_name
                arguments: (arguments . (string) @label)
            ) @test_call
        """)
        cursor = tree_sitter.QueryCursor(q)
        for _pat, caps in cursor.matches(root):
            test_call_nodes = caps.get("test_call", [])
            call_name_nodes = caps.get("call_name", [])
            label_nodes = caps.get("label", [])
            if not test_call_nodes or not call_name_nodes:
                continue
            tc_node = test_call_nodes[0]
            cn_node = call_name_nodes[0]
            if tc_node.id in seen_node_ids:
                continue

            call_name = cn_node.text.decode("utf-8") if cn_node.text else ""
            if call_name not in ("describe", "test", "it", "beforeEach", "afterEach", "beforeAll", "afterAll"):
                continue

            # Only add describe/test/it as TEST entities
            if call_name not in ("describe", "test", "it"):
                continue

            seen_node_ids.add(tc_node.id)
            label = ""
            if label_nodes:
                lbl = label_nodes[0].text.decode("utf-8") if label_nodes[0].text else ""
                label = lbl.strip("\"'`")

            name = f"{call_name}({label!r})" if label else call_name
            start_line = tc_node.start_point[0] + 1
            end_line = tc_node.end_point[0] + 1
            e_id = generate_entity_id(repository_id, file_path, EntityType.TEST, name, start_line)
            node_to_entity_id[tc_node.id] = e_id
            entities.append(CodeEntity(
                entity_id=e_id,
                repository_id=repository_id,
                analysis_id=analysis_id,
                file_path=file_path,
                entity_type=EntityType.TEST,
                name=name,
                start_line=start_line,
                end_line=end_line,
                language=language,
                extraction_method="TREE_SITTER",
                parent_entity_id=get_parent_entity_id(tc_node),
            ))

        return entities


def _parse_error(
    repository_id: str,
    analysis_id: str,
    file_path: str,
    language: str,
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
        extraction_method="TREE_SITTER",
        extraction_status="PARSE_ERROR",
    )
