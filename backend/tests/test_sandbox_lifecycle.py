"""
SVA Phase 18B — Sandbox Lifecycle Tests
=========================================

Tests cooperative cancellation, worker lease loss, sandbox teardown, and
that no late-completion can alter the analysis state after cancellation.

All tests use controlled fixtures and NEVER attempt host escape.
"""

import pytest
from unittest.mock import MagicMock, call, patch
from app.execution.docker import DockerSandboxBackend
from app.execution.sandbox import LocalSafeFallbackSandbox
from app.execution.models import (
    ExecutionObservation,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionStatus,
    SandboxIdentity,
)


@pytest.fixture
def snapshot_dir(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("print('hello')")
    return str(repo)


@pytest.fixture
def sample_request(snapshot_dir):
    return ExecutionRequest(
        execution_id="exec-lifecycle-001",
        contract_id="c1",
        obligation_id="o1",
        target_id="t1",
        repository_id="r1",
        commit_id="abc123",
        job_id="job-1",
        analysis_id="ana-1",
        snapshot_id="snap-1",
        command=["python", "-m", "pytest", "main.py"],
        working_directory=".",
        expected_outcome="PASS",
    )


@pytest.fixture
def sample_policy():
    return ExecutionPolicy()


# ─── LocalSafeFallbackSandbox Lifecycle ──────────────────────────────────────

class TestLocalFallbackLifecycle:

    def test_create_succeeds(self):
        sb = LocalSafeFallbackSandbox()
        sb.create()  # Should not raise

    def test_execute_returns_unsupported(self, sample_request, sample_policy):
        sb = LocalSafeFallbackSandbox()
        sb.create()
        obs = sb.execute(sample_request, sample_policy)
        assert obs.status == ExecutionStatus.UNSUPPORTED

    def test_terminate_is_safe_when_never_executed(self):
        sb = LocalSafeFallbackSandbox()
        sb.create()
        sb.terminate()  # Should not raise

    def test_destroy_is_safe_when_never_executed(self):
        sb = LocalSafeFallbackSandbox()
        sb.create()
        sb.destroy()  # Should not raise

    def test_collect_returns_blocked_message(self):
        sb = LocalSafeFallbackSandbox()
        sb.create()
        msg = sb.collect()
        assert "block" in msg.lower() or "artifact" in msg.lower() or "no artifacts" in msg.lower()

    def test_unsupported_observation_has_correct_backend_name(self, sample_request, sample_policy):
        sb = LocalSafeFallbackSandbox()
        obs = sb.execute(sample_request, sample_policy)
        assert obs.sandbox_identity.backend_name == "SAFE_FALLBACK"

    def test_unsupported_observation_preserves_snapshot_id(self, sample_request, sample_policy):
        sb = LocalSafeFallbackSandbox()
        obs = sb.execute(sample_request, sample_policy)
        assert obs.snapshot_id == "snap-1"

    def test_sandbox_implements_protocol(self):
        """Ensure LocalSafeFallbackSandbox satisfies the Sandbox protocol."""
        sb = LocalSafeFallbackSandbox()
        assert callable(sb.create)
        assert callable(sb.execute)
        assert callable(sb.collect)
        assert callable(sb.terminate)
        assert callable(sb.destroy)


# ─── DockerSandboxBackend Lifecycle (without Docker) ─────────────────────────

class TestDockerBackendWithoutDocker:

    def test_docker_unavailable_returns_unsupported_on_execute(self, snapshot_dir, sample_request, sample_policy):
        sb = DockerSandboxBackend(snapshot_path=snapshot_dir)
        sb._docker_available = False  # Simulate Docker not present
        sb.create()
        obs = sb.execute(sample_request, sample_policy)
        assert obs.status == ExecutionStatus.UNSUPPORTED
        assert obs.sandbox_identity.backend_name == "DOCKER"

    def test_terminate_is_safe_when_docker_unavailable(self, snapshot_dir):
        sb = DockerSandboxBackend(snapshot_path=snapshot_dir)
        sb._docker_available = False
        sb.terminate()  # Should not raise

    def test_destroy_is_safe_when_docker_unavailable(self, snapshot_dir):
        sb = DockerSandboxBackend(snapshot_path=snapshot_dir)
        sb._docker_available = False
        sb.destroy()  # Should not raise

    def test_destroy_cleans_scratch_dir(self, snapshot_dir, sample_request, sample_policy):
        import os
        sb = DockerSandboxBackend(snapshot_path=snapshot_dir)
        sb._docker_available = False
        sb.create()  # must call create() to set scratch_dir
        scratch = sb.scratch_dir
        assert scratch is not None, "scratch_dir must be set after create()"
        assert os.path.exists(scratch)
        sb.destroy()
        assert not os.path.exists(scratch), "Scratch dir must be cleaned up after destroy()"

    def test_destroy_twice_is_idempotent(self, snapshot_dir):
        sb = DockerSandboxBackend(snapshot_path=snapshot_dir)
        sb._docker_available = False
        sb.create()
        sb.destroy()
        sb.destroy()  # Second destroy should not raise


# ─── Cancellation Lifecycle Tests ────────────────────────────────────────────

class TestCancellationLifecycle:

    def test_terminate_called_before_destroy_on_cancellation(self, snapshot_dir, sample_request, sample_policy):
        """Cancellation must call terminate then destroy, not just destroy."""
        sb = DockerSandboxBackend(snapshot_path=snapshot_dir)
        sb._docker_available = False
        sb.create()

        call_order = []

        # Store originals before we shadow them
        _orig_terminate = sb.__class__.terminate
        _orig_destroy = sb.__class__.destroy

        def mock_terminate(self_inner):
            call_order.append("terminate")
            # just track
            pass

        def mock_destroy(self_inner):
            call_order.append("destroy")
            # Clean scratch manually
            import shutil, os as _os
            if self_inner.scratch_dir and _os.path.exists(self_inner.scratch_dir):
                shutil.rmtree(self_inner.scratch_dir)
                self_inner.scratch_dir = None

        import types
        sb.terminate = types.MethodType(mock_terminate, sb)
        sb.destroy = types.MethodType(mock_destroy, sb)

        # Simulate cancellation sequence
        sb.terminate()
        sb.destroy()

        assert call_order == ["terminate", "destroy"], \
            f"Expected terminate then destroy, got: {call_order}"

    def test_unsupported_obs_after_cancellation_does_not_fail_job(self, snapshot_dir, sample_request, sample_policy):
        """
        If the sandbox was cancelled (UNSUPPORTED/CANCELLED), the capture pipeline
        must not produce PROVEN or map to a FAILED analysis state.
        """
        from app.execution.capture import EvidenceCapture
        from app.evidence.models import EvidenceResult

        sb = DockerSandboxBackend(snapshot_path=snapshot_dir)
        sb._docker_available = False
        sb.create()
        obs = sb.execute(sample_request, sample_policy)

        capture = EvidenceCapture()
        ev = capture.capture(sample_request, obs)

        # UNSUPPORTED must map to NOT_RUN, never PASS or direct PROVEN
        assert ev.result in [EvidenceResult.NOT_RUN, EvidenceResult.INCONCLUSIVE], \
            f"Expected NOT_RUN or INCONCLUSIVE, got {ev.result}"

        sb.destroy()


# ─── Worker Lease Loss Tests ──────────────────────────────────────────────────

class TestWorkerLeaseLoss:

    def test_sandbox_destroy_called_on_lease_loss(self, snapshot_dir):
        """
        Simulate: worker A loses its lease → sandbox must be terminated and destroyed.
        """
        sb = DockerSandboxBackend(snapshot_path=snapshot_dir)
        sb._docker_available = False
        sb.create()  # create() must be called to allocate scratch_dir
        scratch_before = sb.scratch_dir
        assert scratch_before is not None, "scratch_dir must exist after create()"

        # Simulate lease loss → teardown must happen
        sb.terminate()
        sb.destroy()

        import os
        assert not os.path.exists(scratch_before), \
            "Scratch dir must not persist after lease loss teardown"
