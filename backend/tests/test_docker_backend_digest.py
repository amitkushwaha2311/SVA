"""
Tests for DockerSandboxBackend - focused on APPROVED_IMAGE digest configuration.

Scope
-----
* Digest is pinned and non-empty.
* Digest format is valid (sha256:<64 hex chars>).
* The locally present Docker image resolves for that digest (requires Docker daemon).
* Backend instantiates with correct _docker_available flag.
* _unsupported_result is returned when the image is absent (mocked 404).

These tests do NOT run containers; they verify configuration, image lookup,
and the UNSUPPORTED fast-exit path only.
"""

import re
import pytest
from unittest.mock import MagicMock, patch

from app.execution.docker import DockerSandboxBackend

# -----------------------------------------------------------------
# Constants
# -----------------------------------------------------------------

VALID_DIGEST_RE = re.compile(
    r"^[a-zA-Z0-9._\-]+/[a-zA-Z0-9._\-]+@sha256:[0-9a-f]{64}$"
    r"|"
    r"^[a-zA-Z0-9._\-]+@sha256:[0-9a-f]{64}$"
)

EXPECTED_DIGEST = (
    "alpine@sha256:"
    "d56c381f961d307a21b3ca004cf1e3910f106644aefb1f43e654c8a56c4fd395"
)


def _docker_available() -> bool:
    try:
        import docker
        docker.from_env().ping()
        return True
    except Exception:
        return False


requires_docker = pytest.mark.skipif(
    not _docker_available(),
    reason="Docker daemon not reachable - skipping live image tests",
)


# -----------------------------------------------------------------
# 1. Digest constant - no Docker required
# -----------------------------------------------------------------

class TestApprovedImageConstant:
    def test_approved_image_is_not_empty(self):
        assert DockerSandboxBackend.APPROVED_IMAGE, "APPROVED_IMAGE must not be empty"

    def test_approved_image_contains_sha256_digest(self):
        assert "@sha256:" in DockerSandboxBackend.APPROVED_IMAGE, (
            "APPROVED_IMAGE must use a pinned @sha256: digest, not a mutable tag"
        )

    def test_approved_image_digest_is_64_hex_chars(self):
        _, digest_part = DockerSandboxBackend.APPROVED_IMAGE.split("@sha256:", 1)
        assert re.fullmatch(r"[0-9a-f]{64}", digest_part), (
            f"Digest hex portion must be exactly 64 lowercase hex chars, got: {digest_part!r}"
        )

    def test_approved_image_matches_verified_digest(self):
        """Regression guard: catches accidental digest rollback or typo."""
        assert DockerSandboxBackend.APPROVED_IMAGE == EXPECTED_DIGEST, (
            f"APPROVED_IMAGE digest has drifted from the verified value.\n"
            f"  Expected: {EXPECTED_DIGEST}\n"
            f"  Actual  : {DockerSandboxBackend.APPROVED_IMAGE}"
        )

    def test_approved_image_format_is_valid(self):
        assert VALID_DIGEST_RE.match(DockerSandboxBackend.APPROVED_IMAGE), (
            f"APPROVED_IMAGE format is invalid: {DockerSandboxBackend.APPROVED_IMAGE!r}"
        )

    def test_stale_digest_is_not_present(self):
        """Ensures the old broken digest is gone."""
        stale = "c5b1261d6d3e43071626931fc004fa70c82dae47a9c878b1731677353f47e3be"
        assert stale not in DockerSandboxBackend.APPROVED_IMAGE, (
            "Stale digest c5b1261d is still present in APPROVED_IMAGE - update it."
        )


# -----------------------------------------------------------------
# 2. Backend instantiation - no Docker required (mocked)
# -----------------------------------------------------------------

