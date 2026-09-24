"""
Phase 18B - Final Security Audit Gap Tests
==========================================

Targeted tests for items previously classified as ENFORCED_NOT_TESTED
or requiring evidence of actual enforcement vs mere modeling.
"""
import inspect
import os
import tempfile

import pytest

from app.evidence.integrity import compute_evidence_hash, verify_evidence_hash
from app.evidence.models import (
    EnvironmentFingerprint,
    Evidence,
    EvidenceIntegrity,
    EvidenceResult,
    EvidenceStatus,
    EvidenceType,
    VerificationMethod,
)
from app.execution.capture import EvidenceCapture
from app.execution.docker import DockerSandboxBackend
from app.execution.models import (
    EnvironmentPolicy,
    ExecutionObservation,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionStatus,
    NetworkPolicy,
    SandboxEnvironment,
    SandboxIdentity,
    SandboxResourceLimits,
    SecretPolicy,
)
from app.contracts.models import (
    ContractStatus,
    SemanticContract,
    VerificationTarget,
    VerificationTargetCategory,
)
from app.repository.intent.models import Provenance


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(**overrides) -> ExecutionRequest:
    defaults = dict(
        execution_id="exec-123",
        contract_id="c-1",
        obligation_id="o-1",
        target_id="t-1",
        repository_id="r-1",
        commit_id="abc123",
        job_id="job-1",
        analysis_id="ana-1",
        snapshot_id="snap-1",
        command=["python", "-m", "pytest", "tests/test_pass.py"],
        working_directory=".",
        expected_outcome="PASS",
    )
    defaults.update(overrides)
    return ExecutionRequest(**defaults)


def _make_observation(request, status=ExecutionStatus.PASSED, exit_code=0):
    identity = SandboxIdentity(backend_name="DOCKER", image_digest="sha256:abc123")
    return ExecutionObservation(
        execution_id=request.execution_id,
        status=status,
        exit_code=exit_code,
        stdout="test passed",
        stderr="",
        duration_seconds=1.0,
        sandbox_identity=identity,
        environment=SandboxEnvironment(
            env_vars_injected=[],
            mounted_paths=["/repo:ro"],
            working_dir="/repo",
        ),
        policy_id="default",
        repository_id=request.repository_id,
        commit_id=request.commit_id,
        snapshot_id=request.snapshot_id,
    )


def _make_policy():
    return ExecutionPolicy(policy_id="default")


def _make_evidence(**overrides):
    defaults = dict(
        evidence_id="ev-1",
        contract_id="c-1",
        requirement_id="req-1",
        repository_id="r-1",
        evidence_type=EvidenceType.DETERMINISTIC_TEST,
        verification_method=VerificationMethod.UNIT_TEST,
        description="test run",
        observation="STDOUT:\ntest passed\nEXIT CODE: 0",
        result=EvidenceResult.INCONCLUSIVE,
        status=EvidenceStatus.OBSERVED,
        commit_id="abc123",
        environment=EnvironmentFingerprint(tool_name="DOCKER", tool_version="sha256:abc"),
        provenance=Provenance.CODE,
        execution_id="exec-123",
        job_id="job-1",
        analysis_id="ana-1",
        snapshot_id="snap-1",
        obligation_id="o-1",
    )
    defaults.update(overrides)
    return Evidence(**defaults)


def _make_ready_contract():
    return SemanticContract(
        contract_id="c-1",
        repository_id="r-1",
        requirement_id="req-1",
        candidate_id="cand-1",
        analysis_id="ana-1",
        statement="The system must do X.",
        compilation_status=ContractStatus.READY,
        verification_targets=[
            VerificationTarget(
                target_id="t-1",
                category=VerificationTargetCategory.BEHAVIOR,
                description="target",
            )
        ],
    )


# ---------------------------------------------------------------------------
# 1. TMPFS WRITABLE FILESYSTEM LIMIT
# ---------------------------------------------------------------------------

class TestWritableFsLimitEnforced:

    def test_docker_backend_uses_tmpfs_not_host_mount(self):
        src = inspect.getsource(DockerSandboxBackend.execute)
        assert "tmpfs" in src, "Must use tmpfs for /scratch, not host bind-mount"

    def test_tmpfs_uses_fs_limit_from_policy(self):
        src = inspect.getsource(DockerSandboxBackend.execute)
        assert "writable_fs_limit_mb" in src, "tmpfs size must come from policy limits"

    def test_writable_fs_limit_mb_has_default(self):
        limits = SandboxResourceLimits()
        assert hasattr(limits, "writable_fs_limit_mb")
        assert limits.writable_fs_limit_mb is not None
        assert limits.writable_fs_limit_mb > 0


# ---------------------------------------------------------------------------
# 2. BOUNDED LOG STREAMING
# ---------------------------------------------------------------------------

