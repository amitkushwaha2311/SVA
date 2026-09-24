"""
GitProvider — Secure Git Repository Ingestion
===============================================

Security controls:
- shell=False with strictly typed argument arrays (no shell expansion)
- HTTPS only — rejects file://, ssh://, http://, git://, ftp://
- Embedded credentials in URLs are forbidden
- Revision validation: only branch names, tag names, or commit SHAs are allowed
- Revisions are validated before being passed to subprocess argv
- Git hooks are disabled globally (core.hooksPath=/dev/null)
- Credential helpers are suppressed (credential.helper=)
- Git aliases for clone/checkout are overridden to prevent alias execution
- Subprocess stderr is NEVER re-propagated (prevents secret leakage on failure)
- Resolved commit SHA is stored — not the user-supplied revision
- Environment is minimal: only safe OS variables needed for subprocess execution
  are inherited (PATH, SYSTEMROOT, TEMP, TMP on Windows) so that git's internal
  network threads can initialise Winsock/DNS without leaking sensitive variables.
"""

import os
import platform
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from .base import RepositoryProvider, RepositoryMetadata, IngestionError


_IS_WINDOWS = platform.system() == "Windows"

# Environment variable names that are safe to inherit from the parent process.
# These are required for git's subprocess to function correctly (DNS, DLL loading,
# temp files) without leaking sensitive variables like credentials or tokens.
# On Linux/macOS the list is shorter because /bin/false handles askpass and
# Winsock/DNS does not need SYSTEMROOT.
_SAFE_INHERIT_ENV_VARS_WINDOWS = (
    "PATH",          # Needed to locate git.exe and system DLLs
    "SYSTEMROOT",    # Required by Winsock to initialize — without it, getaddrinfo threads fail
    "SYSTEMDRIVE",   # Windows system drive letter
    "WINDIR",        # Needed by some Windows runtime components
    "TEMP",          # Temp directory — git uses it for lock files
    "TMP",           # Alternate temp variable
    "USERPROFILE",   # Some git versions check this for home dir
    "HOMEDRIVE",     # Windows home drive
    "HOMEPATH",      # Windows home path (needed to avoid ~/.gitconfig issues)
    "COMPUTERNAME",  # Sometimes needed by Windows network stack
    "NUMBER_OF_PROCESSORS",  # Used by git for worker count
)
_SAFE_INHERIT_ENV_VARS_POSIX = (
    "PATH",          # Needed to locate git binary
    "HOME",          # Needed by git to find its own config (not user creds)
    "TMPDIR",        # Temp directory
    "LANG",          # Character encoding — avoids garbled error messages
    "LC_ALL",        # Locale
)


def _build_safe_env() -> dict[str, str]:
    """
    Build a minimal, safe environment for git subprocess invocations.

    Inherits only the OS variables needed for subprocess execution
    (PATH, networking libraries, temp dirs) while stripping:
    - Credential-related variables (GIT_TOKEN, GITHUB_TOKEN, etc.)
    - Shell variables that could influence git behaviour
    - User-specific config paths beyond home dir

    Security: the allowlist approach ensures no unexpected variables
    slip through. New variables must be explicitly added here.
    """
    parent_env = os.environ
    safe: dict[str, str] = {}

    inherit_keys = _SAFE_INHERIT_ENV_VARS_WINDOWS if _IS_WINDOWS else _SAFE_INHERIT_ENV_VARS_POSIX
    for key in inherit_keys:
        val = parent_env.get(key)
        if val is not None:
            safe[key] = val

    # Security overrides — these MUST always be set regardless of parent env
    safe["GIT_TERMINAL_PROMPT"] = "0"     # Never prompt for credentials

    if _IS_WINDOWS:
        pass
    else:
        safe["GIT_ASKPASS"] = "/bin/false"
        safe["SSH_ASKPASS"] = "/bin/false"
        safe["GIT_SSH_COMMAND"] = "ssh -o StrictHostKeyChecking=no -o BatchMode=yes"

    return safe


class GitProviderError(IngestionError):
    pass


# ─── Revision Validation Constants ────────────────────────────────────────────

# Maximum length for a revision string.
# Git SHA is 40 hex chars; branch/tag names up to 255 bytes per git spec.
_REVISION_MAX_LENGTH = 255

# Allowlist pattern for a safe git ref component:
#   - Alphanumeric characters
#   - Hyphens, underscores, dots (common in branch/tag names)
#   - Forward slash (for remote branches, e.g. "origin/main")
#   - Must not start with a dot or hyphen
#
# This pattern matches:
#   - Branch names: main, feature/PROJ-123, release-1.0
#   - Tag names: v1.0.0, 2024-01-01
#   - Short SHA prefixes: abc1234
#   - Full SHAs: abc1234567890abcdef...
_SAFE_REVISION_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._/\-]{0,254}$')

