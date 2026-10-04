#!/usr/bin/env python3
"""
SVA Tree-sitter Smoke Test
==========================

Verifies tree-sitter API compatibility before we build the full parser.
Uses the NEW tree-sitter >=0.22 API (not the deprecated build_library approach).

Run with:
    .venv/Scripts/python scripts/treesitter_smoke_test.py
"""

from __future__ import annotations

import sys


def check_import(name: str) -> tuple[bool, str]:
    """Try to import a module and return (success, version_or_error)."""
    try:
        mod = __import__(name.replace("-", "_"))
        ver = getattr(mod, "__version__", "unknown")
        return True, str(ver)
    except ImportError as e:
        return False, str(e)


def test_python_grammar() -> bool:
    """Parse a real Python snippet with tree-sitter-python 0.25+."""
    try:
        import tree_sitter_python as tspython
        from tree_sitter import Language, Parser

        PY_LANGUAGE = Language(tspython.language())
        parser = Parser(PY_LANGUAGE)

        code = b"""
def greet(name: str) -> str:
    '''Return a greeting.'''
    return f"Hello, {name}!"

class Greeter:
    def __init__(self, prefix: str = "Hello") -> None:
        self.prefix = prefix

    def greet(self, name: str) -> str:
        return f"{self.prefix}, {name}!"
"""

        tree = parser.parse(code)

        if tree.root_node is None:
            print("  ✗ Parse returned no root node")
            return False

        root = tree.root_node
        print(f"  ✓ root_node.type    = {root.type!r}")
        print(f"  ✓ root_node.children = {len(root.children)} top-level nodes")

        if root.has_error:
            print("  ⚠ Parse tree has errors (unexpected for valid Python)")
        else:
            print("  ✓ No parse errors")

        # Verify we can walk the tree
        func_defs = [
            n for n in root.children if n.type == "function_definition"
        ]
        class_defs = [
            n for n in root.children if n.type == "class_definition"
        ]
        print(f"  ✓ top-level function_definitions: {len(func_defs)}")
        print(f"  ✓ top-level class_definitions:    {len(class_defs)}")

        if len(func_defs) != 1 or len(class_defs) != 1:
            print("  ✗ Expected exactly 1 function and 1 class at top level")
            return False

        return True

    except Exception as exc:
        print(f"  ✗ Python grammar test FAILED: {exc}")
        return False


def test_javascript_grammar() -> bool:
    """Parse a JS snippet with tree-sitter-javascript 0.25+."""
    try:
        import tree_sitter_javascript as tsjs
        from tree_sitter import Language, Parser

        JS_LANGUAGE = Language(tsjs.language())
        parser = Parser(JS_LANGUAGE)

        code = b"""
function greet(name) {
    return `Hello, ${name}!`;
}

const arrow = (x) => x * 2;

class Greeter {
    constructor(prefix) {
        this.prefix = prefix;
    }
    greet(name) {
        return `${this.prefix}, ${name}!`;
    }
}
"""

        tree = parser.parse(code)
        root = tree.root_node

        if root is None:
            print("  ✗ Parse returned no root node")
            return False

        print(f"  ✓ root_node.type     = {root.type!r}")
        print(f"  ✓ child count        = {len(root.children)}")

        if root.has_error:
            print("  ⚠ Parse tree has errors")
        else:
            print("  ✓ No parse errors")

        return True

    except Exception as exc:
        print(f"  ✗ JavaScript grammar test FAILED: {exc}")
        return False


def test_error_recovery() -> bool:
    """Verify tree-sitter handles malformed code without crashing SVA."""
    try:
        import tree_sitter_python as tspython
        from tree_sitter import Language, Parser

        PY_LANGUAGE = Language(tspython.language())
        parser = Parser(PY_LANGUAGE)

        # Deliberately malformed code
        bad_code = b"def (\n\n\n\n@@@INVALID@@@ class {"

        tree = parser.parse(bad_code)
        root = tree.root_node

        # Should not raise — tree-sitter always returns a tree
        if root is None:
            print("  ✗ Parser returned None root for malformed code")
            return False

        # Malformed code should produce error nodes
        print(f"  ✓ Malformed code parsed without exception")
        print(f"  ✓ root.has_error = {root.has_error} (expected True)")
        return True

    except Exception as exc:
        print(f"  ✗ Error recovery test FAILED: {exc}")
        return False


def main() -> int:
    print("=" * 60)
    print("SVA Tree-sitter Smoke Test")
    print("=" * 60)

    # 1. Version check
    print("\n[1] Module versions")
    results: dict[str, tuple[bool, str]] = {}
    for mod in ["tree_sitter", "tree_sitter_python", "tree_sitter_javascript"]:
        ok, info = check_import(mod)
        results[mod] = (ok, info)
        mark = "✓" if ok else "✗"
        print(f"  {mark} {mod}: {info}")

    if not results["tree_sitter"][0]:
        print("\nFATAL: tree_sitter not importable — cannot continue.")
        return 1

    # 2. Python grammar
    print("\n[2] Python grammar (tree-sitter-python 0.25+)")
    py_ok = test_python_grammar()

    # 3. JavaScript grammar
    print("\n[3] JavaScript grammar (tree-sitter-javascript 0.25+)")
    js_ok = test_javascript_grammar()

    # 4. Error recovery
    print("\n[4] Error recovery (malformed code must not crash)")
    err_ok = test_error_recovery()

    # 5. Summary
    print("\n" + "=" * 60)
    all_ok = py_ok and js_ok and err_ok
    if all_ok:
        print("RESULT: ALL TESTS PASSED — tree-sitter API is compatible")
        print("Safe to proceed with SVA parser implementation.")
    else:
        failures = []
        if not py_ok:
            failures.append("Python grammar")
        if not js_ok:
            failures.append("JavaScript grammar")
        if not err_ok:
            failures.append("Error recovery")
        print(f"RESULT: FAILURES — {', '.join(failures)}")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
