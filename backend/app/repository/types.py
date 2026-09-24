"""Repository scanner security types shared across the package."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------


class DetectionMethod(str, Enum):
    EXTENSION = "extension"
    FILENAME = "filename"
    SHEBANG = "shebang"
    CONTENT_HEURISTIC = "content_heuristic"
    UNKNOWN = "unknown"


class Certainty(str, Enum):
    DETERMINISTIC = "deterministic"
    HEURISTIC = "heuristic"


@dataclass(frozen=True)
class LanguageMatch:
    """Result of language detection for a single file."""
    language: str | None
    detection_method: DetectionMethod
    certainty: Certainty


# ---------------------------------------------------------------------------
# File classification
# ---------------------------------------------------------------------------


class FileClassification(str, Enum):
    """
    Semantic classification of a repository file.

    These are structural roles — they say nothing about whether the file
    implements a requirement correctly.
    """

    SOURCE_CODE = "source_code"
    TEST = "test"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    API_SCHEMA = "api_schema"
    DATABASE_SCHEMA = "database_schema"
    INFRASTRUCTURE = "infrastructure"
    BUILD = "build"
    DEPENDENCY_LOCK = "dependency_lock"
    GENERATED = "generated"
    ASSET = "asset"
    VENDOR = "vendor"
    CI_CD = "ci_cd"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ClassificationResult:
    """Result of file classification, including an explainable reason."""
    category: FileClassification
    reason: str


# ---------------------------------------------------------------------------
# Framework and Package Manager Evidence
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FrameworkCandidate:
    """A detected framework with structural evidence."""
    name: str
    evidence_type: str  # e.g., "filename", "dependency"
    evidence_path: str  # e.g., "package.json", "next.config.js"
    reason: str         # e.g., "package.json dependency: next"


@dataclass(frozen=True)
class PackageManagerCandidate:
    """A detected package manager with structural evidence."""
    name: str
    evidence_type: str
    evidence_path: str
    reason: str


# ---------------------------------------------------------------------------
# Prompt injection finding
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PromptInjectionFinding:
    """
    A detected prompt-injection-like pattern found in repository text.

    =========================================================
    CRITICAL SECURITY NOTE
    =========================================================
    This is a DETECTION result ONLY.

    SVA NEVER:
    - executes matched content
    - obeys matched instructions
    - forwards matched text to any AI system as instructions
    - treats matched text as anything other than DATA

    Repository text is DATA. This finding is a flag for the
    security log, not an instruction to SVA.
    =========================================================
    """

    matched_text: str
    start_offset: int
    end_offset: int
    pattern_name: str
    source_path: str  # relative path within repository


# ---------------------------------------------------------------------------
# File record
# ---------------------------------------------------------------------------


@dataclass
class FileRecord:
    """
    Metadata and classification for a single file within a scanned repository.

    Produced by FileDiscovery after PathGuard validation, binary detection,
    encoding detection, hashing, and classification.
    """

    absolute_path: Path
    relative_path: str  # relative to repo root (forward slashes)
    size_bytes: int
    is_binary: bool
    encoding: str | None  # None if binary
    content_hash: str  # SHA-256 hex digest of raw bytes

    # Classification
    classification: FileClassification = FileClassification.UNKNOWN
    classification_reason: str = ""
    language: str | None = None
    language_detection_method: DetectionMethod = DetectionMethod.UNKNOWN
    language_certainty: Certainty = Certainty.HEURISTIC

    # Security
    prompt_injection_findings: list[PromptInjectionFinding] = field(default_factory=list)

    # Error handling
    read_error: str | None = None  # set if the file could not be read

    @property
    def is_readable(self) -> bool:
        return self.read_error is None and not self.is_binary

    @property
    def extension(self) -> str:
        return Path(self.relative_path).suffix.lower()


# ---------------------------------------------------------------------------
# Scan error
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScanError:
    """A non-fatal error encountered during repository scanning."""

    path: str
    error_type: str
    message: str


# ---------------------------------------------------------------------------
# Scan result
# ---------------------------------------------------------------------------


@dataclass
class ScanResult:
    """
    Complete result of scanning a repository.

    Produced by FileDiscovery.scan() after all files have been
    processed through PathGuard, classified, and checked for security issues.
    """

    root_path: Path
    files: list[FileRecord] = field(default_factory=list)
    scan_errors: list[ScanError] = field(default_factory=list)
    skipped_too_large: int = 0
    skipped_security: int = 0
    total_security_findings: int = 0

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def source_files(self) -> list[FileRecord]:
        return [f for f in self.files if f.classification == FileClassification.SOURCE_CODE]

    @property
    def test_files(self) -> list[FileRecord]:
        return [f for f in self.files if f.classification == FileClassification.TEST]

    @property
    def doc_files(self) -> list[FileRecord]:
        return [f for f in self.files if f.classification == FileClassification.DOCUMENTATION]

    @property
    def all_injection_findings(self) -> list[PromptInjectionFinding]:
        findings = []
        for f in self.files:
            findings.extend(f.prompt_injection_findings)
        return findings