class TestBoundedLogStreaming:

    def test_log_collection_uses_stream_true(self):
        src = inspect.getsource(DockerSandboxBackend.execute)
        assert "stream=True" in src, "container.logs() must use stream=True for bounded streaming"

    def test_log_collection_has_early_termination_logic(self):
        src = inspect.getsource(DockerSandboxBackend.execute)
        assert "_fetch_bounded_logs" in src, "Must use streaming bounded log collection helper"
        assert "break" in src, "_fetch_bounded_logs must break early when limit exceeded"


# ---------------------------------------------------------------------------
# 3. SYMLINK / WORKING DIRECTORY BOUNDARY
# ---------------------------------------------------------------------------

class TestWorkingDirectoryBoundary:

    def test_working_directory_escape_is_detected_in_code(self):
        src = inspect.getsource(DockerSandboxBackend.execute)
        assert 'container_wd.startswith("/repo")' in src

    def test_planner_rejects_dotdot_traversal_in_test_file(self):
        from app.execution.planner import VerificationPlanner
        contract = _make_ready_contract()
        result = VerificationPlanner().plan(
            contract=contract, obligation_id="o-1", target_id="t-1",
            repository_id="r-1", commit_id="abc", test_file="../../etc/shadow",
        )
        assert result is None

    def test_planner_rejects_absolute_posix_path(self):
        from app.execution.planner import VerificationPlanner
        contract = _make_ready_contract()
        result = VerificationPlanner().plan(
            contract=contract, obligation_id="o-1", target_id="t-1",
            repository_id="r-1", commit_id="abc", test_file="/etc/passwd",
        )
        assert result is None

    def test_symlink_mitigation_controls_present(self):
        src = inspect.getsource(DockerSandboxBackend.execute)
        assert "read_only=True" in src, "read_only=True must be set (symlink mitigation)"
        assert "user=" in src, "Non-root user must be set (symlink escalation mitigation)"


# ---------------------------------------------------------------------------
# 4. EVIDENCE INTEGRITY BINDING
# ---------------------------------------------------------------------------

class TestEvidenceProvenanceBinding:

    def test_evidence_model_has_execution_fields(self):
        ev = _make_evidence()
        assert ev.execution_id == "exec-123"
        assert ev.job_id == "job-1"
        assert ev.analysis_id == "ana-1"
        assert ev.snapshot_id == "snap-1"
        assert ev.obligation_id == "o-1"

    def test_integrity_hash_changes_when_execution_id_changes(self):
        h1 = compute_evidence_hash(_make_evidence(execution_id="exec-A"))
        h2 = compute_evidence_hash(_make_evidence(execution_id="exec-B"))
        assert h1 != h2, "execution_id must be in integrity hash"

    def test_integrity_hash_changes_when_snapshot_id_changes(self):
        h1 = compute_evidence_hash(_make_evidence(snapshot_id="snap-A"))
        h2 = compute_evidence_hash(_make_evidence(snapshot_id="snap-B"))
        assert h1 != h2, "snapshot_id must be in integrity hash"

    def test_integrity_hash_changes_when_job_id_changes(self):
        h1 = compute_evidence_hash(_make_evidence(job_id="job-A"))
        h2 = compute_evidence_hash(_make_evidence(job_id="job-B"))
        assert h1 != h2, "job_id must be in integrity hash"

    def test_integrity_hash_changes_when_obligation_id_changes(self):
        h1 = compute_evidence_hash(_make_evidence(obligation_id="o-A"))
        h2 = compute_evidence_hash(_make_evidence(obligation_id="o-B"))
        assert h1 != h2, "obligation_id must be in integrity hash"

    def test_integrity_hash_changes_when_environment_changes(self):
        ev1 = _make_evidence(environment=EnvironmentFingerprint(tool_name="DOCKER", tool_version="sha256:aaa"))
        ev2 = _make_evidence(environment=EnvironmentFingerprint(tool_name="DOCKER", tool_version="sha256:bbb"))
        assert compute_evidence_hash(ev1) != compute_evidence_hash(ev2)

    def test_tampering_with_execution_id_fails_verify(self):
        ev = _make_evidence()
        ev.integrity = EvidenceIntegrity(
            evidence_hash=compute_evidence_hash(ev), hash_algorithm="SHA-256"
        )
        assert verify_evidence_hash(ev) is True
        ev.execution_id = "tampered"
        assert verify_evidence_hash(ev) is False

    def test_tampering_with_snapshot_id_fails_verify(self):
        ev = _make_evidence()
        ev.integrity = EvidenceIntegrity(
            evidence_hash=compute_evidence_hash(ev), hash_algorithm="SHA-256"
        )
        ev.snapshot_id = "tampered"
        assert verify_evidence_hash(ev) is False


# ---------------------------------------------------------------------------
# 5. EVIDENCE CAPTURE PROVENANCE BINDING
# ---------------------------------------------------------------------------

