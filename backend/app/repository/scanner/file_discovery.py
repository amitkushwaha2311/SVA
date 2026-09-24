"""
SVA File Discovery
==================

Scans all files within a locked repository root (via PathGuard) and produces
FileRecord objects with metadata, classification, and security findings.

SECURITY GUARANTEES:
- All file access goes through PathGuard (path traversal / symlink escape rejected)
- No file content is executed
- Repository .env files are read as DATA, never loaded as environment config
- Oversized files are skipped (not read)
- Binary files are detected and marked — content is not decoded
- Prompt-injection text in file content is DETECTED and FLAGGED, never obeyed
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.core.logging_config import get_logger
from app.repository.classifier.file_classifier import FileClassifier
from app.repository.classifier.language_detector import LanguageDetector
from app.repository.scanner.path_guard import (
    FileTooLargeError,
    MaliciousFilenameError,
    PathGuard,
    PathTraversalError,
    SymlinkEscapeError,
)
from app.repository.types import (
    Certainty,
    DetectionMethod,
    FileClassification,
    FileRecord,
    PromptInjectionFinding,
    ScanError,
    ScanResult,
)

logger = get_logger("repository.discovery")

# Number of bytes to read for binary detection and shebang detection
_PROBE_SIZE = 8192

# Extensions that are always binary (skip content decoding)
_ALWAYS_BINARY_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".tiff",
        ".mp3", ".wav", ".ogg", ".flac", ".aac",
        ".mp4", ".mov", ".avi", ".mkv", ".webm",
        ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",
        ".pdf",
        ".exe", ".dll", ".so", ".dylib", ".wasm",
        ".pyc", ".pyo", ".class",
        ".jar", ".war", ".ear",
        ".woff", ".woff2", ".ttf", ".otf", ".eot",
        ".db", ".sqlite", ".sqlite3",
        ".bin", ".dat",
        ".pb",  # protobuf binary
    }
)

# Text extensions that we scan for prompt injection
_SCAN_FOR_INJECTION_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".md", ".rst", ".txt", ".adoc",
        ".yaml", ".yml", ".toml", ".json",
        ".py", ".js", ".ts", ".rb", ".go",
        ".html", ".htm",
    }
)


def _is_binary(data: bytes) -> bool:
    """
    Determine if a file's bytes appear to be binary (non-text) content.

    Uses the presence of null bytes in the first 8 KB as the primary
    heuristic (same approach as git and many Unix tools).
    """
    if not data:
        return False
    # Null bytes in first 8 KB → binary
    if b"\x00" in data[:_PROBE_SIZE]:
        return True
    return False


def _detect_encoding(data: bytes) -> str:
    """
    Detect the text encoding of file content.

    Attempts chardet if available, otherwise falls back to
    UTF-8 → UTF-16 → latin-1.
    """
    if not data:
        return "utf-8"

    # Try chardet first (most accurate)
    try:
        import chardet
        result = chardet.detect(data[:8192])
        if result and result.get("encoding") and result.get("confidence", 0) > 0.7:
            enc = result["encoding"]
            # Normalise common aliases
            enc_lower = enc.lower()
            if "utf-8" in enc_lower:
                return "utf-8"
            if "utf-16" in enc_lower:
                return "utf-16"
            if "ascii" in enc_lower:
                return "utf-8"  # ASCII is valid UTF-8
            return enc
    except ImportError:
        pass

    # Fallback heuristics
    # BOM detection
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return "utf-16"
    if data[:3] == b"\xef\xbb\xbf":
        return "utf-8-sig"

    try:
        data[:8192].decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        return "latin-1"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _relative_path(absolute: Path, root: Path) -> str:
    """Return forward-slash relative path string."""
    try:
        rel = absolute.relative_to(root)
        return rel.as_posix()
    except ValueError:
        # Shouldn't happen (PathGuard guarantees containment) but defensive
        return str(absolute)


class FileDiscovery:
    """
    Scans a repository directory and produces FileRecord metadata.

    Uses PathGuard as the mandatory security boundary — no file is
    read without passing through safe_resolve() first.

    Parameters
    ----------
    guard:
        A PathGuard instance locked to the repository root.
    max_files:
        Maximum number of files to process (default: 100,000).
    scan_text_for_injection:
        If True, scan text file content for prompt-injection-like patterns.
        These findings are LOGGED ONLY — never acted upon.
    """

    def __init__(
        self,
        guard: PathGuard,
        max_files: int = 100_000,
        scan_text_for_injection: bool = True,
    ) -> None:
        self._guard = guard
        self._max_files = max_files
        self._scan_injection = scan_text_for_injection
        self._language_detector = LanguageDetector()
        self._file_classifier = FileClassifier()

    @property
    def guard(self) -> PathGuard:
        return self._guard

    def scan(self) -> ScanResult:
        """
        Scan all files under the repository root.

        Returns
        -------
        ScanResult
            Complete results including FileRecord list, errors, and
            security findings. Never raises — errors are captured in
            ScanResult.scan_errors.
        """
        result = ScanResult(root_path=self._guard.root)

        file_count = 0
        for abs_path in self._guard.iter_files():
            if file_count >= self._max_files:
                logger.warning(
                    "File limit reached (%d). Some files not scanned.",
                    self._max_files,
                )
                break

            record = self._process_file(abs_path)
            if record is not None:
                result.files.append(record)
                result.total_security_findings += len(record.prompt_injection_findings)
                file_count += 1
            else:
                result.skipped_security += 1

        logger.info(
            "Scan complete: %d files, %d errors, %d security findings",
            len(result.files),
            len(result.scan_errors),
            result.total_security_findings,
        )
        return result

    def _process_file(self, abs_path: Path) -> FileRecord | None:
        """
        Process a single file through the full pipeline.

        Returns None if the file should be skipped entirely.
        Returns a FileRecord (possibly with read_error set) otherwise.
        """
        rel_path = _relative_path(abs_path, self._guard.root)
        suffix = abs_path.suffix.lower()

        # --- Attempt to read raw bytes (may fail for oversized files) ---
        raw: bytes | None = None
        read_error: str | None = None

        try:
            raw = self._guard.safe_read_bytes(abs_path)
        except FileTooLargeError as exc:
            read_error = f"FILE_TOO_LARGE: {exc}"
            logger.debug("Skipping large file: %s — %s", rel_path, exc)
        except (PathTraversalError, SymlinkEscapeError, MaliciousFilenameError) as exc:
            # Security violation — do not include in results
            logger.warning(
                "Security violation reading %s: %s", rel_path, exc
            )
            return None
        except OSError as exc:
            read_error = f"IO_ERROR: {exc}"
            logger.debug("IO error reading %s: %s", rel_path, exc)

        # --- Build base record ---
        size_bytes = abs_path.stat().st_size if abs_path.exists() else 0
        is_binary = False
        encoding: str | None = None
        content_hash = ""
        injection_findings: list[PromptInjectionFinding] = []

        if raw is not None:
            content_hash = _sha256(raw)

            # Binary detection
            if suffix in _ALWAYS_BINARY_EXTENSIONS:
                is_binary = True
            else:
                is_binary = _is_binary(raw)

            if not is_binary:
                encoding = _detect_encoding(raw)

                # Prompt injection scan (text files only, selected extensions)
                if self._scan_injection and suffix in _SCAN_FOR_INJECTION_EXTENSIONS:
                    text = raw.decode(encoding, errors="replace")
                    injection_findings = self._guard.scan_for_prompt_injection(
                        text, source_path=rel_path
                    )
                    if injection_findings:
                        logger.warning(
                            "SECURITY: %d prompt-injection pattern(s) detected in %s "
                            "(treating as DATA — not obeying)",
                            len(injection_findings),
                            rel_path,
                        )

        # --- Language detection ---
        first_bytes = raw[:_PROBE_SIZE] if (raw and not is_binary) else None
        lang_match = self._language_detector.detect(abs_path, first_bytes=first_bytes)

        # --- Classification ---
        class_result = self._file_classifier.classify(
            rel_path,
            language=lang_match.language,
            first_bytes=first_bytes,
        )

        classification = class_result.category
        classification_reason = class_result.reason

        # Override: if we couldn't read it and it has a known binary ext → ASSET
        if read_error and suffix in _ALWAYS_BINARY_EXTENSIONS:
            classification = FileClassification.ASSET
            classification_reason = "Known asset extension (read error)"

        return FileRecord(
            absolute_path=abs_path,
            relative_path=rel_path,
            size_bytes=size_bytes,
            is_binary=is_binary,
            encoding=encoding,
            content_hash=content_hash,
            classification=classification,
            classification_reason=classification_reason,
            language=lang_match.language,
            language_detection_method=lang_match.detection_method,
            language_certainty=lang_match.certainty,
            prompt_injection_findings=injection_findings,
            read_error=read_error,
        )