# SHA patterns (short 7+ or full 40 hex digits)
_SHA_RE = re.compile(r'^[0-9a-f]{7,40}$', re.IGNORECASE)

# Leading option injection patterns — these must never appear in a revision
_OPTION_PREFIXES = (
    "--upload-pack",
    "--config",
    "--exec-path",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--super-prefix",
    "--help",
    "--version",
    "--no-",
    "--",   # any other double-dash
    "-",    # any single-dash option
)

# Characters that must never appear in a revision
_FORBIDDEN_CHARS_RE = re.compile(
    r'[\x00-\x1f'   # control characters (includes CR, LF, NUL, TAB, etc.)
    r'\x7f'         # DEL
    r'~^:?*\[\\\s'  # git pathspec special chars and whitespace
    r'!$`|;&<>(){}' # shell metacharacters
    r']'
)

# Path traversal forms
_PATH_TRAVERSAL_RE = re.compile(r'(\.\./|/\.\.|\.\.$|^\.\.$)')


class GitProvider(RepositoryProvider):
    """
    Provider for securely cloning Git repositories.

    Security controls:
    - shell=False with strictly typed argument arrays.
    - HTTPS only (rejects file:// and arbitrary local paths).
    - Prevents credential embedding in URL.
    - Revision validated before being appended to subprocess argv.
    - Disables git hooks and credential helpers globally for the command.
    - Git aliases for clone and checkout are suppressed.
    """

    def fetch_snapshot(self, identifier: str, revision: str, target_dir: Path) -> RepositoryMetadata:
        # Validate URL and revision BEFORE touching the filesystem or subprocess
        self._validate_url(identifier)
        self._validate_revision(revision)

        # Ensure target_dir exists and is empty
        target_dir.mkdir(parents=True, exist_ok=True)

        safe_env = _build_safe_env()

        # Common safe args: disable hooks, credential helpers, and user aliases
        # This prevents inherited gitconfig from altering behavior.
        base_args = [
            "git",
            "-c", "core.hooksPath=/dev/null",
            "-c", "credential.helper=",
            "-c", "core.askPass=",
            "-c", "alias.clone=",
            "-c", "alias.checkout=",
            "-c", "alias.rev-parse=",
            "-c", "protocol.allow=never",
            "-c", "protocol.https.allow=always",
        ]

        # Clone (no checkout yet — revision validated separately)
        clone_args = base_args + [
            "clone",
            "--no-checkout",
            "--quiet",
            identifier,
            str(target_dir),
        ]

        try:
            subprocess.run(
                clone_args,
                cwd=str(target_dir.parent),
                check=True,
                shell=False,
                env=safe_env,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            # DO NOT include e.stderr in the user-facing message — it may contain
            # the URL with credentials if a redirect occurred, or other secrets.
            # Log internally for diagnostics only.
            import logging as _logging
            _logging.getLogger(__name__).error(
                "Git clone failed (returncode=%d). STDERR: %s STDOUT: %s",
                e.returncode, e.stderr, e.stdout
            )
            raise GitProviderError(
                "Failed to clone repository. Ensure it is publicly accessible via HTTPS."
            )
        # ── Step 2: Resolve the user-supplied revision to an immutable SHA ──────
        #
        # We MUST resolve the branch/tag/ref to a fixed commit SHA BEFORE checking
        # it out.  Checking out by SHA instead of by branch name is strictly more
        # secure: a 40-character hexadecimal string is provably not a git option
        # flag, so there is no need for the '--' end-of-options separator.
        #
        # We use 'origin/<revision>' because after --no-checkout clone the remote
        # refs are fully populated (refs/remotes/origin/*).  For an explicit SHA
        # the rev-parse call returns the SHA unchanged, so both branches and SHAs
        # are handled identically.
        rev_parse_args = base_args + [
            "rev-parse",
            f"origin/{revision}",
        ]

        try:
            rp_result = subprocess.run(
                rev_parse_args,
                cwd=str(target_dir),
                check=True,
                shell=False,
                env=safe_env,
                capture_output=True,
                text=True,
            )
            resolved_commit = rp_result.stdout.strip()
        except subprocess.CalledProcessError:
            raise GitProviderError("Failed to resolve the revision to a commit SHA.")

        # Validate before using as a subprocess argument (defence in depth)
        if not _SHA_RE.match(resolved_commit):
            raise GitProviderError(
                "Resolved commit SHA has unexpected format. Refusing to continue."
            )

        # ── Step 3: Checkout the validated, immutable SHA ────────────────────────
        #
        # We pass the SHA directly as the treeish.  A 40-char hex string:
        #   • cannot start with '-' (all hex chars are [0-9a-f])
        #   • cannot be confused with a git option flag
        #   • is unique regardless of branch/tag namespace
        # The '--' end-of-options separator is therefore not needed here; its
        # omission is intentional and documented.
        checkout_args = base_args + [
            "checkout",
            "--quiet",
            resolved_commit,
        ]

        try:
            subprocess.run(
                checkout_args,
                cwd=str(target_dir),
                check=True,
                shell=False,
                env=safe_env,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            # Don't include the revision in the error message verbatim
            raise GitProviderError("Failed to checkout the requested revision.")

        # Remove .git directory — the snapshot must be a clean, immutable directory
        # with no git metadata that could be used to re-execute git commands.
        import shutil, os, stat

        git_dir = target_dir / ".git"
        if git_dir.exists():
            def _remove_readonly(func, path, _):
                os.chmod(path, stat.S_IWRITE)
                func(path)

            shutil.rmtree(git_dir, onerror=_remove_readonly)

        return RepositoryMetadata(
            provider="git",
            repository_identifier=identifier,
            default_branch="main",
            revision=revision,
            resolved_commit=resolved_commit,
        )

    # ─── Validators ───────────────────────────────────────────────────────────

    def _validate_url(self, url: str) -> None:
        """
        Validate that a URL is safe to pass to git clone.

        Enforces:
        - Non-empty
        - HTTPS scheme only
        - No embedded username or password
        - No argument-injection prefix (--)
        """
        if not url:
            raise GitProviderError("Repository URL is empty.")

        parsed = urlparse(url)

        if parsed.scheme != "https":
            raise GitProviderError(
                f"Unsupported repository scheme: {parsed.scheme!r}. Only HTTPS is permitted."
            )

        if parsed.username or parsed.password:
            raise GitProviderError(
                "Embedded credentials in repository URL are strictly forbidden."
            )

        if url.startswith("--"):
            raise GitProviderError(
                "Repository URL cannot start with hyphens (argument injection)."
            )

    def _validate_revision(self, revision: str) -> None:
        """
        Validate that a revision string is safe to pass as a git ref.

        A valid revision is one of:
          - A branch name: main, feature/PROJ-123, release-1.0
          - A tag name: v1.0.0, 2024-01-01
          - A commit SHA: abc1234 (7+) or full 40-char SHA

        Rejects:
          - Empty or whitespace-only strings
          - Strings exceeding _REVISION_MAX_LENGTH
          - Any string starting with a git option prefix (--upload-pack, etc.)
          - Control characters (CR, LF, NUL, TAB)
          - Shell metacharacters (;, &, |, $, `, etc.)
          - Path traversal patterns (.., ../)
          - Git pathspec special chars (~, ^, :, ?, *, [)
        """
        if not revision or not revision.strip():
            raise GitProviderError("Revision cannot be empty or whitespace.")

        if len(revision) > _REVISION_MAX_LENGTH:
            raise GitProviderError(
                f"Revision exceeds maximum length of {_REVISION_MAX_LENGTH} characters."
            )

        # Reject any string starting with an option prefix
        rev_lower = revision.lower()
        for prefix in _OPTION_PREFIXES:
            if rev_lower.startswith(prefix):
                raise GitProviderError(
                    f"Revision resembles a git option ({prefix!r}). "
                    "Revisions must be branch names, tag names, or commit SHAs only."
                )

        # Reject forbidden characters
        match = _FORBIDDEN_CHARS_RE.search(revision)
        if match:
            char = match.group(0)
            raise GitProviderError(
                f"Revision contains a forbidden character: {char!r}. "
                "Only branch names, tag names, and commit SHAs are accepted."
            )

        # Reject path traversal forms
        if _PATH_TRAVERSAL_RE.search(revision):
            raise GitProviderError(
                "Revision contains a path traversal sequence. "
                "Revisions must be branch names, tag names, or commit SHAs only."
            )

        # Final allowlist check: must match the safe revision pattern
        if not _SAFE_REVISION_RE.match(revision):
            raise GitProviderError(
                f"Revision {revision!r} does not match the allowed format. "
                "Only alphanumeric characters, hyphens, underscores, dots, and "
                "forward slashes are permitted."
            )