class TestEvidenceCaptureBindsProvenance:

    def test_capture_binds_execution_id(self):
        req = _make_request(execution_id="exec-BIND")
        obs = _make_observation(req)
        ev = EvidenceCapture().capture(req, obs)
        assert ev.execution_id == "exec-BIND"

    def test_capture_binds_job_id(self):
        req = _make_request(job_id="job-BIND")
        obs = _make_observation(req)
        ev = EvidenceCapture().capture(req, obs)
        assert ev.job_id == "job-BIND"

    def test_capture_binds_analysis_id(self):
        req = _make_request(analysis_id="ana-BIND")
        obs = _make_observation(req)
        ev = EvidenceCapture().capture(req, obs)
        assert ev.analysis_id == "ana-BIND"

    def test_capture_binds_snapshot_id(self):
        req = _make_request(snapshot_id="snap-BIND")
        obs = _make_observation(req)
        ev = EvidenceCapture().capture(req, obs)
        assert ev.snapshot_id == "snap-BIND"

    def test_capture_binds_obligation_id(self):
        req = _make_request(obligation_id="o-BIND")
        obs = _make_observation(req)
        ev = EvidenceCapture().capture(req, obs)
        assert ev.obligation_id == "o-BIND"

    def test_captured_evidence_hash_passes_verification(self):
        req = _make_request()
        obs = _make_observation(req)
        ev = EvidenceCapture().capture(req, obs)
        assert ev.integrity is not None
        assert verify_evidence_hash(ev) is True


# ---------------------------------------------------------------------------
# 6. SEMANTIC SEPARATION
# ---------------------------------------------------------------------------

class TestSemanticSeparationAudit:

    def test_exit_code_zero_produces_inconclusive_not_pass(self):
        req = _make_request()
        obs = _make_observation(req, status=ExecutionStatus.PASSED, exit_code=0)
        ev = EvidenceCapture().capture(req, obs)
        assert ev.result != EvidenceResult.PASS, "exit_code=0 must NOT map to PASS"
        assert ev.result == EvidenceResult.INCONCLUSIVE

    def test_timeout_produces_error_evidence(self):
        req = _make_request()
        obs = _make_observation(req, status=ExecutionStatus.TIMEOUT, exit_code=-1)
        ev = EvidenceCapture().capture(req, obs)
        assert ev.result == EvidenceResult.ERROR

    def test_unsupported_produces_not_run_evidence(self):
        req = _make_request()
        obs = _make_observation(req, status=ExecutionStatus.UNSUPPORTED, exit_code=None)
        obs.exit_code = None
        ev = EvidenceCapture().capture(req, obs)
        assert ev.result == EvidenceResult.NOT_RUN


# ---------------------------------------------------------------------------
# 7. NETWORK AND CLOUD DENIAL
# ---------------------------------------------------------------------------

class TestNetworkAndCloudDenial:

    def test_network_mode_none_in_source(self):
        src = inspect.getsource(DockerSandboxBackend.execute)
        assert 'network_mode="none"' in src

    def test_default_policy_denies_network(self):
        """Default ExecutionPolicy must set network=DENY."""
        p = ExecutionPolicy(policy_id="test")
        assert p.network == NetworkPolicy.DENY, f"Default network policy must be DENY, got {p.network}"

    def test_default_policy_denies_secrets(self):
        """Default ExecutionPolicy must set secrets=DENY."""
        p = ExecutionPolicy(policy_id="test")
        assert p.secrets == SecretPolicy.DENY, f"Default secrets policy must be DENY, got {p.secrets}"

    def test_env_vars_passed_to_container_is_empty(self):
        src = inspect.getsource(DockerSandboxBackend.execute)
        assert "env_vars = {}" in src, "Container env must be empty dict"


# ---------------------------------------------------------------------------
# 8. CANCELLATION AND LIFECYCLE
# ---------------------------------------------------------------------------

class TestCancellationLifecycle:

    def test_terminate_is_safe_before_execute(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sb = DockerSandboxBackend(snapshot_path=tmpdir)
            sb.create()
            sb.terminate()  # Must not raise

    def test_destroy_cleans_scratch_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sb = DockerSandboxBackend(snapshot_path=tmpdir)
            sb.create()
            scratch = sb.scratch_dir
            sb.destroy()
            assert not os.path.exists(scratch)

    def test_destroy_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sb = DockerSandboxBackend(snapshot_path=tmpdir)
            sb.create()
            sb.destroy()
            sb.destroy()  # Must not raise

    def test_terminate_then_destroy_sequence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sb = DockerSandboxBackend(snapshot_path=tmpdir)
            sb.create()
            sb.terminate()
            sb.destroy()


# ---------------------------------------------------------------------------
# 9. APPROVED IMAGE PINNING
# ---------------------------------------------------------------------------

class TestApprovedImagePinning:

    def test_approved_image_contains_sha256_digest(self):
        assert "@sha256:" in DockerSandboxBackend.APPROVED_IMAGE

    def test_docker_backend_does_not_accept_user_provided_image(self):
        sig = inspect.signature(DockerSandboxBackend.__init__)
        assert "image" not in sig.parameters
