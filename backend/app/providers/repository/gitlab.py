"""
GitLab Provider — Secure Integration.

Architecture:
  GitLab API (HTTPS) → Resolve commit → Download archive → Extract safely → RepositorySnapshot

Security controls:
- Only HTTPS GitLab.com URLs are accepted (self-hosted domains configurable via GITLAB_HOST).
- Credentials (tokens) are never passed to shell commands.
- Credentials are NEVER logged, serialized to responses, or stored in snapshots.
- Downloaded archive is extracted with strict safety checks (no symlinks, no traversal).
- Snapshot identity is always bound to the resolved commit SHA, not the branch name.

Required token scopes (least privilege):
  - read_api — to read repository data and commits
  - read_repository — to download archives
  - (no write scopes are requested or needed)
"""

from __future__ import annotations

import logging
import urllib.parse
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

_GITLAB_HOST = "gitlab.com"
_GITLAB_API_BASE = "https://gitlab.com/api/v4"
_ALLOWED_HOSTS = (_GITLAB_HOST,)

_MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
_TIMEOUT_SECONDS = 30.0


def _make_headers(token: str) -> dict:
    """Build secure GitLab API headers. Never log this dict."""
    return {
        "PRIVATE-TOKEN": token,
        "User-Agent": "SVA-Integration/1.0",
    }


class GitLabProvider(RepositoryProvider):
    """
    Provider for securely cloning GitLab repositories via the GitLab API.

    Credentials are used only within this class.
    They must not be passed to subprocesses, logged, or exposed via API.
    """

    def fetch_snapshot(
        self,
        identifier: str,
        revision: str,
        target_dir: Path,
        credential: Optional[str] = None,
    ) -> RepositoryMetadata:
        """
        Fetches the specified GitLab repository at the given revision.

        Flow:
          1. Validate URL (HTTPS, approved host, no embedded credentials)
          2. Resolve revision to immutable commit SHA via API
          3. Download archive for that exact commit
          4. Safely extract the archive (no symlinks, no traversal)
          5. Return metadata with the resolved commit SHA
        """
        if not credential:
            raise ProviderError(
                AUTHENTICATION_FAILED,
                "GitLab provider requires a credential. None was supplied."
            )

        owner, repo = validate_provider_url(identifier, _ALLOWED_HOSTS)
        project_path = urllib.parse.quote(f"{owner}/{repo}", safe="")

        resolved_commit = self._resolve_commit(project_path, revision, credential)
        validate_commit_sha(resolved_commit)

        archive_data = self._fetch_archive(project_path, resolved_commit, credential)
        extract_tarball_safely(archive_data, target_dir)

        return RepositoryMetadata(
            provider="gitlab",
            repository_identifier=identifier,
            default_branch=self._get_default_branch(project_path, credential),
            revision=revision,
            resolved_commit=resolved_commit,
            owner=owner,
            repository_name=repo,
            provider_repository_id=f"{owner}/{repo}",
        )

    def _resolve_commit(
        self, project_path: str, revision: str, token: str
    ) -> str:
        """Resolve a branch/tag/SHA to a full 40-char commit SHA."""
        url = f"{_GITLAB_API_BASE}/projects/{project_path}/repository/commits/{revision}"
        try:
            with httpx.Client(timeout=_TIMEOUT_SECONDS, follow_redirects=False) as client:
                resp = client.get(url, headers=_make_headers(token))
        except httpx.TimeoutException:
            raise ProviderError(PROVIDER_UNAVAILABLE, "GitLab API timed out.")
        except httpx.RequestError:
            raise ProviderError(PROVIDER_UNAVAILABLE, "GitLab API request failed.")

        _check_response(resp, project_path, "resolve commit")
        data = resp.json()
        sha = data.get("id", "")
        validate_commit_sha(sha)
        return sha

    def _fetch_archive(
        self, project_path: str, commit_sha: str, token: str
    ) -> bytes:
        """Download the archive for the given commit SHA."""
        url = f"{_GITLAB_API_BASE}/projects/{project_path}/repository/archive.tar.gz"
        try:
            with httpx.Client(timeout=_TIMEOUT_SECONDS, follow_redirects=True) as client:
                resp = client.get(
                    url,
                    headers=_make_headers(token),
                    params={"sha": commit_sha},
                )
        except httpx.TimeoutException:
            raise ProviderError(PROVIDER_UNAVAILABLE, "GitLab archive download timed out.")
        except httpx.RequestError:
            raise ProviderError(PROVIDER_UNAVAILABLE, "GitLab archive request failed.")

        _check_response(resp, project_path, "fetch archive")
        content = resp.content
        if len(content) > _MAX_ARCHIVE_BYTES:
            raise ProviderError(
                SNAPSHOT_INTEGRITY_FAILED,
                f"Archive exceeds maximum allowed size of {_MAX_ARCHIVE_BYTES} bytes."
            )
        return content

    def _get_default_branch(self, project_path: str, token: str) -> str:
        """Fetch project metadata to determine the default branch."""
        url = f"{_GITLAB_API_BASE}/projects/{project_path}"
        try:
            with httpx.Client(timeout=_TIMEOUT_SECONDS, follow_redirects=False) as client:
                resp = client.get(url, headers=_make_headers(token))
        except Exception:
            return "main"
        if resp.status_code != 200:
            return "main"
        return resp.json().get("default_branch", "main")


def _check_response(resp: httpx.Response, project: str, operation: str) -> None:
    """Translate GitLab API response codes to ProviderError with safe messages."""
    if resp.status_code == 200 or resp.status_code == 201:
        return
    if resp.status_code == 401:
        raise ProviderError(AUTHENTICATION_FAILED, "GitLab authentication failed.")
    if resp.status_code == 403:
        raise ProviderError(AUTHORIZATION_FAILED, "GitLab access forbidden.")
    if resp.status_code == 404:
        raise ProviderError(REPOSITORY_NOT_FOUND, "Repository or reference not found on GitLab.")
    if resp.status_code == 429:
        raise ProviderError(RATE_LIMITED, "GitLab API rate limit exceeded.")
    if resp.status_code >= 500:
        raise ProviderError(PROVIDER_UNAVAILABLE, "GitLab API returned a server error.")
    raise ProviderError(
        PROVIDER_UNAVAILABLE,
        f"GitLab API returned unexpected status {resp.status_code} for {operation}."
    )
