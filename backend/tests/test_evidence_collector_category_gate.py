"""
Focused tests: EvidenceCollector dynamic-execution category gate.

Verifies that:
1. BEHAVIOR, FUNCTION, and METHOD targets reach the sandbox execution path
   (planner.plan is called, backend.execute is called when plan succeeds).
2. Categories that should NOT reach the execution path (API_ENDPOINT,
   DATABASE_OPERATION, USER_FLOW, POLICY) are correctly skipped.
3. The planner's own guard safely rejects BEHAVIOR/FUNCTION/METHOD targets
   whose code_entity_ref is None — no AttributeError, no unsafe execution.
4. A BEHAVIOR target with a valid code_entity_ref produces a DETERMINISTIC_TEST
   evidence item (even when sandbox returns UNSUPPORTED).

All sandbox calls are mocked. No Docker daemon required.
"""

import pytest
from unittest.mock import MagicMock, patch, call

from app.contracts.models import (
    BehaviorExpectation,
    ContractStatus,
    SemanticContract,
    VerificationTarget,
    VerificationTargetCategory,
)
from app.contracts.ids import generate_contract_id
from app.evidence.collectors import EvidenceCollector
from app.evidence.models import EvidenceType
from app.execution.models import (
    ExecutionObservation,
    ExecutionStatus,
    SandboxIdentity,
)
from app.execution.policy import get_default_policy


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _make_contract(
    category: VerificationTargetCategory,
    code_entity_ref: str | None = "tests/test_delete.py",
    target_id: str = "tgt-exec-1",
) -> SemanticContract:
    cid = generate_contract_id("repo-test", "req-test")
    beh = BehaviorExpectation(
        behavior_id="beh-1",
        description="Every delete of project must verify authorization before proceeding.",
        action="delete",
        resource="project",
    )
    target = VerificationTarget(
        target_id=target_id,
        category=category,
        description="Target for dynamic execution",
        code_entity_ref=code_entity_ref,
    )
    return SemanticContract(
        contract_id=cid,
        requirement_id="req-test",
        candidate_id="cand-test",
        analysis_id="analysis-test",
        statement="Only project owners can delete projects.",
        compilation_status=ContractStatus.READY,
        allowed_behaviors=[beh],
        verification_targets=[target],
    )


def _unsupported_obs(execution_id: str) -> ExecutionObservation:
    """Mimics what DockerSandboxBackend returns when image is absent or UNSUPPORTED."""
    return ExecutionObservation(
        execution_id=execution_id,
        status=ExecutionStatus.UNSUPPORTED,
        exit_code=None,
        stdout="Execution refused: Approved execution image unavailable",
        stderr="Safe fallback engaged. Returning UNSUPPORTED.",
        sandbox_identity=SandboxIdentity(backend_name="DOCKER"),
        policy_id="DEFAULT_POLICY",
        repository_id="repo-test",
        commit_id="HEAD",
        snapshot_id="snap-test",
    )


class EmptyScan:
    files = []
    total_files = 0
    total_lines = 0
    scan_duration_ms = 0
    skipped_files = []


# ──────────────────────────────────────────────────────────────
# 1. Executable categories reach the sandbox path
# ──────────────────────────────────────────────────────────────

class TestExecutableCategoriesReachSandbox:
    """
    For each executable category, verify that planner.plan() is invoked and —
    when the plan succeeds — backend.execute() is also invoked.
    """

    @pytest.mark.parametrize("category", [
        VerificationTargetCategory.BEHAVIOR,
        VerificationTargetCategory.FUNCTION,
        VerificationTargetCategory.METHOD,
    ])
    def test_category_reaches_planner(self, category, tmp_path):
        contract = _make_contract(category, code_entity_ref="tests/test_auth.py")
        collector = EvidenceCollector()

        mock_backend = MagicMock()
        mock_backend._docker_available = True

        # Plan returns a valid request (we let the real planner decide)
        # but we intercept execute() so no container is launched.
        mock_execute_obs = _unsupported_obs("exec-1")
        mock_backend.execute.return_value = mock_execute_obs
        collector.sandbox_backend = mock_backend

        # Also mock the planner so we can assert it was called
        with patch.object(collector.planner, "plan", wraps=collector.planner.plan) as mock_plan:
            collector.collect(
                repository_id="repo-test",
                analysis_id="analysis-test",
                scan_result=EmptyScan(),
                contracts=[contract],
                commit_id="HEAD",
                snapshot_path=str(tmp_path),
                snapshot_id="snap-test",
            )

        mock_plan.assert_called_once()
        _, kwargs = mock_plan.call_args
        assert kwargs["test_file"] == "tests/test_auth.py", (
            f"planner received wrong test_file for category {category.name}"
        )

    @pytest.mark.parametrize("category", [
        VerificationTargetCategory.BEHAVIOR,
        VerificationTargetCategory.FUNCTION,
        VerificationTargetCategory.METHOD,
    ])
    def test_category_reaches_backend_execute_when_plan_succeeds(self, category, tmp_path):
        contract = _make_contract(category, code_entity_ref="tests/test_auth.py")
        collector = EvidenceCollector()

        mock_backend = MagicMock()
        mock_backend.execute.return_value = _unsupported_obs("exec-2")
        collector.sandbox_backend = mock_backend

        collector.collect(
            repository_id="repo-test",
            analysis_id="analysis-test",
            scan_result=EmptyScan(),
            contracts=[contract],
            commit_id="HEAD",
            snapshot_path=str(tmp_path),
            snapshot_id="snap-test",
        )

        mock_backend.create.assert_called_once()
        mock_backend.execute.assert_called_once()
        mock_backend.destroy.assert_called_once()


