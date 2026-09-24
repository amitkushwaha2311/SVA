"""
SVA Language Detector
=====================

Detects the programming language of a file using:
1. File extension (primary signal, high confidence)
2. Filename patterns (e.g., Dockerfile, Makefile)
3. Shebang line content (for scripts without extension)
4. Content heuristics (limited — fallback only)

SECURITY: This module reads file content through PathGuard only.
It never executes content to detect the language.
"""

from __future__ import annotations

from pathlib import Path

from app.repository.types import Certainty, DetectionMethod, LanguageMatch

# ---------------------------------------------------------------------------
# Extension → Language map
# ---------------------------------------------------------------------------
# Covers the languages most commonly found in software repositories.
# Keys are lowercase extensions including the dot.
# ---------------------------------------------------------------------------

_EXTENSION_MAP: dict[str, str] = {
    # Python
    ".py": "Python",
    ".pyi": "Python",
    ".pyw": "Python",
    # JavaScript
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript",
    # TypeScript
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".mts": "TypeScript",
    ".cts": "TypeScript",
    # Web
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    # JVM
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",
    ".groovy": "Groovy",
    ".clj": "Clojure",
    # .NET
    ".cs": "C#",
    ".fs": "F#",
    ".vb": "Visual Basic",
    # Systems
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".hxx": "C++",
    ".rs": "Rust",
    ".go": "Go",
    ".swift": "Swift",
    ".m": "Objective-C",
    ".mm": "Objective-C++",
    # Shell
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".fish": "Shell",
    ".ps1": "PowerShell",
    ".psm1": "PowerShell",
    ".psd1": "PowerShell",
    # Data / config
    ".json": "JSON",
    ".jsonc": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "INI",
    ".conf": "Config",
    ".env": "Environment",
    ".xml": "XML",
    ".xsd": "XML Schema",
    ".xsl": "XSLT",
    # Documentation
    ".md": "Markdown",
    ".mdx": "MDX",
    ".rst": "reStructuredText",
    ".txt": "Text",
    ".adoc": "AsciiDoc",
    ".asciidoc": "AsciiDoc",
    # Database / schema
    ".sql": "SQL",
    ".graphql": "GraphQL",
    ".gql": "GraphQL",
    ".proto": "Protocol Buffers",
    # Infrastructure
    ".tf": "Terraform",
    ".hcl": "HCL",
    ".nix": "Nix",
    ".bicep": "Bicep",
    # Other languages
    ".rb": "Ruby",
    ".php": "PHP",
    ".lua": "Lua",
    ".r": "R",
    ".R": "R",
    ".dart": "Dart",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hrl": "Erlang",
    ".hs": "Haskell",
    ".lhs": "Haskell",
    ".ml": "OCaml",
    ".mli": "OCaml",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".elm": "Elm",
    ".cr": "Crystal",
    ".nim": "Nim",
    ".zig": "Zig",
    ".jl": "Julia",
    ".pl": "Perl",
    ".pm": "Perl",
    # Templates
    ".j2": "Jinja2",
    ".jinja": "Jinja2",
    ".jinja2": "Jinja2",
    ".tmpl": "Template",
    ".tpl": "Template",
    # Lock files / manifests (treated as config)
    ".lock": "Lock File",
}

# ---------------------------------------------------------------------------
# Filename (no extension) → Language
# ---------------------------------------------------------------------------

_FILENAME_MAP: dict[str, str] = {
    # Docker
    "Dockerfile": "Dockerfile",
    "dockerfile": "Dockerfile",
    # Build systems
    "Makefile": "Makefile",
    "makefile": "Makefile",
    "GNUmakefile": "Makefile",
    "Rakefile": "Ruby",
    "Justfile": "Just",
    "justfile": "Just",
    # Config files without extensions
    ".gitignore": "Git Config",
    ".gitattributes": "Git Config",
    ".gitmodules": "Git Config",
    ".dockerignore": "Docker Config",
    ".npmignore": "npm Config",
    ".eslintrc": "JSON",
    ".babelrc": "JSON",
    ".prettierrc": "JSON",
    # CI/CD
    "Jenkinsfile": "Groovy",
    "Vagrantfile": "Ruby",
    # Python packaging
    "Pipfile": "TOML",
    "poetry.toml": "TOML",
    # Other
    "LICENSE": "Text",
    "LICENCE": "Text",
    "CHANGELOG": "Text",
    "CHANGES": "Text",
    "AUTHORS": "Text",
    "CONTRIBUTORS": "Text",
    "README": "Text",
    "NOTICE": "Text",
    "SECURITY": "Text",
}

