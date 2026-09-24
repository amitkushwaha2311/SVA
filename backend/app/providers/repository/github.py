"""
GitHub Provider — Secure Integration.

Architecture:
  GitHub API (HTTPS) → Resolve commit → Download tarball → Extract safely → RepositorySnapshot

Security controls:
- Only HTTPS GitHub URLs are accepted.
- Credentials (tokens) are never passed to shell commands.
- Credentials are NEVER logged, serialized to responses, or stored in snapshots.
- Downloaded archive is extracted with strict safety checks (no symlinks, no traversal).
- Snapshot identity is always bound to the resolved commit SHA, not the branch name.

Required token scopes (least privilege):
  - contents:read  — to download repository archives
  - (no write scopes are requested or needed)

GitHubApp installation tokens additionally require:
  - contents:read at the installation level
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import httpx

from .base import (
    RepositoryProvider,
    RepositoryMetadata,
    ProviderError,
    AUTHENTICATION_FAILED,
    AUTHORIZATION_FAILED,
    REPOSITORY_NOT_FOUND,
    PROVIDER_UNAVAILABLE,
    RATE_LIMITED,
    COMMIT_NOT_FOUND,
    SNAPSHOT_INTEGRITY_FAILED,
    validate_provider_url,
    validate_commit_sha,
    extract_tarball_safely,
)

logger = logging.getLogger(__name__)

_GITHUB_HOST = "github.com"
_GITHUB_API_BASE = "https://api.github.com"
_ALLOWED_HOSTS = (_GITHUB_HOST,)

# Maximum archive size (100 MB) — prevents memory exhaustion
_MAX_ARCHIVE_BYTES = 100 * 1024 * 1024

# Network timeout for GitHub API calls
_TIMEOUT_SECONDS = 30.0


def _make_headers(token: str) -> dict:
    """Build secure GitHub API headers. Never log this dict."""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "SVA-Integration/1.0",
    }


class GitHubProvider(RepositoryProvider):
    """
    Provider for securely cloning GitHub repositories via the GitHub API.

    Credentials are used only within this class. They must not be:
    - Passed to any subprocess
    - Logged
    - Stored in the snapshot directory
    - Returned via any API response
    - Injected into sandbox environment variables
    """

    def fetch_snapshot(
        self,
        identifier: str,
        revision: str,
        target_dir: Path,
        credential: Optional[str] = None,
    ) -> RepositoryMetadata:
        """
        Fetches the specified GitHub repository at the given revision.

        Flow:
          1. Validate URL (HTTPS, approved host, no embedded credentials)
          2. Resolve the revision to an immutable commit SHA via API
          3. Download the tarball for that exact commit
          4. Safely extract the archive (no symlinks, no traversal)
          5. Return metadata with the resolved commit SHA

        Raises ProviderError on any failure.
        """
        if not credential:
            raise ProviderError(
                AUTHENTICATION_FAILED,
                "GitHub provider requires a credential. None was supplied."
            )

        owner, repo = validate_provider_url(identifier, _ALLOWED_HOSTS)

        resolved_commit = self._resolve_commit(owner, repo, revision, credential)
        validate_commit_sha(resolved_commit)

        archive_data = self._fetch_archive(owner, repo, resolved_commit, credential)
        extract_tarball_safely(archive_data, target_dir)

        return RepositoryMetadata(
            provider="github",
            repository_identifier=identifier,
            default_branch=self._get_default_branch(owner, repo, credential),
            revision=revision,
            resolved_commit=resolved_commit,
            owner=owner,
            repository_name=repo,
            provider_repository_id=f"{owner}/{repo}",
        )

    def _resolve_commit(
        self, owner: str, repo: str, revision: str, token: str
    ) -> str:
        """Resolve a branch/tag/SHA to a full 40-char commit SHA."""
        url = f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/commits/{revision}"
        try:
            with httpx.Client(timeout=_TIMEOUT_SECONDS, follow_redirects=False) as client:
                resp = client.get(url, headers=_make_headers(token))
        except httpx.TimeoutException:
            raise ProviderError(PROVIDER_UNAVAILABLE, "GitHub API timed out.")
        except httpx.RequestError:
            raise ProviderError(PROVIDER_UNAVAILABLE, "GitHub API request failed.")

        _check_response(resp, owner, repo, "resolve commit")
        data = resp.json()
        sha = data.get("sha", "")
        validate_commit_sha(sha)
        return sha

    def _fetch_archive(
        self, owner: str, repo: str, commit_sha: str, token: str
    ) -> bytes:
        """Download the tarball for the given commit SHA."""
        url = f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/tarball/{commit_sha}"
        try:
            with httpx.Client(timeout=_TIMEOUT_SECONDS, follow_redirects=True) as client:
                resp = client.get(url, headers=_make_headers(token))
        except httpx.TimeoutException:
            raise ProviderError(PROVIDER_UNAVAILABLE, "GitHub archive download timed out.")
        except httpx.RequestError:
            raise ProviderError(PROVIDER_UNAVAILABLE, "GitHub archive request failed.")

        _check_response(resp, owner, repo, "fetch archive")

        content = resp.content
        if len(content) > _MAX_ARCHIVE_BYTES:
            raise ProviderError(
                SNAPSHOT_INTEGRITY_FAILED,
                f"Archive exceeds maximum size of {_MAX_ARCHIVE_BYTES} bytes."
            )
        return content

    def _get_default_branch(self, owner: str, repo: str, token: str) -> str:
        """Fetch repository metadata to determine the default branch."""
        url = f"{_GITHUB_API_BASE}/repos/{owner}/{repo}"
        try:
            with httpx.Client(timeout=_TIMEOUT_SECONDS, follow_redirects=False) as client:
                resp = client.get(url, headers=_make_headers(token))
        except Exception:
            return "main"  # Safe fallback — this is non-critical metadata

        if resp.status_code != 200:
            return "main"
        return resp.json().get("default_branch", "main")


def _check_response(resp: httpx.Response, owner: str, repo: str, operation: str) -> None:
    """Translate GitHub API response codes to ProviderError with safe messages."""
    if resp.status_code == 200 or resp.status_code == 201:
        return
    if resp.status_code == 401:
        raise ProviderError(AUTHENTICATION_FAILED, "GitHub authentication failed.")
    if resp.status_code == 403:
        raise ProviderError(AUTHORIZATION_FAILED, "GitHub access forbidden.")
    if resp.status_code == 404:
        raise ProviderError(REPOSITORY_NOT_FOUND, "Repository or reference not found on GitHub.")
    if resp.status_code == 409:
        raise ProviderError(COMMIT_NOT_FOUND, "Commit not found or repository is empty.")
    if resp.status_code == 429:
        raise ProviderError(RATE_LIMITED, "GitHub API rate limit exceeded.")
    if resp.status_code >= 500:
        raise ProviderError(PROVIDER_UNAVAILABLE, "GitHub API returned a server error.")
    raise ProviderError(
        PROVIDER_UNAVAILABLE,
        f"GitHub API returned unexpected status {resp.status_code} for {operation}."
    )
