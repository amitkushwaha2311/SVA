"""
Provider Security Tests — Phase 17 Final Audit
================================================

Tests are written against the ACTUAL implementation signatures:
  GitProvider.fetch_snapshot(identifier, revision, target_dir) -> RepositoryMetadata
  GitProvider._validate_url(url) -> None
  LocalProvider.fetch_snapshot(identifier, revision, target_dir) -> RepositoryMetadata
  LocalProvider._safe_copy(source_root, target_root) -> None

All tests are hermetic — no real network or filesystem access.
"""

import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.providers.repository.git import GitProvider, GitProviderError
from app.providers.repository.local import LocalProvider, LocalProviderError


# ─── GitProvider URL Validation ───────────────────────────────────────────────

class TestGitProviderURLValidation:
    """GitProvider._validate_url must reject every disallowed scheme and pattern."""

    def _validate(self, url: str):
        p = GitProvider()
        p._validate_url(url)

    def test_rejects_http(self):
        with pytest.raises(GitProviderError, match="Only HTTPS is permitted"):
            self._validate("http://github.com/org/repo")

    def test_rejects_ssh(self):
        with pytest.raises(GitProviderError, match="Only HTTPS is permitted"):
            self._validate("ssh://git@github.com/org/repo")

    def test_rejects_file(self):
        with pytest.raises(GitProviderError, match="Only HTTPS is permitted"):
            self._validate("file:///etc/passwd")

    def test_rejects_git_protocol(self):
        with pytest.raises(GitProviderError, match="Only HTTPS is permitted"):
            self._validate("git://github.com/org/repo")

    def test_rejects_ftp(self):
        with pytest.raises(GitProviderError, match="Only HTTPS is permitted"):
            self._validate("ftp://example.com/repo")

    def test_rejects_embedded_username(self):
        with pytest.raises(GitProviderError, match="Embedded credentials"):
            self._validate("https://user@github.com/org/repo")

    def test_rejects_embedded_username_and_password(self):
        with pytest.raises(GitProviderError, match="Embedded credentials"):
            self._validate("https://user:secret@github.com/org/repo")

    def test_rejects_url_starting_with_dashes(self):
        """Prevent argument injection via URL that starts with --.
        The URL scheme check fires first, but either way it is rejected."""
        with pytest.raises(GitProviderError):
            self._validate("--upload-pack=/bin/sh")

    def test_accepts_valid_https(self):
        """Valid HTTPS URLs must NOT raise."""
        self._validate("https://github.com/org/repo")
        self._validate("https://gitlab.com/org/repo.git")


# ─── GitProvider Subprocess Security ──────────────────────────────────────────

class TestGitProviderSubprocessSecurity:
    """Verify the git subprocess is invoked with security-hardened arguments."""

    @patch("app.providers.repository.git.subprocess.run")
    def test_clone_uses_strict_arg_array_not_shell(self, mock_run, tmp_path):
        """git clone must never use shell=True."""
        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n")

        target = tmp_path / "repo"
        target.mkdir()
        provider = GitProvider()

        try:
            provider.fetch_snapshot("https://github.com/org/repo", "main", target)
        except Exception:
            pass  # We only care about how subprocess was called

        for call in mock_run.call_args_list:
            args, kwargs = call
            assert kwargs.get("shell") is False, "shell=True must never be used"
            cmd = args[0]
            assert isinstance(cmd, list), "Command must be a list, not a string"

    @patch("app.providers.repository.git.subprocess.run")
    def test_clone_disables_hooks(self, mock_run, tmp_path):
        """core.hooksPath must be nullified in every git invocation."""
        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n")

        target = tmp_path / "repo"
        target.mkdir()
        provider = GitProvider()

        try:
            provider.fetch_snapshot("https://github.com/org/repo", "main", target)
        except Exception:
            pass

        for call in mock_run.call_args_list:
            args, _ = call
            cmd = args[0]
            assert "core.hooksPath=/dev/null" in cmd, (
                f"core.hooksPath=/dev/null missing from git command: {cmd}"
            )

    @patch("app.providers.repository.git.subprocess.run")
    def test_clone_disables_credential_helper(self, mock_run, tmp_path):
        """credential.helper must be blanked to prevent credential leakage."""
        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n")

        target = tmp_path / "repo"
        target.mkdir()
        provider = GitProvider()

        try:
            provider.fetch_snapshot("https://github.com/org/repo", "main", target)
        except Exception:
            pass

        for call in mock_run.call_args_list:
            args, _ = call
            cmd = args[0]
            assert "credential.helper=" in cmd, (
                f"credential.helper= blank missing from git command: {cmd}"
            )

    @patch("app.providers.repository.git.subprocess.run")
    def test_clone_disables_terminal_prompt(self, mock_run, tmp_path):
        """GIT_TERMINAL_PROMPT=0 prevents hanging on credential prompts."""
        mock_run.return_value = MagicMock(returncode=0, stdout="abc123\n")

        target = tmp_path / "repo"
        target.mkdir()
        provider = GitProvider()

        try:
            provider.fetch_snapshot("https://github.com/org/repo", "main", target)
        except Exception:
            pass

        for call in mock_run.call_args_list:
            _, kwargs = call
            env = kwargs.get("env", {})
            assert env.get("GIT_TERMINAL_PROMPT") == "0", (
                "GIT_TERMINAL_PROMPT=0 must be in git subprocess environment"
            )

    @patch("app.providers.repository.git.subprocess.run")
    def test_stderr_not_propagated_on_failure(self, mock_run, tmp_path):
        """
        On clone failure, the error raised must NOT include the raw git stderr
        which may contain URLs with credentials or other secrets.
        """
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=128,
            cmd=["git", "clone"],
            stderr="fatal: Authentication failed for 'https://user:SECRET@github.com/org/repo'"
        )

        target = tmp_path / "repo"
        target.mkdir()
        provider = GitProvider()

        with pytest.raises(GitProviderError) as exc_info:
            provider.fetch_snapshot("https://github.com/org/repo", "main", target)

        # The raw stderr containing credentials must NOT appear in the error message
        error_str = str(exc_info.value)
        assert "SECRET" not in error_str, "Git stderr (which may contain secrets) must not be re-raised verbatim"
        assert "Authentication failed" not in error_str, "Raw git stderr must not be exposed"


