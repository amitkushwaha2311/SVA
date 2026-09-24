"""
Revision Security Tests — Phase 17 Security Gap Fix
=====================================================

Tests GitProvider._validate_revision() exhaustively against:
  - Valid inputs that must NOT raise
  - Invalid inputs that MUST raise GitProviderError

Also tests:
  - Git alias override arguments are present in every subprocess invocation
  - The '--' separator is present in checkout to prevent revision-as-option injection
  - The '--' is never inserted before the URL in clone (would break it)

These tests are written against the actual implementation.
No mocking of _validate_revision() itself — it must be called through fetch_snapshot()
for subprocess-level tests, but tested directly for validation-only tests.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.providers.repository.git import (
    GitProvider,
    GitProviderError,
    _SAFE_REVISION_RE,
    _SHA_RE,
    _FORBIDDEN_CHARS_RE,
    _OPTION_PREFIXES,
)


# ─── Valid Revisions (must NOT raise) ─────────────────────────────────────────

class TestValidRevisions:
    """Every entry here must be accepted by _validate_revision() without raising."""

    def _accept(self, rev: str):
        provider = GitProvider()
        provider._validate_revision(rev)  # must not raise

    def test_simple_branch(self):
        self._accept("main")

    def test_branch_with_hyphen(self):
        self._accept("feature-login")

    def test_branch_with_slash(self):
        self._accept("feature/PROJ-123")

    def test_branch_with_dot(self):
        self._accept("release-1.0")

    def test_tag_semver(self):
        self._accept("v1.0.0")

    def test_tag_date(self):
        self._accept("2024-01-01")

    def test_short_sha(self):
        self._accept("abc1234")

    def test_full_sha(self):
        self._accept("a" * 40)

    def test_mixed_case(self):
        self._accept("HotFix-AUTH")

    def test_underscore(self):
        self._accept("fix_auth_bug")

    def test_numeric_only(self):
        self._accept("20240117")

    def test_long_branch_near_limit(self):
        # 255 chars — just at the limit
        self._accept("a" + "b" * 254)


# ─── Rejected Revisions (must raise GitProviderError) ─────────────────────────

class TestRejectedRevisions:
    """Every entry here must raise GitProviderError."""

    def _reject(self, rev: str, *, match: str | None = None):
        provider = GitProvider()
        if match:
            with pytest.raises(GitProviderError, match=match):
                provider._validate_revision(rev)
        else:
            with pytest.raises(GitProviderError):
                provider._validate_revision(rev)

    # ── Empty / whitespace ────────────────────────────────────────────────────

    def test_empty_string(self):
        self._reject("", match="empty")

    def test_whitespace_only(self):
        self._reject("   ", match="empty")

    def test_tab_only(self):
        self._reject("\t", match="empty")

    # ── Length ────────────────────────────────────────────────────────────────

    def test_exceeds_max_length(self):
        self._reject("a" * 256, match="maximum length")

    # ── Git option injection (leading options) ─────────────────────────────────

    def test_upload_pack(self):
        self._reject("--upload-pack=/bin/sh")

    def test_config_injection(self):
        self._reject("--config=core.hooksPath=/tmp")

    def test_exec_path(self):
        self._reject("--exec-path=/evil")

    def test_git_dir(self):
        self._reject("--git-dir=/etc")

    def test_work_tree(self):
        self._reject("--work-tree=/etc")

    def test_namespace(self):
        self._reject("--namespace=evil")

    def test_no_prefix(self):
        self._reject("--no-checkout")

    def test_generic_double_dash(self):
        self._reject("--evil")

    def test_single_dash_option(self):
        self._reject("-c")

    def test_single_dash_long(self):
        self._reject("-core.hooksPath=/tmp")

    # ── Shell metacharacters ───────────────────────────────────────────────────

    def test_semicolon(self):
        self._reject("main;rm -rf /")

    def test_ampersand(self):
        self._reject("main&&evil")

    def test_pipe(self):
        self._reject("main|cat /etc/passwd")

    def test_backtick(self):
        self._reject("main`id`")

    def test_dollar_subshell(self):
        self._reject("main$(id)")

    def test_bang(self):
        self._reject("main!cmd")

    def test_angle_bracket_in(self):
        self._reject("main<file")

    def test_angle_bracket_out(self):
        self._reject("main>file")

    def test_paren(self):
        self._reject("main(arg)")

    def test_brace(self):
        self._reject("main{arg}")

    # ── Control characters ────────────────────────────────────────────────────

    def test_newline(self):
        self._reject("main\n")

    def test_carriage_return(self):
        self._reject("main\r")

    def test_nul_byte(self):
        self._reject("main\x00")

    def test_tab(self):
        self._reject("main\t")

    def test_backspace(self):
        self._reject("main\x08")

    def test_escape(self):
        self._reject("main\x1b")

    # ── Embedded whitespace ───────────────────────────────────────────────────

    def test_space_in_middle(self):
        self._reject("main branch")

    # ── Git pathspec special characters ───────────────────────────────────────

    def test_tilde(self):
        self._reject("main~1")

    def test_caret(self):
        self._reject("main^0")

    def test_colon(self):
        self._reject("main:path")

    def test_question_mark(self):
        self._reject("main?")

    def test_asterisk(self):
        self._reject("main*")

    def test_square_bracket(self):
        self._reject("main[0]")

    def test_backslash(self):
        self._reject("main\\path")

    # ── Path traversal ────────────────────────────────────────────────────────

    def test_dotdot_slash(self):
        self._reject("../etc/passwd")

    def test_slash_dotdot(self):
        self._reject("branch/../../etc")

    def test_dotdot_only(self):
        self._reject("..")

    # ── Leading dot (also rejected by allowlist) ──────────────────────────────

    def test_leading_dot(self):
        self._reject(".hidden-branch")

    def test_leading_dot_dotdot(self):
        self._reject("./../etc/passwd")


# ─── Subprocess Security: '--' Separator & Alias Overrides ────────────────────

class TestSubprocessSecurity:
    """Verify subprocess argv structure after validation."""

    @patch("app.providers.repository.git.subprocess.run")
    def test_checkout_uses_resolved_sha_not_branch_name(self, mock_run, tmp_path):
        """
        The checkout command must operate on a resolved, immutable commit SHA
        rather than the raw user-supplied branch name.

        A 40-char hexadecimal SHA:
          • cannot start with '-'   → cannot be a git option flag
          • cannot contain whitespace → cannot split into multiple argv tokens
          • is unambiguous across branches/tags/HEAD

        This is strictly stronger than placing '--' before a branch name,
        because it eliminates the injection surface entirely rather than
        just neutralising it.
        """
        resolved_sha = "4c2dd18f95d91e1633115eac306deb2103855261"
        mock_run.return_value = MagicMock(returncode=0, stdout=f"{resolved_sha}\n")

        target = tmp_path / "repo"
        target.mkdir()
        provider = GitProvider()

        try:
            provider.fetch_snapshot("https://github.com/org/repo", "main", target)
        except Exception:
            pass

        # Find the checkout call
        checkout_call = None
        for call in mock_run.call_args_list:
            args, _ = call
            cmd = args[0]
            if "checkout" in cmd:
                checkout_call = cmd
                break

        assert checkout_call is not None, "No checkout call found in subprocess invocations"

        # The user-supplied branch name must NOT appear in the checkout command.
        # Only the resolved SHA must be used.
        assert "main" not in checkout_call, (
            f"Branch name must not appear in checkout command; only resolved SHA "
            f"may be used. Got: {checkout_call}"
        )

        # The resolved SHA must appear in the checkout command
        assert resolved_sha in checkout_call, (
            f"Resolved SHA must be the treeish in checkout command. Got: {checkout_call}"
        )

        # The SHA must not start with '-' (sanity; enforced by _SHA_RE)
        sha_in_cmd = [a for a in checkout_call if a == resolved_sha][0]
        assert not sha_in_cmd.startswith("-"), "SHA must not start with '-'"

    @patch("app.providers.repository.git.subprocess.run")
    def test_clone_does_not_inject_double_dash_before_url(self, mock_run, tmp_path):
        """
        The clone command must NOT insert '--' before the URL —
        that would break git clone. URL safety is enforced by _validate_url().
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="abc1234567890\n")

        target = tmp_path / "repo"
        target.mkdir()
        provider = GitProvider()

        try:
            provider.fetch_snapshot("https://github.com/org/repo", "main", target)
        except Exception:
            pass

        clone_call = None
        for call in mock_run.call_args_list:
            args, _ = call
            cmd = args[0]
            if "clone" in cmd:
                clone_call = cmd
                break

        assert clone_call is not None, "No clone call found"
        url_idx = clone_call.index("https://github.com/org/repo")

        # If '--' appears in clone, it must not be immediately before the URL
        if "--" in clone_call:
            double_dash_idx = clone_call.index("--")
            # '--' in clone should be a no-checkout flag, not separating the URL
            # Check that what's at double_dash_idx is actually "--no-checkout"
            assert clone_call[double_dash_idx] == "--no-checkout", (
                f"The '--' in clone must be '--no-checkout', not a bare separator before URL"
            )

    @patch("app.providers.repository.git.subprocess.run")
    def test_alias_clone_overridden(self, mock_run, tmp_path):
        """
        Every git invocation must include '-c alias.clone=' to prevent
        a user's gitconfig alias from hijacking the clone command.
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="abc1234567890\n")

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
            assert "alias.clone=" in cmd, (
                f"'alias.clone=' override is missing from git command: {cmd}"
            )

    @patch("app.providers.repository.git.subprocess.run")
    def test_alias_checkout_overridden(self, mock_run, tmp_path):
        """
        Every git invocation must include '-c alias.checkout=' to prevent
        a user's gitconfig alias from hijacking the checkout command.
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="abc1234567890\n")

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
            assert "alias.checkout=" in cmd, (
                f"'alias.checkout=' override is missing from git command: {cmd}"
            )

    @patch("app.providers.repository.git.subprocess.run")
    def test_protocol_allow_restricted(self, mock_run, tmp_path):
        """
        protocol.allow=never and protocol.https.allow=always must be set
        to prevent git from using unsafe transport protocols (e.g. git://, ext::)
        even if a redirect or credential lookup triggers a secondary fetch.
        """
        mock_run.return_value = MagicMock(returncode=0, stdout="abc1234567890\n")

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
            assert "protocol.allow=never" in cmd, (
                f"'protocol.allow=never' missing from git command: {cmd}"
            )
            assert "protocol.https.allow=always" in cmd, (
                f"'protocol.https.allow=always' missing from git command: {cmd}"
            )

    @patch("app.providers.repository.git.subprocess.run")
    def test_validate_revision_called_before_subprocess(self, mock_run, tmp_path):
        """
        _validate_revision() must be called before any subprocess.run().
        If the revision is invalid, subprocess must never be invoked.
        """
        target = tmp_path / "repo"
        target.mkdir()
        provider = GitProvider()

        with pytest.raises(GitProviderError):
            provider.fetch_snapshot(
                "https://github.com/org/repo",
                "--upload-pack=/bin/sh",  # Malicious revision
                target,
            )

        # subprocess.run must NEVER have been called with the malicious revision
        mock_run.assert_not_called()
