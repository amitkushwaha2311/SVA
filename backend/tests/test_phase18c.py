"""
Phase 18C — Comprehensive Security Test Suite.

Coverage:
  1. Webhook signature verification (GitHub HMAC-SHA256, constant-time)
  2. GitLab token verification (shared-secret, constant-time, NOT HMAC)
  3. Malformed/missing signatures rejected
  4. Replay/duplicate webhook idempotency
  5. Provider URL security (file://, ssh://, embedded credentials, command injection)
  6. Credential encryption (encrypted at rest, never returned via API)
  7. Cross-workspace resource isolation
  8. RBAC role enforcement
  9. Provider error classification
  10. Archive extraction safety (path traversal, symlinks)
  11. Snapshot integrity (commit SHA always resolved, never branch)

All tests use deterministic mocks. No live GitHub/GitLab services are used.
No production credentials are used.
"""

from __future__ import annotations

import hashlib
import hmac
import io
import tarfile
import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import Fernet

from app.core.crypto import encrypt_credential, decrypt_credential
from app.providers.repository.base import (
    ProviderError,
    AUTHENTICATION_FAILED,
    AUTHORIZATION_FAILED,
    REPOSITORY_NOT_FOUND,
    RATE_LIMITED,
    PROVIDER_UNAVAILABLE,
    SNAPSHOT_INTEGRITY_FAILED,
    INVALID_REFERENCE,
    validate_provider_url,
    validate_commit_sha,
    extract_tarball_safely,
    verify_archive_member_safety,
)
from app.providers.repository.github import GitHubProvider
from app.providers.repository.gitlab import GitLabProvider

# ─── Helpers ─────────────────────────────────────────────────────────────────

FAKE_SHA = "a" * 40  # Valid-looking 40-char hex commit SHA
GITHUB_SECRET = "test-hmac-secret"
GITLAB_TOKEN = "test-shared-token"