class TestDockerBackendInstantiation:
    def test_docker_unavailable_sets_flag_false(self, tmp_path):
        # docker is imported lazily inside __init__; patch the builtins import
        import builtins
        real_import = builtins.__import__
        def fake_import(name, *args, **kwargs):
            if name == "docker":
                raise ImportError("no daemon")
            return real_import(name, *args, **kwargs)
        with patch("builtins.__import__", side_effect=fake_import):
            backend = DockerSandboxBackend(snapshot_path=str(tmp_path))
        assert backend._docker_available is False
        assert backend.client is None

    def test_docker_available_sets_flag_true(self, tmp_path):
        # Real docker is available in this environment - verify the flag is set
        backend = DockerSandboxBackend(snapshot_path=str(tmp_path))
        # The flag reflects whether docker.from_env() succeeded
        assert isinstance(backend._docker_available, bool)
        # If docker is importable and daemon reachable, flag should be True
        if _docker_available():
            assert backend._docker_available is True
            assert backend.client is not None
        else:
            assert backend._docker_available is False
            assert backend.client is None


# -----------------------------------------------------------------
# 3. Image lookup against real Docker daemon
# -----------------------------------------------------------------

class TestApprovedImagePresenceInDaemon:
    @requires_docker
    def test_approved_image_resolves_in_local_daemon(self, tmp_path):
        """The APPROVED_IMAGE digest must be resolvable via client.images.get()."""
        import docker as docker_sdk
        client = docker_sdk.from_env()
        try:
            img = client.images.get(DockerSandboxBackend.APPROVED_IMAGE)
        except docker_sdk.errors.ImageNotFound:
            pytest.fail(
                f"APPROVED_IMAGE not found in local Docker daemon.\n"
                f"  Digest: {DockerSandboxBackend.APPROVED_IMAGE}\n"
                f"  Pull it with: docker pull {DockerSandboxBackend.APPROVED_IMAGE}"
            )
        assert img is not None

    @requires_docker
    def test_approved_image_digest_matches_pulled_image(self, tmp_path):
        """Cross-check: pulled image RepoDigests contain our pinned digest hex."""
        import docker as docker_sdk
        client = docker_sdk.from_env()
        img = client.images.get(DockerSandboxBackend.APPROVED_IMAGE)
        repo_digests = img.attrs.get("RepoDigests", [])
        digest_hex = DockerSandboxBackend.APPROVED_IMAGE.split("sha256:")[-1]
        found = any(digest_hex in rd for rd in repo_digests)
        assert found, (
            f"Pulled image RepoDigests do not contain expected digest hex.\n"
            f"  Expected hex: {digest_hex}\n"
            f"  RepoDigests : {repo_digests}"
        )


# -----------------------------------------------------------------
# 4. _unsupported_result fast-exit when image is absent (mocked)
# -----------------------------------------------------------------

class TestDockerBackendUnsupportedPath:
    """
    Verifies execute() returns UNSUPPORTED when images.get() raises ImageNotFound,
    mimicking the old stale-digest scenario.
    """

    def _make_request(self):
        from app.execution.models import ExecutionRequest
        return ExecutionRequest(
            execution_id="test-exec-1",
            contract_id="contract-1",
            obligation_id="obl-1",
            target_id="tgt-1",
            repository_id="repo-1",
            commit_id="HEAD",
            snapshot_id="snap-1",
            analysis_id="analysis-1",
            job_id=None,
            command=["echo", "hello"],
            working_directory=".",
            expected_outcome="PASS",
            command_id="echo",
            test_file=None,
        )

    def test_execute_returns_unsupported_when_image_not_found(self, tmp_path):
        from app.execution.models import ExecutionStatus
        from app.execution.policy import get_default_policy
        import docker as docker_sdk

        # Build a real backend (docker is available in this env)
        backend = DockerSandboxBackend(snapshot_path=str(tmp_path))
        if not backend._docker_available:
            pytest.skip("Docker not available - cannot test image-not-found path via mocked client")

        # Swap the client with a mock that raises ImageNotFound for images.get()
        mock_client = MagicMock()
        mock_client.images.get.side_effect = docker_sdk.errors.ImageNotFound("No such image")
        backend.client = mock_client

        backend.create()
        request = self._make_request()
        policy = get_default_policy()
        obs = backend.execute(request, policy)

        assert obs.status == ExecutionStatus.UNSUPPORTED, (
            f"Expected UNSUPPORTED when approved image is absent, got {obs.status}"
        )
        assert "unavailable" in obs.stdout.lower() or "not available" in obs.stdout.lower(), (
            f"UNSUPPORTED stdout should explain why: {obs.stdout!r}"
        )