# ─── LocalProvider Filesystem Security ────────────────────────────────────────

class TestLocalProviderFilesystemSecurity:
    """LocalProvider must never copy symlinks or non-regular files."""

    def test_copies_regular_files(self, tmp_path):
        """Regular files must be copied correctly."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "safe.py").write_text("def hello(): pass")
        (source / "sub").mkdir()
        (source / "sub" / "nested.py").write_text("x = 1")

        target = tmp_path / "target"
        target.mkdir()

        provider = LocalProvider()
        provider._safe_copy(source, target)

        assert (target / "safe.py").read_text() == "def hello(): pass"
        assert (target / "sub" / "nested.py").read_text() == "x = 1"

    @pytest.mark.skipif(
        __import__('platform').system() == "Windows",
        reason="Symlink tests require Developer Mode on Windows"
    )
    def test_skips_internal_symlinks(self, tmp_path):
        """Symlinks within the source tree must be silently skipped."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "real.py").write_text("content")
        (source / "link.py").symlink_to("real.py")

        target = tmp_path / "target"
        target.mkdir()

        provider = LocalProvider()
        provider._safe_copy(source, target)

        assert (target / "real.py").exists()
        assert not (target / "link.py").exists(), "Symlinks must not be copied"

    @pytest.mark.skipif(
        __import__('platform').system() == "Windows",
        reason="Symlink tests require Developer Mode on Windows"
    )
    def test_skips_external_symlinks(self, tmp_path):
        """External symlinks (pointing outside source tree) must be skipped, not followed."""
        secret = tmp_path / "etc_passwd"
        secret.write_text("root:x:0:0:root:/root:/bin/bash")

        source = tmp_path / "source"
        source.mkdir()
        (source / "safe.py").write_text("content")
        (source / "dangerous_link").symlink_to(str(secret))

        target = tmp_path / "target"
        target.mkdir()

        provider = LocalProvider()
        provider._safe_copy(source, target)

        assert (target / "safe.py").exists()
        assert not (target / "dangerous_link").exists(), "External symlinks must not be copied"
        # Crucially: the target must NOT contain the contents of 'secret'
        for f in target.rglob("*"):
            if f.is_file():
                assert f.read_text() != "root:x:0:0:root:/root:/bin/bash", (
                    "Secret file contents must not appear in snapshot"
                )

    def test_fingerprint_is_deterministic(self, tmp_path):
        """The content hash must be reproducible for the same files."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "a.py").write_text("hello")
        (source / "b.py").write_text("world")

        provider = LocalProvider()
        h1 = provider._hash_directory(source)
        h2 = provider._hash_directory(source)
        assert h1 == h2

    def test_fingerprint_changes_with_content(self, tmp_path):
        """Content change must change the hash."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "a.py").write_text("original")

        provider = LocalProvider()
        h1 = provider._hash_directory(source)
        (source / "a.py").write_text("modified")
        h2 = provider._hash_directory(source)
        assert h1 != h2

    def test_provider_rejects_nonexistent_path(self, tmp_path):
        """fetch_snapshot must fail if source directory does not exist."""
        target = tmp_path / "target"
        target.mkdir()

        provider = LocalProvider()
        with pytest.raises(LocalProviderError, match="not found"):
            provider.fetch_snapshot("/nonexistent/path/to/nowhere", "main", target)

    def test_provider_rejects_file_not_directory(self, tmp_path):
        """fetch_snapshot must fail if source is a file, not a directory."""
        source_file = tmp_path / "a_file.py"
        source_file.write_text("content")
        target = tmp_path / "target"
        target.mkdir()

        provider = LocalProvider()
        with pytest.raises(LocalProviderError, match="not found"):
            provider.fetch_snapshot(str(source_file), "main", target)