# ---------------------------------------------------------------------------
# Shebang → Language  (first line of script files)
# ---------------------------------------------------------------------------

_SHEBANG_PATTERNS: list[tuple[str, str]] = [
    ("python3", "Python"),
    ("python", "Python"),
    ("node", "JavaScript"),
    ("bash", "Shell"),
    ("sh", "Shell"),
    ("zsh", "Shell"),
    ("fish", "Shell"),
    ("ruby", "Ruby"),
    ("perl", "Perl"),
    ("php", "PHP"),
    ("lua", "Lua"),
    ("Rscript", "R"),
]


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class LanguageDetector:
    """
    Determines the programming language of a repository file.

    Detection order (most reliable first):
    1. Exact filename match (e.g., Dockerfile, Makefile)
    2. File extension match
    3. Shebang line (first line of file, if provided)
    4. Content heuristics (minimal — extension is almost always correct)

    All detection is static — no code execution.
    """

    def detect(
        self,
        path: str | Path,
        first_bytes: bytes | None = None,
    ) -> LanguageMatch:
        """
        Detect the language of a file.

        Parameters
        ----------
        path:
            The file path (relative or absolute). Extension and filename
            are read from this, not from the file system.
        first_bytes:
            Optional first N bytes of the file content. Used for
            shebang detection. Safe to pass None.

        Returns
        -------
        LanguageMatch
            The best language match found.
        """
        p = Path(path)
        name = p.name
        suffix = p.suffix.lower()

        # --- 1. Exact filename match (highest confidence) ----------------
        if name in _FILENAME_MAP:
            return LanguageMatch(
                language=_FILENAME_MAP[name],
                detection_method=DetectionMethod.FILENAME,
                certainty=Certainty.DETERMINISTIC,
            )

        # Also check without leading dot for hidden files like .eslintrc
        if name.startswith(".") and name in _FILENAME_MAP:
            return LanguageMatch(
                language=_FILENAME_MAP[name],
                detection_method=DetectionMethod.FILENAME,
                certainty=Certainty.DETERMINISTIC,
            )

        # --- 2. Extension match ------------------------------------------
        if suffix and suffix in _EXTENSION_MAP:
            return LanguageMatch(
                language=_EXTENSION_MAP[suffix],
                detection_method=DetectionMethod.EXTENSION,
                certainty=Certainty.DETERMINISTIC,
            )

        # Handle compound extensions like .tar.gz, .test.js
        # Take the last meaningful extension
        suffixes = p.suffixes
        if len(suffixes) >= 2:
            # e.g., ["test", ".py"] → check ".py"
            for s in reversed(suffixes):
                sl = s.lower()
                if sl in _EXTENSION_MAP:
                    return LanguageMatch(
                        language=_EXTENSION_MAP[sl],
                        detection_method=DetectionMethod.EXTENSION,
                        certainty=Certainty.DETERMINISTIC,
                    )

        # --- 3. Shebang line detection -----------------------------------
        if first_bytes:
            lang = self._detect_shebang(first_bytes)
            if lang:
                return LanguageMatch(
                    language=lang,
                    detection_method=DetectionMethod.SHEBANG,
                    certainty=Certainty.HEURISTIC,
                )

        # --- 4. Unknown --------------------------------------------------
        return LanguageMatch(
            language=None,
            detection_method=DetectionMethod.UNKNOWN,
            certainty=Certainty.HEURISTIC,
        )

    def _detect_shebang(self, first_bytes: bytes) -> str | None:
        """
        Detect language from a shebang line (first line starting with #!).

        Returns language name or None.
        """
        # Only check files that start with a shebang
        if not first_bytes.startswith(b"#!"):
            return None

        # Extract just the first line
        first_line = first_bytes.split(b"\n", 1)[0].decode("utf-8", errors="replace")

        for token, language in _SHEBANG_PATTERNS:
            if token in first_line:
                return language

        return None
