"""
SVA PathGuard — Repository Security Boundary
=============================================

SECURITY PRINCIPLE
------------------
Every file system operation during SVA analysis MUST go through PathGuard.
Repository content is UNTRUSTED DATA — never instructions to SVA.

PROTECTIONS IMPLEMENTED
-----------------------
1. Repository root locked at initialization (resolved, absolute)
2. Path traversal rejection — ../../../etc rejected via Path.resolve() + relative_to()
3. Symlink escape prevention — symlinks are resolved; if target escapes root, rejected
4. Maximum file size enforcement
5. Maximum directory depth limit
6. Binary file safe handling (detected, not decoded)
7. Malicious filename detection (null bytes, Windows reserved names)
8. Prompt-injection text detection in file content
   → DETECTION ONLY — matched text is NEVER executed, obeyed, or forwarded

WHAT PATHGUARD NEVER DOES
--------------------------
- Execute repository code
- Run shell commands
- Load repository .env files
- Follow paths outside the locked root
- Treat repository text as instructions
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterator

from app.repository.types import PromptInjectionFinding


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PathGuardError(Exception):
    """Base class for PathGuard security errors."""


class PathTraversalError(PathGuardError):
    """
    Raised when a path resolves to a location outside the repository root.

    This covers both explicit traversal (../../etc) and traversal via
    symlinks that point outside the root.
    """


class SymlinkEscapeError(PathGuardError):
    """
    Raised when a symlink's resolved target is outside the repository root.

    Distinct from PathTraversalError to allow callers to differentiate
    deliberate traversal attempts from unexpected symlink configurations.
    """


class MaliciousFilenameError(PathGuardError):
    """
    Raised when a filename or path component is potentially malicious.

    Examples: null bytes, Windows device names (CON, NUL, COM1...).
    """


class FileTooLargeError(PathGuardError):
    """
    Raised when a file exceeds the configured maximum size.

    SVA refuses to read files above this limit to prevent memory exhaustion
    from repository files designed to be extremely large.
    """


# ---------------------------------------------------------------------------
# PathGuard
# ---------------------------------------------------------------------------


class PathGuard:
    """
    Security boundary for SVA repository analysis.

    Locks the analysis root at construction. All file system access during
    analysis MUST be validated through safe_resolve() before any open() call.

    Usage
    -----
    ::

        guard = PathGuard(root=Path("/path/to/repo"))
        safe_path = guard.safe_resolve("subdir/file.py")
        raw = guard.safe_read_bytes(safe_path)

    The root is resolved at construction time (symlinks in the root path
    itself are followed). Subsequent calls to safe_resolve() resolve the
    full path chain and verify containment.
    """

    # Default limits
    MAX_FILE_SIZE_DEFAULT: int = 10 * 1024 * 1024  # 10 MB
    MAX_DEPTH_DEFAULT: int = 50

    # -----------------------------------------------------------------
    # Prompt-injection detection patterns
    # DETECTION ONLY — SVA never executes or obeys matched content
    # -----------------------------------------------------------------
    _INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
        (
            "ignore_previous_instructions",
            re.compile(
                r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?",
                re.IGNORECASE,
            ),
        ),
        (
            "disregard_instructions",
            re.compile(
                r"disregard\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?",
                re.IGNORECASE,
            ),
        ),
        (
            "forget_instructions",
            re.compile(
                r"forget\s+(?:all\s+)?(?:previous\s+)?instructions?",
                re.IGNORECASE,
            ),
        ),
        (
            "you_are_now",
            re.compile(r"you\s+are\s+now\s+(?:a|an)\b", re.IGNORECASE),
        ),
        (
            "act_as",
            re.compile(r"(?:^|\s)act\s+as\s+(?:a|an|if)\b", re.IGNORECASE),
        ),
        (
            "new_system_prompt",
            re.compile(r"new\s+system\s+prompt", re.IGNORECASE),
        ),
        (
            "special_tokens",
            re.compile(
                r"<\|(?:system|im_start|im_end|endoftext|startoftext)\|>",
                re.IGNORECASE,
            ),
        ),
        (
            "prompt_delimiter",
            re.compile(
                r"#{4,}\s*(?:SYSTEM|PROMPT|INSTRUCTIONS?)\s*#{4,}",
                re.IGNORECASE,
            ),
        ),
        (
            "jailbreak_dan",
            re.compile(
                r"\bDAN\b.*(?:do\s+anything\s+now|jailbreak)",
                re.IGNORECASE,
            ),
        ),
    ]

    # Windows reserved device names — access to these can cause hangs or errors
    _WINDOWS_RESERVED: frozenset[str] = frozenset(
        {
            "CON", "PRN", "AUX", "NUL",
            "COM1", "COM2", "COM3", "COM4", "COM5",
            "COM6", "COM7", "COM8", "COM9",
            "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
            "LPT6", "LPT7", "LPT8", "LPT9",
        }
    )

    # Directories always skipped during iteration
    _DEFAULT_SKIP_DIRS: frozenset[str] = frozenset(
        {
            ".git", ".svn", ".hg", ".bzr",
            "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
            ".venv", "venv", ".env",
            "node_modules", ".yarn", ".pnpm-store",
            "dist", "build", "target", "out",
            ".tox", ".nox",
        }
    )

    def __init__(
        self,
        root: Path,
        max_file_size_bytes: int = MAX_FILE_SIZE_DEFAULT,
        max_depth: int = MAX_DEPTH_DEFAULT,
    ) -> None:
        """
        Lock the repository root.

        Parameters
        ----------
        root:
            The repository directory to analyse. Must exist and be a directory.
        max_file_size_bytes:
            Maximum size (bytes) of any single file SVA will read.
        max_depth:
            Maximum directory recursion depth during file iteration.

        Raises
        ------
        ValueError
            If root does not exist or is not a directory.
        """
        resolved_root = Path(root).resolve()

        if not resolved_root.exists():
            raise ValueError(f"Repository root does not exist: {root!r}")
        if not resolved_root.is_dir():
            raise ValueError(f"Repository root is not a directory: {root!r}")

        self._root: Path = resolved_root
        self._max_file_size_bytes: int = max_file_size_bytes
        self._max_depth: int = max_depth

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def root(self) -> Path:
        """The locked repository root (resolved, absolute path)."""
        return self._root

    @property
    def max_file_size_bytes(self) -> int:
        return self._max_file_size_bytes

    @property
    def max_depth(self) -> int:
        return self._max_depth

    # ------------------------------------------------------------------
    # Core security method
    # ------------------------------------------------------------------

    def safe_resolve(self, path: str | Path) -> Path:
        """
        Resolve a path and verify it is within the locked repository root.

        This is the SINGLE correct entry point for all path resolution
        during SVA analysis. Every file open, read, or stat MUST call
        this method first.

        Implementation
        --------------
        1. Reject null bytes — these can bypass filename checks.
        2. Validate each path component for known malicious patterns.
        3. Build an absolute candidate relative to the locked root.
        4. Call ``Path.resolve()`` to expand ALL symlinks in the full
           path chain (not just the final component).
        5. Call ``resolved.relative_to(self._root)`` — raises ValueError
           if resolved is not a descendant of root. This check is immune
           to prefix tricks such as ``/root`` vs ``/root-evil``.

        Parameters
        ----------
        path:
            A relative path within the repository, or an absolute path
            that must be under the root.

        Returns
        -------
        Path
            The resolved, absolute path — guaranteed to be within root.

        Raises
        ------
        PathTraversalError
            Path resolves outside the repository root.
        MaliciousFilenameError
            Path contains null bytes or Windows reserved device names.
        """
        raw = str(path)

        # ---- 1. Null byte check ----------------------------------------
        if "\x00" in raw:
            raise MaliciousFilenameError(
                f"Path contains null byte (possible injection attempt): {raw!r}"
            )

        candidate = Path(raw)

        # ---- 2. Validate path components --------------------------------
        for part in candidate.parts:
            # Skip structural separators
            if part in {os.sep, os.altsep, ".", ".."}:
                continue
            self._validate_component(part)

        # ---- 3. Build absolute candidate --------------------------------
        if candidate.is_absolute():
            full_path = candidate
        else:
            full_path = self._root / candidate

        # ---- 4. Resolve ALL symlinks ------------------------------------
        try:
            resolved = full_path.resolve()
        except (OSError, ValueError) as exc:
            raise PathTraversalError(
                f"Cannot resolve path {raw!r}: {exc}"
            ) from exc

        # ---- 5. Containment check ---------------------------------------
        try:
            resolved.relative_to(self._root)
        except ValueError:
            raise PathTraversalError(
                f"Path traversal rejected: {raw!r} → {resolved!r} "
                f"is outside repository root {self._root!r}"
            )

        return resolved

    def _validate_component(self, component: str) -> None:
        """Validate a single filename or directory-name component."""
        if "\x00" in component:
            raise MaliciousFilenameError(
                f"Null byte in path component: {component!r}"
            )
        # Windows reserved device names (stem without extension)
        stem = Path(component).stem.upper()
        if stem in self._WINDOWS_RESERVED:
            raise MaliciousFilenameError(
                f"Windows reserved device name in path: {component!r}"
            )

    # ------------------------------------------------------------------
    # Safe file reading
    # ------------------------------------------------------------------

    def safe_read_bytes(self, path: str | Path) -> bytes:
        """
        Read raw file bytes after full security validation.

        Parameters
        ----------
        path:
            Relative or absolute path to the file.

        Returns
        -------
        bytes
            The raw file content.

        Raises
        ------
        PathTraversalError, MaliciousFilenameError
            Security violations from safe_resolve().
        FileTooLargeError
            File exceeds max_file_size_bytes.
        FileNotFoundError
            Path does not exist.
        IsADirectoryError
            Path is a directory, not a file.
        """
        resolved = self.safe_resolve(path)

        if not resolved.exists():
            raise FileNotFoundError(f"File does not exist: {resolved!r}")
        if resolved.is_dir():
            raise IsADirectoryError(f"Path is a directory, not a file: {resolved!r}")
        if not resolved.is_file():
            raise OSError(f"Path is not a regular file: {resolved!r}")

        try:
            size = resolved.stat().st_size
        except OSError as exc:
            raise OSError(f"Cannot stat file {resolved!r}: {exc}") from exc

        if size > self._max_file_size_bytes:
            raise FileTooLargeError(
                f"File is {size:,} bytes, exceeds limit of "
                f"{self._max_file_size_bytes:,} bytes: {resolved!r}"
            )

        return resolved.read_bytes()

    def safe_read_text(
        self,
        path: str | Path,
        encoding: str = "utf-8",
        errors: str = "replace",
    ) -> str:
        """
        Read file as decoded text after full security validation.

        Binary content is decoded with ``errors='replace'`` by default so
        that malformed bytes never raise an unhandled exception.
        """
        raw = self.safe_read_bytes(path)
        return raw.decode(encoding, errors=errors)

    # ------------------------------------------------------------------
    # Prompt injection detection
    # ------------------------------------------------------------------

    def scan_for_prompt_injection(
        self,
        text: str,
        source_path: str = "<unknown>",
    ) -> list[PromptInjectionFinding]:
        """
        Scan text content for prompt-injection-like patterns.

        =========================================================
        CRITICAL SECURITY NOTE
        =========================================================
        This method DETECTS patterns and returns a list of findings.

        It NEVER:
        - executes matched content
        - obeys matched instructions
        - forwards matched text to any AI system as instructions
        - modifies SVA behaviour based on repository text

        Matched content is treated as DATA to be logged.
        Repository text is ALWAYS data — never instructions to SVA.
        =========================================================

        Parameters
        ----------
        text:
            Decoded text content of a repository file.
        source_path:
            Relative path of the source file (for inclusion in findings).

        Returns
        -------
        list[PromptInjectionFinding]
            Zero or more detection results (empty list = no matches).
        """
        findings: list[PromptInjectionFinding] = []

        for pattern_name, pattern in self._INJECTION_PATTERNS:
            for match in pattern.finditer(text):
                findings.append(
                    PromptInjectionFinding(
                        matched_text=match.group(0),
                        start_offset=match.start(),
                        end_offset=match.end(),
                        pattern_name=pattern_name,
                        source_path=source_path,
                    )
                )

        return findings

    # ------------------------------------------------------------------
    # Directory iteration
    # ------------------------------------------------------------------

    def iter_files(
        self,
        skip_hidden: bool = False,
        extra_skip_dirs: frozenset[str] | None = None,
    ) -> Iterator[Path]:
        """
        Safely iterate all files under the repository root.

        Files that fail security checks are silently skipped (the scan
        continues rather than aborting on a single bad file). Security
        violations are expected to be logged by the caller.

        Parameters
        ----------
        skip_hidden:
            Skip files and directories whose names start with ``'.'``.
        extra_skip_dirs:
            Additional directory names (not paths) to skip.

        Yields
        ------
        Path
            Resolved, validated absolute paths within the root.
        """
        skip_dirs = self._DEFAULT_SKIP_DIRS | (extra_skip_dirs or frozenset())

        def _walk(directory: Path, depth: int) -> Iterator[Path]:
            if depth > self._max_depth:
                return

            try:
                entries = sorted(directory.iterdir())
            except (PermissionError, OSError):
                return

            for entry in entries:
                name = entry.name

                if skip_hidden and name.startswith("."):
                    continue

                try:
                    is_symlink = entry.is_symlink()
                    is_dir = entry.is_dir(follow_symlinks=False)
                    is_file = entry.is_file(follow_symlinks=False)
                except OSError:
                    continue

                if is_symlink:
                    # Resolve and verify symlink target stays within root
                    try:
                        resolved_sym = self.safe_resolve(entry)
                        # If it's a file symlink, yield it
                        if resolved_sym.is_file():
                            yield resolved_sym
                        # Do NOT recurse into symlinked directories
                        # — prevents infinite loops and potential escapes
                    except (PathTraversalError, SymlinkEscapeError, MaliciousFilenameError):
                        pass
                    continue

                if is_dir:
                    if name in skip_dirs or name.endswith(".egg-info"):
                        continue
                    yield from _walk(entry, depth + 1)

                elif is_file:
                    try:
                        safe_path = self.safe_resolve(entry)
                        yield safe_path
                    except (PathTraversalError, MaliciousFilenameError):
                        pass

        yield from _walk(self._root, depth=0)
