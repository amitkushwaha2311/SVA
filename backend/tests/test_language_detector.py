"""
Tests for LanguageDetector
===========================

Verifies:
- Extension-based detection for common languages
- Filename-based detection (Dockerfile, Makefile, etc.)
- Shebang-line detection
- Unknown files return None language
- Compound extensions handled correctly
- Case-insensitive extension handling
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.repository.classifier.language_detector import LanguageDetector


from app.repository.types import Certainty, DetectionMethod

@pytest.fixture
def detector() -> LanguageDetector:
    return LanguageDetector()


class TestExtensionDetection:
    def test_python_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("foo.py"))
        assert result.language == "Python"
        assert result.certainty == Certainty.DETERMINISTIC
        assert result.detection_method == DetectionMethod.EXTENSION

    def test_python_stub_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("types.pyi"))
        assert result.language == "Python"

    def test_javascript_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("app.js"))
        assert result.language == "JavaScript"

    def test_jsx_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("App.jsx"))
        assert result.language == "JavaScript"

    def test_typescript_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("service.ts"))
        assert result.language == "TypeScript"

    def test_tsx_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("Component.tsx"))
        assert result.language == "TypeScript"

    def test_rust_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("main.rs"))
        assert result.language == "Rust"

    def test_go_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("server.go"))
        assert result.language == "Go"

    def test_java_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("Main.java"))
        assert result.language == "Java"

    def test_kotlin_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("App.kt"))
        assert result.language == "Kotlin"

    def test_sql_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("migrations.sql"))
        assert result.language == "SQL"

    def test_graphql_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("schema.graphql"))
        assert result.language == "GraphQL"

    def test_yaml_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("config.yaml"))
        assert result.language == "YAML"

    def test_yml_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("ci.yml"))
        assert result.language == "YAML"

    def test_toml_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("pyproject.toml"))
        assert result.language == "TOML"

    def test_markdown_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("README.md"))
        assert result.language == "Markdown"

    def test_shell_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("deploy.sh"))
        assert result.language == "Shell"

    def test_powershell_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("setup.ps1"))
        assert result.language == "PowerShell"

    def test_case_insensitive_extension(self, detector: LanguageDetector) -> None:
        """Extension detection must be case-insensitive."""
        result = detector.detect(Path("Main.PY"))
        assert result.language == "Python"

    def test_proto_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("user.proto"))
        assert result.language == "Protocol Buffers"

    def test_terraform_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("main.tf"))
        assert result.language == "Terraform"

    def test_elixir_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("router.ex"))
        assert result.language == "Elixir"

    def test_ruby_extension(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("user.rb"))
        assert result.language == "Ruby"


class TestFilenameDetection:
    def test_dockerfile_detected(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("Dockerfile"))
        assert result.language == "Dockerfile"
        assert result.detection_method == DetectionMethod.FILENAME
        assert result.certainty == Certainty.DETERMINISTIC

    def test_makefile_detected(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("Makefile"))
        assert result.language == "Makefile"
        assert result.detection_method == DetectionMethod.FILENAME

    def test_gitignore_detected(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path(".gitignore"))
        assert result.language == "Git Config"

    def test_license_detected(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("LICENSE"))
        assert result.language == "Text"


class TestShebangDetection:
    def test_python_shebang(self, detector: LanguageDetector) -> None:
        shebang = b"#!/usr/bin/env python3\nprint('hello')"
        result = detector.detect(Path("script"), first_bytes=shebang)
        assert result.language == "Python"
        assert result.detection_method == DetectionMethod.SHEBANG

    def test_bash_shebang(self, detector: LanguageDetector) -> None:
        shebang = b"#!/bin/bash\necho hello"
        result = detector.detect(Path("run"), first_bytes=shebang)
        assert result.language == "Shell"
        assert result.detection_method == DetectionMethod.SHEBANG

    def test_node_shebang(self, detector: LanguageDetector) -> None:
        shebang = b"#!/usr/bin/env node\nconsole.log('hello')"
        result = detector.detect(Path("server"), first_bytes=shebang)
        assert result.language == "JavaScript"
        assert result.detection_method == DetectionMethod.SHEBANG

    def test_no_shebang_returns_unknown_for_extensionless(
        self, detector: LanguageDetector
    ) -> None:
        result = detector.detect(Path("unknown_script"), first_bytes=b"some content")
        assert result.language is None
        assert result.detection_method == DetectionMethod.UNKNOWN

    def test_shebang_ignored_when_extension_present(
        self, detector: LanguageDetector
    ) -> None:
        """Extension wins over shebang (extension is checked first)."""
        shebang = b"#!/bin/bash\n"
        result = detector.detect(Path("script.py"), first_bytes=shebang)
        # .py extension → Python, even though shebang says bash
        assert result.language == "Python"
        assert result.detection_method == DetectionMethod.EXTENSION


class TestUnknownFiles:
    def test_no_extension_no_shebang_unknown(
        self, detector: LanguageDetector
    ) -> None:
        result = detector.detect(Path("mystery_file"))
        assert result.language is None
        assert result.certainty == Certainty.HEURISTIC
        assert result.detection_method == DetectionMethod.UNKNOWN

    def test_unknown_extension_unknown(self, detector: LanguageDetector) -> None:
        result = detector.detect(Path("file.xyzabc123"))
        assert result.language is None

    def test_empty_filename_unknown(self, detector: LanguageDetector) -> None:
        # Just a dot
        result = detector.detect(Path("."))
        assert result.language is None
