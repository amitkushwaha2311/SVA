"""
SVA File Classifier
===================

Classifies repository files into semantic categories based on:
- Directory path patterns
- Filename patterns
- Extension patterns
- Content signatures

Classification is deterministic and static — no code execution.
Classification order matters: more specific rules take precedence.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.repository.types import ClassificationResult, FileClassification


# ---------------------------------------------------------------------------
# Path component sets used in classification rules
# ---------------------------------------------------------------------------

# Directories that indicate test files
_TEST_DIRS: frozenset[str] = frozenset(
    {
        "test", "tests", "testing",
        "__tests__", "_tests_",
        "spec", "specs",
        "e2e", "integration", "unit", "functional",
        "fixture", "fixtures",
        "testdata", "test_data",
    }
)

# Documentation directories
_DOC_DIRS: frozenset[str] = frozenset(
    {
        "docs", "doc", "documentation",
        "wiki", "guides", "tutorials",
        "examples", "demo",
    }
)

# Infrastructure / DevOps directories
_INFRA_DIRS: frozenset[str] = frozenset(
    {
        "deploy", "deployment", "infra", "infrastructure",
        "k8s", "kubernetes", "helm", "charts",
        "terraform", "ansible", "puppet", "chef",
        "docker", "containers",
        ".devcontainer",
    }
)

# CI/CD directories
_CI_CD_DIRS: frozenset[str] = frozenset(
    {
        ".github", ".gitlab", ".circleci",
    }
)

# Vendor / dependency directories
_VENDOR_DIRS: frozenset[str] = frozenset(
    {
        "vendor", "vendors",
        "third_party", "third-party", "thirdparty",
        "lib", "libs",  # only when combined with other signals
        "extern", "external",
    }
)

# DB/migration directories
_DB_DIRS: frozenset[str] = frozenset(
    {
        "migrations", "migration",
        "alembic", "flyway", "liquibase",
        "db", "database",
        "schema", "schemas",
    }
)

# API / schema directories
_API_DIRS: frozenset[str] = frozenset(
    {
        "api", "apis",
        "openapi", "swagger",
        "proto", "protobuf", "grpc",
        "graphql",
        "contracts",
    }
)


# ---------------------------------------------------------------------------
# Filename prefix/suffix patterns for test files
# ---------------------------------------------------------------------------

_TEST_NAME_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^test_", re.IGNORECASE),        # test_foo.py
    re.compile(r"_test\.", re.IGNORECASE),         # foo_test.py
    re.compile(r"\.test\.", re.IGNORECASE),        # foo.test.js
    re.compile(r"\.spec\.", re.IGNORECASE),        # foo.spec.ts
    re.compile(r"_spec\.", re.IGNORECASE),         # foo_spec.rb
    re.compile(r"^spec_", re.IGNORECASE),          # spec_foo.rb
    re.compile(r"Test\.java$", re.IGNORECASE),     # FooTest.java
    re.compile(r"Tests\.cs$", re.IGNORECASE),      # FooTests.cs
    re.compile(r"Spec\.rb$", re.IGNORECASE),       # FooSpec.rb
]

# Documentation filenames (stem only, case-insensitive)
_DOC_FILENAMES: frozenset[str] = frozenset(
    {
        "readme", "readme.md", "readme.rst", "readme.txt",
        "changelog", "changelog.md", "changes", "history",
        "contributing", "contributing.md",
        "license", "licence", "license.md", "licence.md",
        "authors", "contributors",
        "security", "security.md",
        "notice", "notices",
        "code_of_conduct", "code_of_conduct.md",
        "support", "support.md",
        "faq", "faq.md",
        "todo", "todo.md",
    }
)

# Documentation extensions
_DOC_EXTENSIONS: frozenset[str] = frozenset(
    {".md", ".rst", ".txt", ".adoc", ".asciidoc", ".mdx"}
)

# Configuration extensions
_CONFIG_EXTENSIONS: frozenset[str] = frozenset(
    {".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env"}
)

# Infrastructure-specific filenames
_INFRA_FILENAMES: frozenset[str] = frozenset(
    {
        "dockerfile", "docker-compose.yml", "docker-compose.yaml",
        "docker-compose.override.yml",
        "vagrantfile", "tiltfile",
    }
)

# CI/CD-specific filenames
_CI_CD_FILENAMES: frozenset[str] = frozenset(
    {
        "jenkinsfile", "circleci.yml",
        ".travis.yml", ".travis.yaml", "appveyor.yml",
    }
)

# Build system files
_BUILD_FILENAMES: frozenset[str] = frozenset(
    {
        "makefile", "gnumakefile",
        "rakefile", "justfile",
        "build.gradle", "build.gradle.kts", "settings.gradle",
        "pom.xml", "build.xml",
        "webpack.config.js", "vite.config.js", "vite.config.ts",
        "rollup.config.js",
        "setup.py", "setup.cfg",
    }
)

# Dependency lock files
_LOCK_FILENAMES: frozenset[str] = frozenset(
    {
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
        "poetry.lock", "pipfile.lock", "gemfile.lock",
        "cargo.lock", "go.sum", "composer.lock",
        "pubspec.lock", "mix.lock",
    }
)

# Config-specific filenames (not infrastructure)
_CONFIG_FILENAMES: frozenset[str] = frozenset(
    {
        "pyproject.toml",
        "package.json",
        "pipfile", "poetry.toml",
        "cargo.toml",
        "go.mod",
        "gemfile",
        "composer.json",
        ".eslintrc", ".eslintrc.json", ".eslintrc.js", ".eslintrc.yaml",
        ".prettierrc", ".prettierrc.json",
        ".babelrc", ".babelrc.json",
        "tsconfig.json", "jsconfig.json",
        ".editorconfig", ".gitignore", ".gitattributes",
        ".dockerignore", ".npmignore",
        "renovate.json", ".renovaterc",
        "codecov.yml", "sonar-project.properties",
        "requirements.txt", "requirements-dev.txt",
        "constraints.txt",
        "mypy.ini", ".mypy.ini",
        "pytest.ini", "tox.ini",
    }
)

# Generated file indicators (in filename)
_GENERATED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\.min\.(js|css)$", re.IGNORECASE),
    re.compile(r"\.bundle\.(js|css)$", re.IGNORECASE),
    re.compile(r"\.generated\.", re.IGNORECASE),
    re.compile(r"_generated\.", re.IGNORECASE),
    re.compile(r"\.pb\.go$", re.IGNORECASE),  # protobuf Go
    re.compile(r"_pb2\.py$", re.IGNORECASE),  # protobuf Python
    re.compile(r"\.pb\.swift$", re.IGNORECASE),
]

# Generated file content signatures (first 512 bytes)
_GENERATED_CONTENT_SIGNATURES: list[bytes] = [
    b"// Code generated",          # Go protobuf
    b"# Code generated",           # Python scripts
    b"/* Auto-generated",
    b"// DO NOT EDIT",
    b"# DO NOT EDIT",
    b"// This file is auto-generated",
    b"// Generated by",
    b"// AUTOMATICALLY GENERATED",
]

# Asset extensions
_ASSET_EXTENSIONS: frozenset[str] = frozenset(
    {
        # Images
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
        ".bmp", ".tiff", ".tif", ".avif", ".heic",
        # Fonts
        ".ttf", ".otf", ".woff", ".woff2", ".eot",
        # Audio
        ".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a",
        # Video
        ".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v",
        # Binary data
        ".bin", ".dat", ".db", ".sqlite", ".sqlite3",
        ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",
        ".jar", ".war", ".ear", ".aar",
        ".exe", ".dll", ".so", ".dylib", ".wasm",
        ".pdf", ".docx", ".xlsx", ".pptx",
        ".pyc", ".pyo", ".class",
    }
)

# Schema / API extensions
_SCHEMA_EXTENSIONS: frozenset[str] = frozenset(
    {".graphql", ".gql", ".proto"}
)

_API_SCHEMA_FILENAMES: frozenset[str] = frozenset(
    {
        "openapi.json", "openapi.yaml", "openapi.yml",
        "swagger.json", "swagger.yaml", "swagger.yml",
        "api.yaml", "api.json",
    }
)

# Database extensions
_DB_EXTENSIONS: frozenset[str] = frozenset({".sql"})


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------


class FileClassifier:
    """
    Classifies repository files into semantic categories with explainable reasons.
    """

    def classify(
        self,
        path: str | Path,
        language: str | None = None,
        first_bytes: bytes | None = None,
    ) -> ClassificationResult:
        p = Path(path)
        name = p.name.lower()
        suffix = p.suffix.lower()
        parts_lower = {part.lower() for part in p.parts}

        # ---- 1. Asset (binary extension) --------------------------------
        if suffix in _ASSET_EXTENSIONS:
            return ClassificationResult(
                FileClassification.ASSET,
                f"Matches known asset extension '{suffix}'"
            )

        # ---- 2. Dependency Lock files -----------------------------------
        if name in _LOCK_FILENAMES:
            return ClassificationResult(
                FileClassification.DEPENDENCY_LOCK,
                f"Matches known dependency lock filename '{name}'"
            )

        # ---- 3. Vendor / dependency directories -------------------------
        vendor_match = parts_lower & {v.lower() for v in _VENDOR_DIRS}
        if vendor_match:
            return ClassificationResult(
                FileClassification.VENDOR,
                f"Path contains vendor directory '{next(iter(vendor_match))}'"
            )

        # ---- 4. Generated file patterns ---------------------------------
        gen_reason = self._is_generated(name, first_bytes)
        if gen_reason:
            return ClassificationResult(FileClassification.GENERATED, gen_reason)

        # ---- 5. Test files ----------------------------------------------
        test_reason = self._is_test(p, parts_lower)
        if test_reason:
            return ClassificationResult(FileClassification.TEST, test_reason)

        # ---- 6. Documentation -------------------------------------------
        doc_reason = self._is_documentation(name, suffix, parts_lower)
        if doc_reason:
            return ClassificationResult(FileClassification.DOCUMENTATION, doc_reason)

        # ---- 7. CI/CD ---------------------------------------------------
        ci_cd_reason = self._is_ci_cd(name, parts_lower)
        if ci_cd_reason:
            return ClassificationResult(FileClassification.CI_CD, ci_cd_reason)

        # ---- 8. Infrastructure ------------------------------------------
        infra_reason = self._is_infrastructure(name, suffix, parts_lower)
        if infra_reason:
            return ClassificationResult(FileClassification.INFRASTRUCTURE, infra_reason)

        # ---- 9. Build ---------------------------------------------------
        if name in _BUILD_FILENAMES:
            return ClassificationResult(
                FileClassification.BUILD,
                f"Matches known build file '{name}'"
            )

        # ---- 10. API / Schema -------------------------------------------
        if suffix in _SCHEMA_EXTENSIONS:
            return ClassificationResult(
                FileClassification.API_SCHEMA,
                f"Matches API schema extension '{suffix}'"
            )
        if name in _API_SCHEMA_FILENAMES:
            return ClassificationResult(
                FileClassification.API_SCHEMA,
                f"Matches API schema filename '{name}'"
            )
        api_dir_match = parts_lower & {v.lower() for v in _API_DIRS}
        if api_dir_match and suffix in {".yaml", ".yml", ".json"}:
            return ClassificationResult(
                FileClassification.API_SCHEMA,
                f"Data file in API directory '{next(iter(api_dir_match))}'"
            )

        # ---- 11. Database / Schema --------------------------------------
        if suffix in _DB_EXTENSIONS:
            return ClassificationResult(
                FileClassification.DATABASE_SCHEMA,
                f"Matches database schema extension '{suffix}'"
            )
        db_dir_match = parts_lower & {v.lower() for v in _DB_DIRS}
        if db_dir_match and suffix in {".py", ".sql", ".xml"}:
            return ClassificationResult(
                FileClassification.DATABASE_SCHEMA,
                f"Schema file in database directory '{next(iter(db_dir_match))}'"
            )

        # ---- 12. Configuration ------------------------------------------
        config_reason = self._is_configuration(name, suffix)
        if config_reason:
            return ClassificationResult(FileClassification.CONFIGURATION, config_reason)

        # ---- 13. Source code (recognized language) ----------------------
        if language and language not in {"Text", "Markdown", "reStructuredText",
                                          "AsciiDoc", "MDX", "JSON", "YAML",
                                          "TOML", "INI", "Config", "Environment",
                                          "Lock File", "Git Config", "Docker Config",
                                          "XML", "XML Schema"}:
            return ClassificationResult(
                FileClassification.SOURCE_CODE,
                f"Detected as '{language}' source code"
            )

        # ---- 14. Unknown ------------------------------------------------
        return ClassificationResult(
            FileClassification.UNKNOWN,
            "Could not determine file classification"
        )

    def _is_generated(self, name: str, first_bytes: bytes | None) -> str | None:
        for pattern in _GENERATED_PATTERNS:
            if pattern.search(name):
                return f"Matches generated filename pattern '{pattern.pattern}'"

        if first_bytes:
            sample = first_bytes[:512]
            for sig in _GENERATED_CONTENT_SIGNATURES:
                if sig in sample:
                    return f"Contains generated file content signature"

        return None

    def _is_test(self, path: Path, parts_lower: set[str]) -> str | None:
        test_dirs_lower = {t.lower() for t in _TEST_DIRS}
        match = parts_lower & test_dirs_lower
        if match:
            return f"Located in test directory '{next(iter(match))}'"

        name = path.name
        for pattern in _TEST_NAME_PATTERNS:
            if pattern.search(name):
                return f"Matches test filename pattern '{pattern.pattern}'"

        return None

    def _is_documentation(self, name: str, suffix: str, parts_lower: set[str]) -> str | None:
        if name in _DOC_FILENAMES:
            return f"Matches known documentation filename '{name}'"

        stem = Path(name).stem.lower()
        if stem in _DOC_FILENAMES:
            return f"Matches known documentation stem '{stem}'"

        doc_dirs_lower = {d.lower() for d in _DOC_DIRS}
        match = parts_lower & doc_dirs_lower
        if match and suffix in _DOC_EXTENSIONS:
            return f"Documentation file in '{next(iter(match))}' directory"

        return None

    def _is_ci_cd(self, name: str, parts_lower: set[str]) -> str | None:
        if name in _CI_CD_FILENAMES:
            return f"Matches known CI/CD filename '{name}'"

        match = parts_lower & _CI_CD_DIRS
        if match:
            return f"Located in CI/CD directory '{next(iter(match))}'"

        return None

    def _is_infrastructure(self, name: str, suffix: str, parts_lower: set[str]) -> str | None:
        if name in _INFRA_FILENAMES:
            return f"Matches known infrastructure filename '{name}'"

        match = parts_lower & {d.lower() for d in _INFRA_DIRS}
        if match:
            return f"Located in infrastructure directory '{next(iter(match))}'"

        if suffix in {".tf", ".hcl"}:
            return f"Matches infrastructure extension '{suffix}'"

        if name.startswith("docker-compose"):
            return "Matches docker-compose pattern"

        return None

    def _is_configuration(self, name: str, suffix: str) -> str | None:
        if name in _CONFIG_FILENAMES:
            return f"Matches known configuration filename '{name}'"

        if suffix in _CONFIG_EXTENSIONS:
            return f"Matches configuration extension '{suffix}'"

        return None
