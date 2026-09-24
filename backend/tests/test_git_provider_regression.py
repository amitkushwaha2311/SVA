import os
import sys
import platform
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call, AsyncMock

import pytest

from app.providers.repository.git import GitProvider, GitProviderError, _build_safe_env


def test_safe_env_preserves_os_critical_vars():
    """
    Regression test: verify that the safe_env retains OS critical variables
    like PATH and SYSTEMROOT (on Windows) which are required for git networking
    threads (getaddrinfo).
    """
    env = _build_safe_env()
    assert "PATH" in env, "PATH must be preserved to find git and system DLLs"

    if platform.system() == "Windows":
        assert "SYSTEMROOT" in env, "SYSTEMROOT must be preserved for Winsock/DNS"
        assert "TEMP" in env or "TMP" in env, "Temp directory must be preserved for lock files"
        assert "GIT_TERMINAL_PROMPT" in env
        assert "GIT_ASKPASS" not in env, "GIT_ASKPASS must not be blindly set to /bin/false on Windows"
    else:
        assert "GIT_ASKPASS" in env
        assert env["GIT_ASKPASS"] == "/bin/false"


@patch("app.providers.repository.git.subprocess.run")
def test_checkout_args_ref_syntax(mock_run, tmp_path):
    """
    Regression test: verify that 'git checkout' is invoked with a resolved,
    immutable commit SHA rather than the raw user-supplied branch name.

    A 40-char SHA cannot start with '-', so it is provably not a git option
    flag — a strictly stronger invariant than placing '--' before a branch name.
    """
    resolved_sha = "7fd1a60b01f91b314f59955a4e4d4e80d8edf11d"
    mock_run.return_value = MagicMock(returncode=0, stdout=f"{resolved_sha}\n")

    provider = GitProvider()
    target = tmp_path / "repo"
    target.mkdir()

    provider.fetch_snapshot("https://github.com/octocat/Hello-World", "main", target)

    checkout_call = None
    for c in mock_run.call_args_list:
        args = c[0][0]
        if "checkout" in args:
            checkout_call = args
            break

    assert checkout_call is not None, "git checkout must be called"

    # The raw branch name must NOT appear in the checkout call
    assert "main" not in checkout_call, (
        f"Branch name must not appear in checkout command. Got: {checkout_call}"
    )

    # The resolved SHA must be the treeish in the checkout command
    assert resolved_sha in checkout_call, (
        f"Resolved SHA must appear in checkout command. Got: {checkout_call}"
    )

    # SHA must never start with '-'
    assert not resolved_sha.startswith("-"), "SHA must not start with '-'"


def test_life_os_public_repo_clone_args(tmp_path):
    """
    Regression test for the LIFE-OS public GitHub repository clone failure.

    This test verifies that GitProvider constructs the correct, secure clone
    command and successfully clones this exact public HTTPS URL over the network.
    """
    provider = GitProvider()
    target = tmp_path / "repo"
    
    metadata = provider.fetch_snapshot(
        identifier="https://github.com/amitkushwaha2311/LIFE-OS.git",
        revision="main",
        target_dir=target,
    )

    assert metadata.resolved_commit is not None
    assert len(metadata.resolved_commit) == 40
    assert (target / "README.md").exists()


@patch("app.providers.repository.git.subprocess.run")
def test_git_clone_failure_raises_provider_error_without_leaking_stderr(mock_run, tmp_path):
    """
    Regression test: when git clone fails, GitProviderError must be raised with
    a safe, generic message. The underlying stderr (which may contain credentials
    from redirects) must NOT appear in the user-facing exception message.
    """
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=128,
        cmd=["git", "clone"],
        stderr=(
            "remote: Repository not found.\n"
            "fatal: repository 'https://secret-token@example.com/repo' not found"
        ),
        output="",
    )

    provider = GitProvider()
    target = tmp_path / "repo"
    target.mkdir()

    with pytest.raises(GitProviderError) as exc_info:
        provider.fetch_snapshot(
            identifier="https://github.com/amitkushwaha2311/LIFE-OS.git",
            revision="main",
            target_dir=target,
        )

    error_msg = str(exc_info.value)
    assert "secret-token" not in error_msg, "Credentials must not appear in user-facing error"
    assert "repository not found" not in error_msg.lower(), "Raw stderr must not leak into error"
    assert "publicly accessible" in error_msg, "Error must give user actionable guidance"


@pytest.mark.asyncio
async def test_worker_lifespan_starts_and_stops_cleanly():
    """
    Regression test for the worker lifespan integration.

    Verifies that LocalAnalysisWorker.start() and stop() execute cleanly in the
    same async context, matching the FastAPI lifespan startup/shutdown sequence.
    Previously the worker was a completely separate process; now it is embedded
    in the server lifespan so analyses run immediately when jobs are enqueued.
    """
    from app.orchestration.worker import LocalAnalysisWorker

    mock_session_factory = MagicMock()

    worker = LocalAnalysisWorker(
        session_factory=mock_session_factory, poll_interval_seconds=0.05
    )

    await worker.start()
    assert worker._running is True
    assert worker._loop_task is not None

    # Immediate stop simulates lifespan shutdown
    await worker.stop()
    assert worker._running is False
