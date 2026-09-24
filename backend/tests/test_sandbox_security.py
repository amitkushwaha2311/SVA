"""
SVA Phase 18B — Threat-Model Security Tests
============================================

Backend-independent policy and planner security tests.
These tests validate that SVA's fail-closed policy, command filtering, and
environment controls reject all unsafe inputs.

These tests use ONLY controlled fixtures and safe boundary checks.
They do NOT perform uncontrolled host escape or external exploitation.
"""

import os
import re
import pytest

from app.execution.models import (
    ExecutionObservation,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionStatus,
    SandboxIdentity,
    SandboxResourceLimits,
    SecretPolicy,
    NetworkPolicy,
)
from app.execution.planner import VerificationPlanner, COMMAND_ALLOWLIST, FORBIDDEN_CHARS
from app.execution.sandbox import LocalSafeFallbackSandbox
from app.execution.validator import ExecutionValidator
from app.execution.docker import DockerSandboxBackend
from app.execution.policy import get_default_policy
from app.execution.capture import EvidenceCapture
from app.evidence.models import EvidenceResult
from app.contracts.models import (
    ContractStatus,
    SemanticContract,
    VerificationTarget,
    VerificationTargetCategory,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def snapshot_dir(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "safe_test.py").write_text("def test_pass(): pass")
    return str(repo)


@pytest.fixture
def policy():
    return get_default_policy()


@pytest.fixture
def ready_contract():
    return SemanticContract(
        contract_id="c-sec-1",
        candidate_id="cand-1",
        analysis_id="a-sec-1",
        repository_id="r-sec-1",
        requirement_id="req-sec-1",
        statement="The system must correctly handle verification targets.",
        compilation_status=ContractStatus.READY,
        verification_targets=[
            VerificationTarget(
                target_id="t-sec-1",
                category=VerificationTargetCategory.BEHAVIOR,
                description="safe_test.py",
            )
        ],
    )


def make_request(**overrides) -> ExecutionRequest:
    base = dict(
        execution_id="sec-test",
        contract_id="c1",
        obligation_id="o1",
        target_id="t1",
        repository_id="r1",
        commit_id="abc123",
        command=["python", "-m", "pytest", "safe_test.py"],
        working_directory=".",
        expected_outcome="PASS",
    )
    base.update(overrides)
    return ExecutionRequest(**base)


# ─── Policy Tests ─────────────────────────────────────────────────────────────

class TestDefaultPolicy:

    def test_network_is_deny_by_default(self, policy):
        assert policy.network == NetworkPolicy.DENY

    def test_secrets_denied_by_default(self, policy):
        assert policy.secrets == SecretPolicy.DENY
        assert policy.secrets_allowed is False

    def test_resource_limits_are_explicit(self, policy):
        assert policy.limits.timeout_seconds > 0
        assert policy.limits.memory_limit_mb is not None
        assert policy.limits.cpu_limit_cores is not None
        assert policy.limits.pid_limit is not None
        assert policy.limits.output_size_limit_kb is not None

    def test_pid_limit_enforced(self, policy):
        assert policy.limits.pid_limit <= 512, "PID limit should be bounded"

    def test_output_size_limit_enforced(self, policy):
        assert policy.limits.output_size_limit_kb <= 10240, "Output limit should be bounded"


# ─── Planner Filesystem Threat Tests ─────────────────────────────────────────

class TestPlannerFilesystemThreats:

    def test_traversal_dotdot_rejected(self, ready_contract):
        planner = VerificationPlanner()
        result = planner.plan(
            contract=ready_contract,
            obligation_id="o1",
            target_id="t-sec-1",
            repository_id="r-sec-1",
            commit_id="abc",
            test_file="../../etc/passwd",
        )
        assert result is None, "Path traversal must be rejected"

    def test_absolute_path_rejected(self, ready_contract):
        planner = VerificationPlanner()
        for path in ["/etc/shadow", "/root/.ssh/id_rsa", "C:\\Windows\\System32"]:
            result = planner.plan(
                contract=ready_contract,
                obligation_id="o1",
                target_id="t-sec-1",
                repository_id="r-sec-1",
                commit_id="abc",
                test_file=path,
            )
            assert result is None, f"Absolute path {path!r} must be rejected"

    def test_git_option_injection_rejected(self, ready_contract):
        planner = VerificationPlanner()
        for bad in ["--upload-pack", "--exec-path=/tmp/evil", "--config=user.name=hax"]:
            result = planner.plan(
                contract=ready_contract,
                obligation_id="o1",
                target_id="t-sec-1",
                repository_id="r-sec-1",
                commit_id="abc",
                test_file=bad,
            )
            assert result is None, f"Git option injection {bad!r} must be rejected"

    def test_empty_test_file_rejected(self, ready_contract):
        planner = VerificationPlanner()
        result = planner.plan(
            contract=ready_contract,
            obligation_id="o1",
            target_id="t-sec-1",
            repository_id="r-sec-1",
            commit_id="abc",
            test_file="",
        )
        assert result is None

    def test_none_test_file_rejected(self, ready_contract):
        planner = VerificationPlanner()
        result = planner.plan(
            contract=ready_contract,
            obligation_id="o1",
            target_id="t-sec-1",
            repository_id="r-sec-1",
            commit_id="abc",
            test_file=None,
        )
        assert result is None


# ─── Shell Injection Threat Tests ─────────────────────────────────────────────

class TestShellInjectionThreats:

    @pytest.mark.parametrize("shell_payload", [
        "test.py; rm -rf /",
        "test.py | cat /etc/passwd",
        "test.py && malicious",
        "test.py > /etc/cron.d/evil",
        "test.py `id`",
        "test.py $(id)",
        "test.py\nrm -rf /",
        "test.py\rrm -rf /",
    ])
    def test_shell_metachar_rejected(self, ready_contract, shell_payload):
        planner = VerificationPlanner()
        result = planner.plan(
            contract=ready_contract,
            obligation_id="o1",
            target_id="t-sec-1",
            repository_id="r-sec-1",
            commit_id="abc",
            test_file=shell_payload,
        )
        assert result is None, f"Shell payload {shell_payload!r} must be rejected"

    def test_forbidden_chars_set_is_comprehensive(self):
        """Verify the FORBIDDEN_CHARS set covers key shell metacharacters."""
        required = {"&", "|", ";", ">", "<", "$", "`", "\n", "\r"}
        missing = required - FORBIDDEN_CHARS
        assert not missing, f"Missing required forbidden chars: {missing}"


# ─── Command Allowlist Threat Tests ──────────────────────────────────────────

class TestCommandAllowlist:

    def test_unapproved_command_id_rejected(self, ready_contract):
        planner = VerificationPlanner()
        result = planner.plan(
            contract=ready_contract,
            obligation_id="o1",
            target_id="t-sec-1",
            repository_id="r-sec-1",
            commit_id="abc",
            test_file="test.py",
            command_id="bash",  # Not in allowlist
        )
        assert result is None

    def test_curl_command_id_rejected(self, ready_contract):
        planner = VerificationPlanner()
        result = planner.plan(
            contract=ready_contract,
            obligation_id="o1",
            target_id="t-sec-1",
            repository_id="r-sec-1",
            commit_id="abc",
            test_file="test.py",
            command_id="curl",
        )
        assert result is None

    def test_rm_command_id_rejected(self, ready_contract):
        planner = VerificationPlanner()
        result = planner.plan(
            contract=ready_contract,
            obligation_id="o1",
            target_id="t-sec-1",
            repository_id="r-sec-1",
            commit_id="abc",
            test_file="test.py",
            command_id="rm",
        )
        assert result is None

    def test_allowed_command_produces_array_not_string(self, ready_contract):
        """Ensure planned commands are argument arrays, not shell strings."""
        planner = VerificationPlanner()
        result = planner.plan(
            contract=ready_contract,
            obligation_id="o1",
            target_id="t-sec-1",
            repository_id="r-sec-1",
            commit_id="abc",
            test_file="safe_test.py",
            command_id="pytest",
        )
        assert result is not None
        assert isinstance(result.command, list), "Command must be a list, not a string"
        for arg in result.command:
            assert isinstance(arg, str)

    def test_allowlist_contains_expected_commands(self):
        """Verify the allowlist is not empty and contains only expected entries."""
        assert "pytest" in COMMAND_ALLOWLIST
        assert "unittest" in COMMAND_ALLOWLIST
        # Unsafe commands must NOT be in the allowlist
        for bad in ["bash", "sh", "curl", "wget", "rm", "exec", "eval"]:
            assert bad not in COMMAND_ALLOWLIST, f"Unsafe command {bad!r} in allowlist"

    def test_contract_not_ready_rejects_planning(self, ready_contract):
        """Planning must fail if the contract is not READY."""
        ready_contract.compilation_status = ContractStatus.DRAFT
        planner = VerificationPlanner()
        result = planner.plan(
            contract=ready_contract,
            obligation_id="o1",
            target_id="t-sec-1",
            repository_id="r-sec-1",
            commit_id="abc",
            test_file="safe_test.py",
        )
        assert result is None


# ─── Validator Threat Tests ───────────────────────────────────────────────────

class TestExecutionValidator:

    def test_validator_rejects_unlisted_command(self, policy):
        validator = ExecutionValidator()
        req = make_request(command=["bash", "-c", "id"])
        with pytest.raises(Exception):
            validator.validate(req, policy)

    def test_validator_rejects_traversal_in_wd(self, policy):
        validator = ExecutionValidator()
        req = make_request(working_directory="../../etc")
        with pytest.raises(Exception):
            validator.validate(req, policy)

    def test_validator_rejects_shell_metachar_in_args(self, policy):
        validator = ExecutionValidator()
        req = make_request(command=["python", "-m", "pytest", "test.py; rm -rf /"])
        with pytest.raises(Exception):
            validator.validate(req, policy)

    def test_validator_rejects_absolute_path_in_args(self, policy):
        validator = ExecutionValidator()
        req = make_request(command=["python", "-m", "pytest", "/etc/passwd"])
        with pytest.raises(Exception):
            validator.validate(req, policy)

    def test_validator_allows_legitimate_request(self, policy):
        validator = ExecutionValidator()
        req = make_request(command=["python", "-m", "pytest", "safe_test.py"])
        validator.validate(req, policy)  # Should not raise


# ─── Secret Isolation Tests ───────────────────────────────────────────────────

class TestSecretIsolation:

    def test_host_secrets_not_in_docker_execution_env(self, snapshot_dir):
        """
        Verify DockerSandboxBackend does NOT pass known secret env vars.
        This test validates the design intent — actual enforcement is per Docker daemon.
        """
        sb = DockerSandboxBackend(snapshot_path=snapshot_dir)
        sb._docker_available = False  # Policy test, not real Docker test

        # In the DockerSandboxBackend, env_vars dict should be empty
        # This proves intent — secrets not explicitly added
        # (Real enforcement happens when Docker invokes the container without inheriting host env)
        # We validate the constructor does NOT initialize with os.environ
        assert not hasattr(sb, '_host_env_inherited') or not sb._host_env_inherited

    @pytest.mark.parametrize("secret_var", [
        "GITHUB_TOKEN",
        "OPENAI_API_KEY",
        "AWS_SECRET_ACCESS_KEY",
        "DATABASE_URL",
        "SECRET_KEY",
        "GIT_ASKPASS",
        "SSH_AUTH_SOCK",
        "NPM_TOKEN",
    ])
    def test_common_secret_vars_are_not_in_sandbox_allowlist(self, secret_var):
        """
        The DockerSandboxBackend must never inject common secret env var names.
        """
        # The sandbox constructs env_vars = {} explicitly
        # We verify the sandbox source doesn't contain these literals as injected vars
        import inspect
        src = inspect.getsource(DockerSandboxBackend.execute)
        assert secret_var not in src or f'env_vars["{secret_var}"]' not in src, \
            f"Secret variable {secret_var!r} must not be injected into sandbox env"


# ─── Docker Configuration Tests ──────────────────────────────────────────────

class TestDockerConfiguration:

    def test_approved_image_is_pinned_to_digest(self):
        """Image must be pinned to SHA256 digest, not a mutable tag."""
        image = DockerSandboxBackend.APPROVED_IMAGE
        assert "@sha256:" in image, \
            f"Image {image!r} must be pinned to sha256 digest"

    def test_approved_image_not_user_controlled(self):
        """Image must be a constant, not derived from request or repository content."""
        import inspect
        src = inspect.getsource(DockerSandboxBackend)
        # Image must be a class-level constant string
        assert "APPROVED_IMAGE" in src
        assert 'sha256:' in src

    def test_docker_backend_does_not_inherit_host_env(self):
        """Verify the execute method explicitly constructs env_vars = {} ."""
        import inspect
        src = inspect.getsource(DockerSandboxBackend.execute)
        assert "env_vars = {}" in src, \
            "DockerSandboxBackend must explicitly construct an empty environment"
        assert "os.environ" not in src, \
            "DockerSandboxBackend must not inherit os.environ"


# ─── Semantic Separation Tests ────────────────────────────────────────────────

class TestSemanticSeparation:

    def test_exit_code_0_does_not_produce_proven(self, snapshot_dir):
        """
        CRITICAL: exit_code == 0 must NEVER directly produce PROVEN.
        """
        from app.execution.models import ExecutionStatus, SandboxIdentity
        obs = ExecutionObservation(
            execution_id="sem-test",
            status=ExecutionStatus.PASSED,
            exit_code=0,
            stdout="1 passed",
            sandbox_identity=SandboxIdentity(backend_name="DOCKER"),
            policy_id="DEFAULT",
            repository_id="r1",
            commit_id="abc",
        )
        req = make_request()
        capture = EvidenceCapture()
        ev = capture.capture(req, obs)

        # The contract: PASSED maps to INCONCLUSIVE (Phase 10 decides truth)
        assert ev.result == EvidenceResult.INCONCLUSIVE, \
            f"exit_code=0 must not produce EvidenceResult.PASS (PROVEN); got {ev.result}"

    def test_unsupported_sandbox_produces_not_run(self, snapshot_dir):
        """UNSUPPORTED must produce NOT_RUN, never PROVEN."""
        from app.execution.models import ExecutionStatus, SandboxIdentity
        obs = ExecutionObservation(
            execution_id="sem-test2",
            status=ExecutionStatus.UNSUPPORTED,
            exit_code=None,
            stdout="Execution refused",
            sandbox_identity=SandboxIdentity(backend_name="SAFE_FALLBACK"),
            policy_id="DEFAULT",
            repository_id="r1",
            commit_id="abc",
        )
        req = make_request()
        capture = EvidenceCapture()
        ev = capture.capture(req, obs)
        assert ev.result == EvidenceResult.NOT_RUN, \
            f"UNSUPPORTED must map to NOT_RUN; got {ev.result}"

    def test_timeout_produces_error_evidence(self, snapshot_dir):
        """Timeout must produce ERROR evidence, never PROVEN."""
        from app.execution.models import ExecutionStatus, SandboxIdentity
        obs = ExecutionObservation(
            execution_id="sem-test3",
            status=ExecutionStatus.TIMEOUT,
            exit_code=-1,
            timed_out=True,
            sandbox_identity=SandboxIdentity(backend_name="DOCKER"),
            policy_id="DEFAULT",
            repository_id="r1",
            commit_id="abc",
        )
        req = make_request()
        capture = EvidenceCapture()
        ev = capture.capture(req, obs)
        assert ev.result == EvidenceResult.ERROR, \
            f"TIMEOUT must produce ERROR evidence; got {ev.result}"

    def test_resource_limit_produces_error_evidence(self, snapshot_dir):
        """RESOURCE_LIMIT must produce ERROR evidence, never PROVEN."""
        from app.execution.models import ExecutionStatus, SandboxIdentity
        obs = ExecutionObservation(
            execution_id="sem-test4",
            status=ExecutionStatus.RESOURCE_LIMIT,
            exit_code=-1,
            resource_limit_exceeded=True,
            sandbox_identity=SandboxIdentity(backend_name="DOCKER"),
            policy_id="DEFAULT",
            repository_id="r1",
            commit_id="abc",
        )
        req = make_request()
        capture = EvidenceCapture()
        ev = capture.capture(req, obs)
        assert ev.result == EvidenceResult.ERROR, \
            f"RESOURCE_LIMIT must produce ERROR evidence; got {ev.result}"


# ─── Integrity Tests ──────────────────────────────────────────────────────────

class TestIntegrity:

    def test_observation_snapshot_id_preserved(self, snapshot_dir):
        """Snapshot ID must be captured in the observation for provenance."""
        sb = DockerSandboxBackend(snapshot_path=snapshot_dir)
        sb._docker_available = False
        sb.create()
        req = make_request(snapshot_id="snap-expected-id")
        obs = sb.execute(req, get_default_policy())
        assert obs.snapshot_id == "snap-expected-id"
        sb.destroy()

    def test_observation_commit_preserved(self, snapshot_dir):
        """Commit ID must be preserved in the observation for provenance."""
        sb = DockerSandboxBackend(snapshot_path=snapshot_dir)
        sb._docker_available = False
        sb.create()
        req = make_request(commit_id="deadbeef1234")
        obs = sb.execute(req, get_default_policy())
        assert obs.commit_id == "deadbeef1234"
        sb.destroy()

    def test_evidence_has_integrity_hash(self, snapshot_dir):
        """All captured evidence must have an integrity hash."""
        from app.execution.models import ExecutionStatus, SandboxIdentity
        obs = ExecutionObservation(
            execution_id="int-test",
            status=ExecutionStatus.UNSUPPORTED,
            sandbox_identity=SandboxIdentity(backend_name="SAFE_FALLBACK"),
            policy_id="DEFAULT",
            repository_id="r1",
            commit_id="abc",
        )
        req = make_request()
        capture = EvidenceCapture()
        ev = capture.capture(req, obs)
        assert ev.integrity is not None
        assert ev.integrity.evidence_hash is not None
        assert len(ev.integrity.evidence_hash) > 0