# ──────────────────────────────────────────────────────────────
# 2. Non-executable categories are skipped
# ──────────────────────────────────────────────────────────────

class TestNonExecutableCategoriesAreSkipped:
    """
    API_ENDPOINT, DATABASE_OPERATION, USER_FLOW, POLICY must NOT trigger
    backend.execute() — they require network or integration environments.
    """

    @pytest.mark.parametrize("category", [
        VerificationTargetCategory.API_ENDPOINT,
        VerificationTargetCategory.DATABASE_OPERATION,
        VerificationTargetCategory.USER_FLOW,
        VerificationTargetCategory.POLICY,
    ])
    def test_category_does_not_reach_sandbox(self, category, tmp_path):
        contract = _make_contract(category, code_entity_ref="tests/test_api.py")
        collector = EvidenceCollector()

        mock_backend = MagicMock()
        collector.sandbox_backend = mock_backend

        collector.collect(
            repository_id="repo-test",
            analysis_id="analysis-test",
            scan_result=EmptyScan(),
            contracts=[contract],
            commit_id="HEAD",
            snapshot_path=str(tmp_path),
            snapshot_id="snap-test",
        )

        mock_backend.execute.assert_not_called()
        mock_backend.create.assert_not_called()


# ──────────────────────────────────────────────────────────────
# 3. None code_entity_ref → planner rejects → no execute
# ──────────────────────────────────────────────────────────────

class TestNoneCodeEntityRefIsSafe:
    """
    When code_entity_ref is None, planner.plan() returns None (its own guard:
    `if not test_file: return None`).  backend.execute must NOT be called.
    No AttributeError should be raised.
    """

    @pytest.mark.parametrize("category", [
        VerificationTargetCategory.BEHAVIOR,
        VerificationTargetCategory.FUNCTION,
        VerificationTargetCategory.METHOD,
    ])
    def test_no_execute_when_code_entity_ref_is_none(self, category, tmp_path):
        contract = _make_contract(category, code_entity_ref=None)
        collector = EvidenceCollector()

        mock_backend = MagicMock()
        collector.sandbox_backend = mock_backend

        # Must not raise; must not call execute
        result = collector.collect(
            repository_id="repo-test",
            analysis_id="analysis-test",
            scan_result=EmptyScan(),
            contracts=[contract],
            commit_id="HEAD",
            snapshot_path=str(tmp_path),
            snapshot_id="snap-test",
        )

        mock_backend.execute.assert_not_called()
        # Evidence list may be empty or contain only static items — never errors
        assert isinstance(result, list)


# ──────────────────────────────────────────────────────────────
# 4. BEHAVIOR target with valid ref → DETERMINISTIC_TEST evidence
# ──────────────────────────────────────────────────────────────

class TestBehaviorTargetProducesDynamicEvidence:
    """
    End-to-end: a BEHAVIOR target with a valid code_entity_ref should
    produce at least one DETERMINISTIC_TEST evidence item, even if the
    sandbox returns UNSUPPORTED (e.g. image absent, Windows host, etc.).
    """

    def test_behavior_produces_deterministic_test_evidence(self, tmp_path):
        contract = _make_contract(
            VerificationTargetCategory.BEHAVIOR,
            code_entity_ref="tests/test_delete.py",
        )
        collector = EvidenceCollector()

        mock_backend = MagicMock()
        # Simulate sandbox UNSUPPORTED (stale image / no docker) — still produces evidence
        mock_backend.execute.return_value = _unsupported_obs("exec-behavior-1")
        collector.sandbox_backend = mock_backend

        evidence_items = collector.collect(
            repository_id="repo-test",
            analysis_id="analysis-test",
            scan_result=EmptyScan(),
            contracts=[contract],
            commit_id="HEAD",
            snapshot_path=str(tmp_path),
            snapshot_id="snap-test",
        )

        dynamic_evs = [
            ev for ev in evidence_items
            if ev.evidence_type == EvidenceType.DETERMINISTIC_TEST
        ]
        assert len(dynamic_evs) >= 1, (
            "Expected at least one DETERMINISTIC_TEST evidence item for a BEHAVIOR "
            f"target with code_entity_ref set. Got evidence types: "
            f"{[ev.evidence_type for ev in evidence_items]}"
        )
        ev = dynamic_evs[0]
        assert ev.target_refs == ["tgt-exec-1"]
        assert ev.contract_id == contract.contract_id

    def test_behavior_evidence_result_is_not_run_on_unsupported(self, tmp_path):
        """UNSUPPORTED observation → EvidenceResult.NOT_RUN (per EvidenceCapture rules)."""
        from app.evidence.models import EvidenceResult

        contract = _make_contract(
            VerificationTargetCategory.BEHAVIOR,
            code_entity_ref="tests/test_delete.py",
        )
        collector = EvidenceCollector()

        mock_backend = MagicMock()
        mock_backend.execute.return_value = _unsupported_obs("exec-behavior-2")
        collector.sandbox_backend = mock_backend

        evidence_items = collector.collect(
            repository_id="repo-test",
            analysis_id="analysis-test",
            scan_result=EmptyScan(),
            contracts=[contract],
            commit_id="HEAD",
            snapshot_path=str(tmp_path),
            snapshot_id="snap-test",
        )

        dynamic_evs = [
            ev for ev in evidence_items
            if ev.evidence_type == EvidenceType.DETERMINISTIC_TEST
        ]
        assert dynamic_evs, "No dynamic evidence produced"
        assert dynamic_evs[0].result == EvidenceResult.NOT_RUN, (
            f"Expected NOT_RUN for UNSUPPORTED observation, got {dynamic_evs[0].result}"
        )
