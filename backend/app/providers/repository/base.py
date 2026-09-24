"""
Provider Base Abstraction — Phase 18C Extension.

Extends the existing RepositoryProvider with methods for external provider
authentication, commit resolution, and archive-based snapshot fetching.

Security principles:
- Credentials only pass through the provider integration layer.
- Only HTTPS URLs with explicitly validated structure are accepted.
- Snapshots are always bound to a resolved immutable commit SHA.
"""

from __future__ import annotations

import abc
import hashlib
import io
import re
import tarfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


class RepositoryMetadata:
    """Normalized metadata for a repository returned by a provider."""

    def __init__(
        self,
        provider: str,
        repository_identifier: str,
        default_branch: str,
        revision: str,
        resolved_commit: str,
        owner: str = "",
        repository_name: str = "",
        provider_repository_id: str = "",
    ) -> None:
        self.provider = provider
        self.repository_identifier = repository_identifier
        self.default_branch = default_branch
        self.revision = revision
        self.resolved_commit = resolved_commit
        self.owner = owner
        self.repository_name = repository_name
        self.provider_repository_id = provider_repository_id


class IngestionError(Exception):
    """Base exception for provider ingestion failures."""
    pass


class ProviderError(IngestionError):
    """Structured provider error with a machine-readable reason."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason  # e.g. "AUTHENTICATION_FAILED", "REPOSITORY_NOT_FOUND"


# Reasons must match those defined in the phase spec:
AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
REPOSITORY_NOT_FOUND = "REPOSITORY_NOT_FOUND"
PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
RATE_LIMITED = "RATE_LIMITED"
INVALID_REFERENCE = "INVALID_REFERENCE"
COMMIT_NOT_FOUND = "COMMIT_NOT_FOUND"
WEBHOOK_INVALID = "WEBHOOK_INVALID"
WEBHOOK_REPLAY = "WEBHOOK_REPLAY"
CONNECTION_REVOKED = "CONNECTION_REVOKED"
UNSUPPORTED = "UNSUPPORTED"
INTERNAL_ERROR = "INTERNAL_ERROR"
SNAPSHOT_INTEGRITY_FAILED = "SNAPSHOT_INTEGRITY_FAILED"

# ─── URL Validation ────────────────────────────────────────────────────────────

_SAFE_SHA_RE = re.compile(r'^[0-9a-f]{40}$')
_SAFE_REF_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._/\-]{0,254}$')
# Forbidden characters in URLs that indicate injection, not URL structure.
# These must never appear in a validated repository URL.
_FORBIDDEN_CHARS_RE = re.compile(r'[\x00-\x1f\x7f;|&$`!{}()]')


def validate_provider_url(url: str, allowed_hosts: tuple[str, ...]) -> tuple[str, str]:
    """
    Strictly validate a GitHub/GitLab HTTPS URL.

    Returns: (owner, repo_name)
    Raises: ProviderError if invalid.
    """
    if not url or not isinstance(url, str):
        raise ProviderError(INVALID_REFERENCE, "Repository URL is empty or invalid.")

    # Reject any string with control characters
    if _FORBIDDEN_CHARS_RE.search(url):
        raise ProviderError(INVALID_REFERENCE, "Repository URL contains forbidden characters.")

    parsed = urlparse(url)

    # Strict scheme enforcement
    if parsed.scheme != "https":
        raise ProviderError(
            INVALID_REFERENCE,
            f"Unsupported URL scheme: {parsed.scheme!r}. Only HTTPS is permitted."
        )

    # No embedded credentials
    if parsed.username or parsed.password:
        raise ProviderError(
            INVALID_REFERENCE,
            "Embedded credentials in repository URL are forbidden."
        )

    # Host must be an approved provider host
    host = parsed.netloc.lower().split(":")[0]  # strip optional port
    if host not in allowed_hosts:
        raise ProviderError(
            INVALID_REFERENCE,
            f"Host {host!r} is not an approved provider host."
        )

    # Path must be /owner/repo or /owner/repo.git
    path = parsed.path.rstrip("/").removesuffix(".git")
    parts = [p for p in path.split("/") if p]
    if len(parts) < 2:
        raise ProviderError(
            INVALID_REFERENCE,
            "Repository URL must have the form https://host/owner/repo"
        )

    owner, repo = parts[0], parts[1]

    # Check for option injection
    if url.startswith("--") or url.startswith("-"):
        raise ProviderError(INVALID_REFERENCE, "URL cannot start with hyphens (option injection).")

    return owner, repo


def validate_commit_sha(sha: str) -> None:
    """Enforce that a string looks like a full 40-char SHA."""
    if not _SAFE_SHA_RE.match(sha):
        raise ProviderError(
            SNAPSHOT_INTEGRITY_FAILED,
            "Resolved commit SHA has unexpected format. Refusing to continue."
        )


def verify_archive_member_safety(member: tarfile.TarInfo) -> bool:
    """
    Returns True only if a tar member is safe to extract.
    Rejects: absolute paths, path traversal, symlinks, devices, etc.
    """
    # Reject absolute paths
    if member.name.startswith("/"):
        return False

    # Reject path traversal
    norm = Path(member.name)
    for part in norm.parts:
        if part == "..":
            return False

    # Reject special types
    if member.issym() or member.islnk() or member.isdev() or member.isfifo():
        return False

    return True


def extract_tarball_safely(data: bytes, target_dir: Path) -> None:
    """
    Extract a tar.gz archive into target_dir with strict safety checks:
    - No absolute paths
    - No path traversal
    - No symlinks, hard links, devices, or FIFOs
    - All paths confined within target_dir
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        members = tf.getmembers()

        # Safety-check all members first before extracting anything
        for member in members:
            if not verify_archive_member_safety(member):
                raise ProviderError(
                    SNAPSHOT_INTEGRITY_FAILED,
                    f"Archive member {member.name!r} failed safety check. Refusing extraction."
                )

        # Strip the root directory from paths (GitHub/GitLab include repo-sha/ prefix)
        for member in members:
            parts = Path(member.name).parts
            if len(parts) > 1:
                member.name = str(Path(*parts[1:]))
            elif member.isdir():
                continue  # Skip the root directory itself

            tf.extract(member, target_dir, set_attrs=False)


class RepositoryProvider(abc.ABC):
    """
    Abstract interface for repository providers (Local, Git, GitHub, GitLab).

    Providers are responsible for:
    1. Validating the repository reference.
    2. Resolving the reference to an immutable commit SHA.
    3. Fetching the archive for that commit.
    4. Constructing a clean, immutable snapshot directory.

    CRITICAL: Provider credentials must never enter the Docker sandbox.
    Provider network access is only permitted outside the sandbox.
    """

    @abc.abstractmethod
    def fetch_snapshot(
        self,
        identifier: str,
        revision: str,
        target_dir: Path,
        credential: Optional[str] = None,
    ) -> RepositoryMetadata:
        """
        Fetch the requested revision into target_dir and return its metadata.

        This MUST:
        - Resolve the actual commit hash.
        - Bind the snapshot to that resolved commit.
        - Never allow malicious filesystem escapes.
        - Never expose credential to logs or subprocesses.
        """
        pass
