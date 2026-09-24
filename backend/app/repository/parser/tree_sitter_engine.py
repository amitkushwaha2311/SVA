"""
SVA Tree-sitter Engine
======================

Provides safe initialization and execution of Tree-sitter parsers and queries.

API: tree-sitter 0.26.x
    tree_sitter.Query(lang, query_str)
    tree_sitter.QueryCursor(query).matches(node)
    -> list of (pattern_index, {capture_name: [Node, ...]})
"""

from __future__ import annotations

import tree_sitter

from app.core.logging_config import get_logger

logger = get_logger("repository.parser.tree_sitter")

_LANGUAGES: dict[str, tree_sitter.Language] = {}


def get_language(language_name: str) -> tree_sitter.Language | None:
    """Safely get or initialize a Tree-sitter Language object."""
    if language_name in _LANGUAGES:
        return _LANGUAGES[language_name]

    try:
        if language_name == "Python":
            import tree_sitter_python
            lang = tree_sitter.Language(tree_sitter_python.language())
        elif language_name == "JavaScript":
            import tree_sitter_javascript
            lang = tree_sitter.Language(tree_sitter_javascript.language())
        elif language_name == "TypeScript":
            import tree_sitter_typescript
            lang = tree_sitter.Language(tree_sitter_typescript.language_typescript())
        else:
            return None

        _LANGUAGES[language_name] = lang
        return lang
    except ImportError as e:
        logger.warning("Could not import tree-sitter grammar %s: %s", language_name, e)
        return None
    except Exception as e:
        logger.error("Failed to initialize tree-sitter language %s: %s", language_name, e)
        return None


def parse_content(language_name: str, content: bytes) -> tree_sitter.Tree | None:
    """Parse raw bytes using the specified language grammar."""
    lang = get_language(language_name)
    if not lang:
        return None

    try:
        parser = tree_sitter.Parser(lang)
        return parser.parse(content)
    except Exception as e:
        logger.error("Parser crashed for language %s: %s", language_name, e)
        return None


def run_query(
    language_name: str,
    query_str: str,
    node: tree_sitter.Node,
) -> list[tuple[tree_sitter.Node, str]]:
    """
    Execute a Tree-sitter query and return a flat list of (node, capture_name) pairs.

    Uses tree_sitter.Query + tree_sitter.QueryCursor per the 0.26.x API.
    Returns empty list on any error — never raises.
    """
    lang = get_language(language_name)
    if not lang:
        return []

    try:
        query = tree_sitter.Query(lang, query_str)
        cursor = tree_sitter.QueryCursor(query)
        matches = cursor.matches(node)
        # matches: list of (pattern_index, {capture_name: [Node, ...]})
        results: list[tuple[tree_sitter.Node, str]] = []
        for _pattern_idx, captures_dict in matches:
            for capture_name, nodes in captures_dict.items():
                for n in nodes:
                    results.append((n, capture_name))
        return results
    except tree_sitter.QueryError as e:
        logger.error("Invalid tree-sitter query: %s", e)
        return []
    except Exception as e:
        logger.error("Query execution failed: %s", e)
        return []