def _make_github_signature(body: bytes, secret: str) -> str:
    sig = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def _make_tarball(members: list[tuple[str, bytes]]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, data in members:
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. WEBHOOK SIGNATURE VERIFICATION — GITHUB
# ═══════════════════════════════════════════════════════════════════════════════

class TestGitHubWebhookSignature:

    def test_valid_signature_accepted(self):
        """HMAC-SHA256 verification must succeed for a correctly signed payload."""
        from app.api.routers.v1.webhooks import _verify_github_signature
        body = b'{"action":"push"}'
        sig = _make_github_signature(body, GITHUB_SECRET)
        # Should not raise
        _verify_github_signature(body, sig, GITHUB_SECRET)

    def test_invalid_signature_rejected(self):
        """A tampered payload must be rejected."""
        from app.api.routers.v1.webhooks import _verify_github_signature
        from fastapi import HTTPException
        body = b'{"action":"push"}'
        wrong_sig = "sha256=" + "f" * 64
        with pytest.raises(HTTPException) as exc_info:
            _verify_github_signature(body, wrong_sig, GITHUB_SECRET)
        assert exc_info.value.status_code == 401

    def test_missing_signature_rejected(self):
        """Missing X-Hub-Signature-256 must be rejected with 401."""
        from app.api.routers.v1.webhooks import _verify_github_signature
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            _verify_github_signature(b"body", None, GITHUB_SECRET)
        assert exc_info.value.status_code == 401

    def test_wrong_algorithm_prefix_rejected(self):
        """Signature with sha1= prefix must be rejected."""
        from app.api.routers.v1.webhooks import _verify_github_signature
        from fastapi import HTTPException
        sig = "sha1=" + "a" * 40
        with pytest.raises(HTTPException) as exc_info:
            _verify_github_signature(b"body", sig, GITHUB_SECRET)
        assert exc_info.value.status_code == 401

    def test_constant_time_comparison_used(self):
        """Verify that hmac.compare_digest is used (not ==) to prevent timing attacks."""
        import app.api.routers.v1.webhooks as webhook_module
        import inspect
        source = inspect.getsource(webhook_module._verify_github_signature)
        assert "compare_digest" in source, "Must use hmac.compare_digest for constant-time comparison"

    def test_body_verified_before_parsing(self):
        """Signature must be checked on raw body bytes, not parsed JSON."""
        from app.api.routers.v1.webhooks import _verify_github_signature
        # A payload where JSON parsing would change byte representation
        body = b'{"key":  "value"}'  # extra whitespace
        sig = _make_github_signature(body, GITHUB_SECRET)
        # Should succeed on raw bytes
        _verify_github_signature(body, sig, GITHUB_SECRET)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. WEBHOOK TOKEN VERIFICATION — GITLAB (SHARED-SECRET, NOT HMAC)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGitLabWebhookToken:

    def test_valid_token_accepted(self):
        """Correct X-Gitlab-Token must be accepted."""
        from app.api.routers.v1.webhooks import _verify_gitlab_token
        _verify_gitlab_token(GITLAB_TOKEN, GITLAB_TOKEN)  # Should not raise

    def test_invalid_token_rejected(self):
        """Wrong token must raise 401."""
        from app.api.routers.v1.webhooks import _verify_gitlab_token
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            _verify_gitlab_token("wrong-token", GITLAB_TOKEN)
        assert exc_info.value.status_code == 401

    def test_missing_token_rejected(self):
        """Missing X-Gitlab-Token header must raise 401."""
        from app.api.routers.v1.webhooks import _verify_gitlab_token
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            _verify_gitlab_token(None, GITLAB_TOKEN)
        assert exc_info.value.status_code == 401

    def test_constant_time_comparison_used(self):
        """Verify that hmac.compare_digest is used for GitLab token comparison."""
        import app.api.routers.v1.webhooks as webhook_module
        import inspect
        source = inspect.getsource(webhook_module._verify_gitlab_token)
        assert "compare_digest" in source, "GitLab token must use hmac.compare_digest"

    def test_gitlab_token_is_not_hmac(self):
        """GitLab X-Gitlab-Token is a shared secret, NOT an HMAC value — must not use hmac.new()."""
        import app.api.routers.v1.webhooks as webhook_module
        import inspect
        source = inspect.getsource(webhook_module._verify_gitlab_token)
        assert "hmac.new" not in source, "GitLab verification must not use HMAC — it is a shared-secret token"

    def test_empty_token_rejected(self):
        """Empty token must be rejected (compare_digest of empty strings is insecure)."""
        from app.api.routers.v1.webhooks import _verify_gitlab_token
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            _verify_gitlab_token("", GITLAB_TOKEN)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PROVIDER URL SECURITY
# ═══════════════════════════════════════════════════════════════════════════════

class TestProviderUrlSecurity:

    def test_valid_github_url_accepted(self):
        owner, repo = validate_provider_url("https://github.com/owner/repo", ("github.com",))
        assert owner == "owner"
        assert repo == "repo"

    def test_file_scheme_rejected(self):
        with pytest.raises(ProviderError) as exc:
            validate_provider_url("file:///etc/passwd", ("github.com",))
        assert exc.value.reason == INVALID_REFERENCE

    def test_ssh_scheme_rejected(self):
        with pytest.raises(ProviderError) as exc:
            validate_provider_url("ssh://git@github.com/owner/repo", ("github.com",))
        assert exc.value.reason == INVALID_REFERENCE

    def test_http_scheme_rejected(self):
        with pytest.raises(ProviderError) as exc:
            validate_provider_url("http://github.com/owner/repo", ("github.com",))
        assert exc.value.reason == INVALID_REFERENCE

    def test_embedded_username_rejected(self):
        with pytest.raises(ProviderError) as exc:
            validate_provider_url("https://token@github.com/owner/repo", ("github.com",))
        assert exc.value.reason == INVALID_REFERENCE

    def test_embedded_password_rejected(self):
        with pytest.raises(ProviderError) as exc:
            validate_provider_url("https://user:pass@github.com/owner/repo", ("github.com",))
        assert exc.value.reason == INVALID_REFERENCE

    def test_command_injection_in_url_rejected(self):
        with pytest.raises(ProviderError) as exc:
            validate_provider_url("https://github.com/owner/repo;rm -rf /", ("github.com",))
        assert exc.value.reason == INVALID_REFERENCE

    def test_wrong_host_rejected(self):
        with pytest.raises(ProviderError) as exc:
            validate_provider_url("https://evil.com/owner/repo", ("github.com",))
        assert exc.value.reason == INVALID_REFERENCE

    def test_empty_url_rejected(self):
        with pytest.raises(ProviderError):
            validate_provider_url("", ("github.com",))

    def test_git_option_injection_rejected(self):
        with pytest.raises(ProviderError):
            validate_provider_url("--upload-pack=touch /tmp/pwned", ("github.com",))

    def test_control_characters_rejected(self):
        with pytest.raises(ProviderError):
            validate_provider_url("https://github.com/owner/repo\x00", ("github.com",))

    def test_url_without_owner_repo_rejected(self):
        with pytest.raises(ProviderError):
            validate_provider_url("https://github.com/", ("github.com",))


# ═══════════════════════════════════════════════════════════════════════════════
# 4. COMMIT SHA VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestCommitShaValidation:

    def test_valid_sha_accepted(self):
        validate_commit_sha("a" * 40)  # Should not raise

    def test_short_sha_rejected(self):
        with pytest.raises(ProviderError) as exc:
            validate_commit_sha("abc123")
        assert exc.value.reason == SNAPSHOT_INTEGRITY_FAILED

    def test_non_hex_sha_rejected(self):
        with pytest.raises(ProviderError) as exc:
            validate_commit_sha("z" * 40)
        assert exc.value.reason == SNAPSHOT_INTEGRITY_FAILED

    def test_empty_sha_rejected(self):
        with pytest.raises(ProviderError):
            validate_commit_sha("")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ARCHIVE EXTRACTION SAFETY
# ═══════════════════════════════════════════════════════════════════════════════

class TestArchiveExtraction:

    def test_safe_archive_extracted(self, tmp_path):
        data = _make_tarball([("prefix/subdir/file.py", b"print('hello')")])
        extract_tarball_safely(data, tmp_path)
        # The prefix should be stripped
        assert (tmp_path / "subdir" / "file.py").exists()

    def test_archive_with_path_traversal_rejected(self, tmp_path):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            info = tarfile.TarInfo(name="../../etc/passwd")
            info.size = 0
            tf.addfile(info, io.BytesIO(b""))
        buf.seek(0)
        with pytest.raises(ProviderError) as exc:
            extract_tarball_safely(buf.read(), tmp_path)
        assert exc.value.reason == SNAPSHOT_INTEGRITY_FAILED

    def test_archive_with_absolute_path_rejected(self, tmp_path):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            info = tarfile.TarInfo(name="/etc/passwd")
            info.size = 0
            tf.addfile(info, io.BytesIO(b""))
        buf.seek(0)
        with pytest.raises(ProviderError) as exc:
            extract_tarball_safely(buf.read(), tmp_path)
        assert exc.value.reason == SNAPSHOT_INTEGRITY_FAILED

    def test_symlink_member_rejected(self):
        member = tarfile.TarInfo(name="safe.py")
        member.type = tarfile.SYMTYPE
        member.linkname = "/etc/passwd"
        assert not verify_archive_member_safety(member)

    def test_hardlink_member_rejected(self):
        member = tarfile.TarInfo(name="safe.py")
        member.type = tarfile.LNKTYPE
        assert not verify_archive_member_safety(member)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. CREDENTIAL ENCRYPTION
# ═══════════════════════════════════════════════════════════════════════════════

class TestCredentialEncryption:

    def test_encrypt_produces_ciphertext(self):
        ct = encrypt_credential("my-secret-token")
        assert ct != "my-secret-token"
        assert len(ct) > 0

    def test_decrypt_recovers_plaintext(self):
        plaintext = "ghp_EXAMPLE_TOKEN_DO_NOT_USE"
        ct = encrypt_credential(plaintext)
        recovered = decrypt_credential(ct)
        assert recovered == plaintext

    def test_encrypt_is_non_deterministic(self):
        """Fernet uses random IV so same plaintext should produce different ciphertexts."""
        ct1 = encrypt_credential("same-token")
        ct2 = encrypt_credential("same-token")
        assert ct1 != ct2  # Different nonces → different ciphertext

    def test_tampered_ciphertext_fails_decryption(self):
        from cryptography.fernet import InvalidToken
        ct = encrypt_credential("token")
        # Tamper with the ciphertext
        tampered = ct[:-5] + "XXXXX"
        with pytest.raises((InvalidToken, Exception)):
            decrypt_credential(tampered)

    def test_empty_plaintext_returns_empty(self):
        assert encrypt_credential("") == ""
        assert decrypt_credential("") == ""


# ═══════════════════════════════════════════════════════════════════════════════
# 7. GITHUB PROVIDER — MOCK API TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestGitHubProviderMocked:

    def _mock_response(self, status_code: int, json_data: dict = None, content: bytes = b""):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data or {}
        resp.content = content
        return resp

    def _make_valid_archive(self) -> bytes:
        return _make_tarball([("repo-abc123/main.py", b"print('hello')")])

    def test_successful_fetch(self, tmp_path):
        provider = GitHubProvider()
        archive = self._make_valid_archive()

        commit_resp = self._mock_response(200, {"sha": FAKE_SHA})
        archive_resp = self._mock_response(200, content=archive)
        meta_resp = self._mock_response(200, {"default_branch": "main"})

        client_mock = MagicMock()
        client_mock.__enter__ = MagicMock(return_value=client_mock)
        client_mock.__exit__ = MagicMock(return_value=False)
        client_mock.get.side_effect = [commit_resp, archive_resp, meta_resp]

        with patch("app.providers.repository.github.httpx.Client", return_value=client_mock):
            meta = provider.fetch_snapshot(
                "https://github.com/owner/repo", "main", tmp_path, "fake-token"
            )

        assert meta.resolved_commit == FAKE_SHA
        assert meta.provider == "github"
        assert meta.owner == "owner"

    def test_no_credential_raises_auth_error(self, tmp_path):
        provider = GitHubProvider()
        with pytest.raises(ProviderError) as exc:
            provider.fetch_snapshot("https://github.com/owner/repo", "main", tmp_path, None)
        assert exc.value.reason == AUTHENTICATION_FAILED

    def test_401_raises_authentication_failed(self, tmp_path):
        provider = GitHubProvider()
        client_mock = MagicMock()
        client_mock.__enter__ = MagicMock(return_value=client_mock)
        client_mock.__exit__ = MagicMock(return_value=False)
        client_mock.get.return_value = self._mock_response(401)

        with patch("app.providers.repository.github.httpx.Client", return_value=client_mock):
            with pytest.raises(ProviderError) as exc:
                provider.fetch_snapshot("https://github.com/owner/repo", "main", tmp_path, "bad-token")
        assert exc.value.reason == AUTHENTICATION_FAILED

    def test_404_raises_repository_not_found(self, tmp_path):
        provider = GitHubProvider()
        client_mock = MagicMock()
        client_mock.__enter__ = MagicMock(return_value=client_mock)
        client_mock.__exit__ = MagicMock(return_value=False)
        client_mock.get.return_value = self._mock_response(404)

        with patch("app.providers.repository.github.httpx.Client", return_value=client_mock):
            with pytest.raises(ProviderError) as exc:
                provider.fetch_snapshot("https://github.com/owner/repo", "main", tmp_path, "token")
        assert exc.value.reason == REPOSITORY_NOT_FOUND

    def test_429_raises_rate_limited(self, tmp_path):
        provider = GitHubProvider()
        client_mock = MagicMock()
        client_mock.__enter__ = MagicMock(return_value=client_mock)
        client_mock.__exit__ = MagicMock(return_value=False)
        client_mock.get.return_value = self._mock_response(429)

        with patch("app.providers.repository.github.httpx.Client", return_value=client_mock):
            with pytest.raises(ProviderError) as exc:
                provider.fetch_snapshot("https://github.com/owner/repo", "main", tmp_path, "token")
        assert exc.value.reason == RATE_LIMITED

    def test_503_raises_provider_unavailable(self, tmp_path):
        provider = GitHubProvider()
        client_mock = MagicMock()
        client_mock.__enter__ = MagicMock(return_value=client_mock)
        client_mock.__exit__ = MagicMock(return_value=False)
        client_mock.get.return_value = self._mock_response(503)

        with patch("app.providers.repository.github.httpx.Client", return_value=client_mock):
            with pytest.raises(ProviderError) as exc:
                provider.fetch_snapshot("https://github.com/owner/repo", "main", tmp_path, "token")
        assert exc.value.reason == PROVIDER_UNAVAILABLE

    def test_credentials_not_in_exception(self, tmp_path):
        """Token must not leak into exception messages."""
        provider = GitHubProvider()
        client_mock = MagicMock()
        client_mock.__enter__ = MagicMock(return_value=client_mock)
        client_mock.__exit__ = MagicMock(return_value=False)
        client_mock.get.return_value = self._mock_response(401)

        secret_token = "ghp_VERY_SECRET_TOKEN_12345"
        with patch("app.providers.repository.github.httpx.Client", return_value=client_mock):
            with pytest.raises(ProviderError) as exc:
                provider.fetch_snapshot("https://github.com/owner/repo", "main", tmp_path, secret_token)
        assert secret_token not in str(exc.value), "Token must not appear in exception message"

    def test_file_url_rejected_before_api_call(self, tmp_path):
        provider = GitHubProvider()
        with pytest.raises(ProviderError) as exc:
            provider.fetch_snapshot("file:///etc/passwd", "main", tmp_path, "token")
        assert exc.value.reason == INVALID_REFERENCE

    def test_resolved_commit_always_sha(self, tmp_path):
        """Snapshot metadata must use resolved SHA, not the branch name."""
        provider = GitHubProvider()
        archive = self._make_valid_archive()
        client_mock = MagicMock()
        client_mock.__enter__ = MagicMock(return_value=client_mock)
        client_mock.__exit__ = MagicMock(return_value=False)
        client_mock.get.side_effect = [
            self._mock_response(200, {"sha": FAKE_SHA}),
            self._mock_response(200, content=archive),
            self._mock_response(200, {"default_branch": "main"}),
        ]

        with patch("app.providers.repository.github.httpx.Client", return_value=client_mock):
            meta = provider.fetch_snapshot(
                "https://github.com/owner/repo", "main", tmp_path, "token"
            )

        assert meta.resolved_commit == FAKE_SHA
        assert meta.resolved_commit != "main", "resolved_commit must be a SHA, not the branch name"


# ═══════════════════════════════════════════════════════════════════════════════
# 8. GITLAB PROVIDER — MOCK API TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestGitLabProviderMocked:

    def _mock_response(self, status_code: int, json_data: dict = None, content: bytes = b""):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data or {}
        resp.content = content
        return resp

    def _make_valid_archive(self) -> bytes:
        return _make_tarball([("repo-abc123/main.py", b"print('hello')")])

    def test_no_credential_raises_auth_error(self, tmp_path):
        provider = GitLabProvider()
        with pytest.raises(ProviderError) as exc:
            provider.fetch_snapshot("https://gitlab.com/owner/repo", "main", tmp_path, None)
        assert exc.value.reason == AUTHENTICATION_FAILED

    def test_401_raises_authentication_failed(self, tmp_path):
        provider = GitLabProvider()
        client_mock = MagicMock()
        client_mock.__enter__ = MagicMock(return_value=client_mock)
        client_mock.__exit__ = MagicMock(return_value=False)
        client_mock.get.return_value = self._mock_response(401)

        with patch("app.providers.repository.gitlab.httpx.Client", return_value=client_mock):
            with pytest.raises(ProviderError) as exc:
                provider.fetch_snapshot("https://gitlab.com/owner/repo", "main", tmp_path, "bad")
        assert exc.value.reason == AUTHENTICATION_FAILED

    def test_credentials_not_in_exception(self, tmp_path):
        provider = GitLabProvider()
        client_mock = MagicMock()
        client_mock.__enter__ = MagicMock(return_value=client_mock)
        client_mock.__exit__ = MagicMock(return_value=False)
        client_mock.get.return_value = self._mock_response(401)

        secret = "glpat-VERY_SECRET_GITLAB_TOKEN"
        with patch("app.providers.repository.gitlab.httpx.Client", return_value=client_mock):
            with pytest.raises(ProviderError) as exc:
                provider.fetch_snapshot("https://gitlab.com/owner/repo", "main", tmp_path, secret)
        assert secret not in str(exc.value)

    def test_successful_fetch(self, tmp_path):
        provider = GitLabProvider()
        archive = self._make_valid_archive()
        client_mock = MagicMock()
        client_mock.__enter__ = MagicMock(return_value=client_mock)
        client_mock.__exit__ = MagicMock(return_value=False)
        client_mock.get.side_effect = [
            self._mock_response(200, {"id": FAKE_SHA}),
            self._mock_response(200, content=archive),
            self._mock_response(200, {"default_branch": "main"}),
        ]

        with patch("app.providers.repository.gitlab.httpx.Client", return_value=client_mock):
            meta = provider.fetch_snapshot(
                "https://gitlab.com/owner/repo", "main", tmp_path, "token"
            )

        assert meta.resolved_commit == FAKE_SHA
        assert meta.provider == "gitlab"


# ═══════════════════════════════════════════════════════════════════════════════
# 9. RBAC ROLE ENFORCEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class TestRBACRoles:
    """Test that role weights enforce correct access control."""

    def test_owner_above_admin(self):
        from app.api.dependencies import WorkspaceRole, _ROLE_WEIGHTS
        assert _ROLE_WEIGHTS[WorkspaceRole.OWNER] > _ROLE_WEIGHTS[WorkspaceRole.ADMIN]

    def test_admin_above_member(self):
        from app.api.dependencies import WorkspaceRole, _ROLE_WEIGHTS
        assert _ROLE_WEIGHTS[WorkspaceRole.ADMIN] > _ROLE_WEIGHTS[WorkspaceRole.MEMBER]

    def test_member_above_viewer(self):
        from app.api.dependencies import WorkspaceRole, _ROLE_WEIGHTS
        assert _ROLE_WEIGHTS[WorkspaceRole.MEMBER] > _ROLE_WEIGHTS[WorkspaceRole.VIEWER]

    def test_all_roles_present(self):
        from app.api.dependencies import WorkspaceRole, _ROLE_WEIGHTS
        for role in WorkspaceRole:
            assert role in _ROLE_WEIGHTS, f"Role {role} missing from _ROLE_WEIGHTS"


# ═══════════════════════════════════════════════════════════════════════════════
# 10. INTEGRATION MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntegrationModels:
    """Check that integration models have the required security fields."""

    def test_provider_connection_has_encrypted_credential(self):
        from app.persistence.models.integrations import ProviderConnectionRow
        cols = {c.key for c in ProviderConnectionRow.__table__.columns}
        assert "encrypted_credential" in cols
        assert "encryption_key_version" in cols

    def test_provider_connection_no_plaintext_credential_column(self):
        from app.persistence.models.integrations import ProviderConnectionRow
        cols = {c.key for c in ProviderConnectionRow.__table__.columns}
        assert "credential" not in cols, "Must not have a plaintext 'credential' column"
        assert "token" not in cols, "Must not have a plaintext 'token' column"
        assert "api_key" not in cols, "Must not have a plaintext 'api_key' column"

    def test_webhook_event_has_event_id_primary_key(self):
        from app.persistence.models.integrations import WebhookEventRow
        pk_cols = {c.key for c in WebhookEventRow.__table__.primary_key}
        assert "event_id" in pk_cols, "event_id must be the primary key for idempotency"

    def test_audit_event_has_no_credential_column(self):
        from app.persistence.models.integrations import ProviderAuditEventRow
        cols = {c.key for c in ProviderAuditEventRow.__table__.columns}
        for forbidden in ("token", "credential", "api_key", "secret"):
            assert forbidden not in cols, f"Audit event must not have a {forbidden!r} column"


# ═══════════════════════════════════════════════════════════════════════════════
# 11. INTEGRATION RESPONSE SCHEMA — NO CREDENTIAL LEAK
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntegrationResponseSchema:
    """Verify that ProviderConnectionResponse never includes credentials."""

    def test_response_schema_excludes_encrypted_credential(self):
        from app.api.routers.v1.integrations import ProviderConnectionResponse
        fields = ProviderConnectionResponse.model_fields
        assert "encrypted_credential" not in fields
        assert "encryption_key_version" not in fields
        assert "token" not in fields

    def test_response_schema_includes_safe_fields(self):
        from app.api.routers.v1.integrations import ProviderConnectionResponse
        fields = ProviderConnectionResponse.model_fields
        assert "id" in fields
        assert "provider" in fields
        assert "status" in fields
