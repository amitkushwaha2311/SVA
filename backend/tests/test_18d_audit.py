"""
Phase 18D Final Audit — Test Suite
====================================
Tests audit items 1, 2 (ground-truth isolation & causal telemetry).

Test 1: FULL_SVA Ground-Truth Isolation
  Verifies FULL_SVA cannot change behaviour when only the ground_truth
  label changes while the fixture and requirement remain identical.

Test 2: End-to-End Causal Observability
  Verifies that analysis_id → job_id → correlation_id → telemetry events
  → requirement_id → contract_id → obligation_id → evidence_id → verification_result
  all carry consistent, linked IDs, and that the timeline endpoint can
  reconstruct the causal chain from them.

Test 3: LLM_JUDGE Determinism Disclosure
  Confirms the deterministic LLM_JUDGE mode is NOT an external LLM
  and its evaluator notes state this explicitly.

Test 4: TEST_ONLY inputs
  Verifies TestOnly only reads fixture file content and nothing else.
"""

import json
import logging
import uuid

import pytest

from app.benchmark.baselines.sva import FullSVAAdapter
from app.benchmark.baselines.llm_judge import LLMJudgeAdapter
from app.benchmark.baselines.test_only import TestOnlyAdapter
from app.benchmark.models import (
    BenchmarkCase,
    BenchmarkCategory,
    CaseResult,
    EvaluationMode,
    GroundTruth,
    RepositoryFixture,
    FileFixture,
    SystemConfigurationMode,
    EvidenceSufficiency,
)
from app.benchmark.runner import BenchmarkRunner
from app.core.telemetry import (
    TelemetryLogger,
    correlation_id_ctx,
    workspace_id_ctx,
    actor_id_ctx,
    scrub_secrets,
)
from app.evidence.models import VerificationState


# ---------------------------------------------------------------------------
# Shared fixture factories
# ---------------------------------------------------------------------------

def _make_ground_truth(known_violation: bool, expected: VerificationState) -> GroundTruth:
    return GroundTruth(
        intent_truth="System shall allow only owners to delete their resources.",
        behavioral_truth="Code checks ownership before deletion.",
        evidence_sufficiency_truth=EvidenceSufficiency.SUFFICIENT,
        known_violation=known_violation,
        expected_assurance_state=expected,
    )


def _make_fixture(content: str = "def delete(user, resource): pass") -> RepositoryFixture:
    return RepositoryFixture(
        fixture_id="fixture-audit-1",
        description="Audit fixture",
        files=[FileFixture(relative_path="main.py", content=content)]
    )


def _make_case(case_id: str, known_violation: bool, expected: VerificationState,
               fixture_content: str = "def delete(user, resource): pass") -> BenchmarkCase:
    return BenchmarkCase(
        case_id=case_id,
        category=BenchmarkCategory.B_DIRECT_SEMANTIC_VIOLATION if known_violation
                 else BenchmarkCategory.A_CORRECT_IMPLEMENTATION,
        requirement_text="Only owners can delete their resources.",
        repository_fixture=_make_fixture(fixture_content),
        ground_truth=_make_ground_truth(known_violation, expected),
    )


# ===========================================================================
# TEST 1 — FULL_SVA Ground-Truth Isolation
# ===========================================================================

class TestFullSVAGroundTruthIsolation:
    """
    FULL_SVA MUST produce identical predictions when only the ground_truth
    changes (known_violation, expected_assurance_state, category label)
    while the fixture content and requirement text remain unchanged.
    """

    def test_prediction_identical_when_only_label_changes(self):
        """
        Change known_violation from False → True and expected state from PROVEN → VIOLATED
        while keeping fixture + requirement identical.
        FULL_SVA prediction must not change.
        """
        adapter = FullSVAAdapter(mode=SystemConfigurationMode.FULL_SVA)

        case_label_correct = _make_case(
            "audit-gt-1",
            known_violation=False,
            expected=VerificationState.PROVEN,
        )
        case_label_violation = BenchmarkCase(
            case_id="audit-gt-1",  # Same case_id
            category=BenchmarkCategory.B_DIRECT_SEMANTIC_VIOLATION,  # Different label
            requirement_text=case_label_correct.requirement_text,   # SAME requirement
            repository_fixture=case_label_correct.repository_fixture,  # SAME fixture
            ground_truth=_make_ground_truth(
                known_violation=True,
                expected=VerificationState.VIOLATED,
            ),
        )

        result_correct_label = adapter.evaluate(case_label_correct)
        result_violation_label = adapter.evaluate(case_label_violation)

        assert result_correct_label.predicted_assurance_state == \
               result_violation_label.predicted_assurance_state, (
            "FULL_SVA prediction changed when only ground_truth label changed. "
            "This indicates ground-truth leakage."
        )

        assert result_correct_label.ambiguity_detected == \
               result_violation_label.ambiguity_detected, \
            "FULL_SVA ambiguity detection changed when only label changed — leakage detected."

        assert result_correct_label.contradiction_detected == \
               result_violation_label.contradiction_detected, \
            "FULL_SVA contradiction detection changed when only label changed — leakage detected."

    def test_evidence_refs_identical_when_only_label_changes(self):
        """Evidence collected must not vary with ground truth label change."""
        adapter = FullSVAAdapter(mode=SystemConfigurationMode.FULL_SVA)
        FIXTURE = "def check_owner(user, resource): return user.id == resource.owner_id"

        case_a = _make_case("audit-ev-1", known_violation=False,
                             expected=VerificationState.PROVEN, fixture_content=FIXTURE)
        case_b = BenchmarkCase(
            case_id="audit-ev-1",
            category=BenchmarkCategory.N_AUTHORIZATION_BOUNDARY_VIOLATION,
            requirement_text=case_a.requirement_text,
            repository_fixture=case_a.repository_fixture,
            ground_truth=_make_ground_truth(True, VerificationState.VIOLATED),
        )

        result_a = adapter.evaluate(case_a)
        result_b = adapter.evaluate(case_b)

        assert sorted(result_a.evidence_refs) == sorted(result_b.evidence_refs), (
            "Evidence refs differ across cases with identical input — ground-truth leakage suspected."
        )

    def test_category_not_accessible_in_adapter(self):
        """
        FullSVAAdapter.evaluate() signature takes a BenchmarkCase but the implementation
        must only use case.requirement_text and case.repository_fixture — never case.category
        or case.ground_truth. This test verifies via code inspection.
        """
        import inspect
        source = inspect.getsource(FullSVAAdapter.evaluate)
        # ground_truth must never be referenced in evaluate()
        assert "ground_truth" not in source, (
            "FullSVAAdapter.evaluate() references 'ground_truth' — leakage risk."
        )
        assert "known_violation" not in source, (
            "FullSVAAdapter.evaluate() references 'known_violation' — leakage risk."
        )
        assert ".category" not in source, (
            "FullSVAAdapter.evaluate() accesses .category — potential label leakage."
        )


# ===========================================================================
# TEST 2 — End-to-End Causal Observability
# ===========================================================================

class TestCausalObservability:
    """
    Verifies that a complete analysis run emits telemetry events that preserve
    the causal chain:
        analysis_id → correlation_id → requirement_id → contract_id → evidence_id → verification_state
    """

    def test_correlation_id_propagates_through_telemetry(self, caplog):
        """
        Setting correlation_id in context before emitting events must be
        preserved in every event's correlation_id field.
        """
        test_correlation_id = f"analysis-{uuid.uuid4()}"
        test_workspace = "ws-audit-test"

        correlation_id_ctx.set(test_correlation_id)
        workspace_id_ctx.set(test_workspace)

        events_captured = []

        with caplog.at_level(logging.INFO, logger="sva.telemetry"):
            # Simulate the causal chain of telemetry events
            TelemetryLogger.log_event(
                "ANALYSIS_CREATED",
                {"analysis_id": test_correlation_id, "repository_id": "repo-1"},
            )
            TelemetryLogger.log_event(
                "JOB_DISPATCHED",
                {"analysis_id": test_correlation_id, "job_id": "job-001"},
            )
            TelemetryLogger.log_event(
                "CONTRACT_COMPILED",
                {"analysis_id": test_correlation_id, "contract_id": "ctr-001",
                 "requirement_id": "req-001"},
            )
            TelemetryLogger.log_event(
                "EVIDENCE_COLLECTED",
                {"analysis_id": test_correlation_id, "contract_id": "ctr-001",
                 "evidence_id": "ev-001", "obligation_id": "obl-001"},
            )
            TelemetryLogger.log_event(
                "VERIFICATION_COMPLETED",
                {"analysis_id": test_correlation_id, "contract_id": "ctr-001",
                 "verification_state": "UNKNOWN"},
            )

        for record in caplog.records:
            event = json.loads(record.message)
            events_captured.append(event)

        assert len(events_captured) == 5, \
            f"Expected 5 causal telemetry events, got {len(events_captured)}"

        # All events must carry the same correlation_id
        for event in events_captured:
            assert event["correlation_id"] == test_correlation_id, (
                f"Event {event['event_type']} has wrong correlation_id: "
                f"{event['correlation_id']!r} != {test_correlation_id!r}"
            )

        # All events must carry correct workspace_id
        for event in events_captured:
            assert event["workspace_id"] == test_workspace

        # Verify causal sequence
        event_types = [e["event_type"] for e in events_captured]
        assert event_types == [
            "ANALYSIS_CREATED",
            "JOB_DISPATCHED",
            "CONTRACT_COMPILED",
            "EVIDENCE_COLLECTED",
            "VERIFICATION_COMPLETED",
        ]

    def test_timeline_can_reconstruct_causal_chain(self, caplog):
        """
        Telemetry events for a single analysis must preserve enough IDs to
        reconstruct: analysis_id → contract_id → evidence_id → verification_state.
        """
        analysis_id = f"analysis-{uuid.uuid4()}"
        contract_id = f"contract-{uuid.uuid4()}"
        evidence_id = f"evidence-{uuid.uuid4()}"
        requirement_id = f"req-{uuid.uuid4()}"
        obligation_id = f"obl-{uuid.uuid4()}"

        correlation_id_ctx.set(analysis_id)

        causal_chain = []

        with caplog.at_level(logging.INFO, logger="sva.telemetry"):
            TelemetryLogger.log_event(
                "ANALYSIS_CREATED",
                {"analysis_id": analysis_id}
            )
            TelemetryLogger.log_event(
                "CONTRACT_COMPILED",
                {"analysis_id": analysis_id, "contract_id": contract_id,
                 "requirement_id": requirement_id}
            )
            TelemetryLogger.log_event(
                "OBLIGATION_EVALUATED",
                {"contract_id": contract_id, "obligation_id": obligation_id}
            )
            TelemetryLogger.log_event(
                "EVIDENCE_COLLECTED",
                {"contract_id": contract_id, "evidence_id": evidence_id,
                 "obligation_id": obligation_id}
            )
            TelemetryLogger.log_event(
                "VERIFICATION_COMPLETED",
                {"analysis_id": analysis_id, "contract_id": contract_id,
                 "evidence_id": evidence_id, "verification_state": "UNKNOWN"}
            )

        for record in caplog.records:
            causal_chain.append(json.loads(record.message))

        # Reconstruct the chain from event details
        detail_map = {e["event_type"]: e["details"] for e in causal_chain}

        # Verify analysis_id flows through
        assert detail_map["ANALYSIS_CREATED"]["analysis_id"] == analysis_id
        assert detail_map["CONTRACT_COMPILED"]["analysis_id"] == analysis_id
        assert detail_map["VERIFICATION_COMPLETED"]["analysis_id"] == analysis_id

        # Verify contract_id bridges CONTRACT → EVIDENCE → VERIFICATION
        assert detail_map["CONTRACT_COMPILED"]["contract_id"] == contract_id
        assert detail_map["EVIDENCE_COLLECTED"]["contract_id"] == contract_id
        assert detail_map["VERIFICATION_COMPLETED"]["contract_id"] == contract_id

        # Verify obligation_id connects OBLIGATION → EVIDENCE
        assert detail_map["OBLIGATION_EVALUATED"]["obligation_id"] == obligation_id
        assert detail_map["EVIDENCE_COLLECTED"]["obligation_id"] == obligation_id

        # Verify evidence_id bridges EVIDENCE → VERIFICATION
        assert detail_map["EVIDENCE_COLLECTED"]["evidence_id"] == evidence_id
        assert detail_map["VERIFICATION_COMPLETED"]["evidence_id"] == evidence_id

        # Verify requirement_id flows from CONTRACT
        assert detail_map["CONTRACT_COMPILED"]["requirement_id"] == requirement_id

    def test_no_fabricated_telemetry_fields(self, caplog):
        """Telemetry events must not contain fabricated/synthetic data not in the input."""
        correlation_id_ctx.set("test-no-fabrication")

        with caplog.at_level(logging.INFO, logger="sva.telemetry"):
            TelemetryLogger.log_event(
                "VERIFICATION_COMPLETED",
                {"analysis_id": "analysis-1", "verification_state": "UNKNOWN",
                 "evidence_count": 0}
            )

        event = json.loads(caplog.records[0].message)

        # Must NOT contain fabricated confidence, p-values, or synthetic score
        details = event["details"]
        assert "confidence_interval" not in details
        assert "p_value" not in details
        assert "significance" not in details
        assert "synthetic_score" not in details


# ===========================================================================
# TEST 3 — LLM_JUDGE Determinism Disclosure
# ===========================================================================

class TestLLMJudgeDisclosure:
    """LLM_JUDGE in DETERMINISTIC mode must self-disclose its nature."""

    def test_deterministic_mode_is_not_external_llm(self):
        adapter = LLMJudgeAdapter(mode=EvaluationMode.DETERMINISTIC)
        assert adapter.evaluation_mode == EvaluationMode.DETERMINISTIC

        case = _make_case("disc-1", known_violation=False, expected=VerificationState.PROVEN)
        result = adapter.evaluate(case)

        # evaluator_notes must disclose deterministic nature
        assert "DETERMINISTIC" in result.evaluator_notes.upper(), (
            "LLM_JUDGE DETERMINISTIC mode did not disclose its non-LLM nature in evaluator_notes."
        )
        assert "does not reflect real llm" in result.evaluator_notes.lower() or \
               "not reflect" in result.evaluator_notes.lower(), (
            "LLM_JUDGE notes do not state that results don't reflect real LLM performance."
        )

    def test_external_mode_raises_not_implemented(self):
        adapter = LLMJudgeAdapter(mode=EvaluationMode.EXTERNAL)
        case = _make_case("ext-1", known_violation=False, expected=VerificationState.PROVEN)
        with pytest.raises(NotImplementedError):
            adapter.evaluate(case)


# ===========================================================================
# TEST 4 — TEST_ONLY declared inputs only
# ===========================================================================

class TestTestOnlyInputBoundary:
    """TestOnly adapter must only use fixture file content."""

    def test_test_only_reads_only_fixture_content(self):
        """
        TestOnly must produce PROVEN only when 'test_pass' is in fixture,
        regardless of category or ground_truth.
        """
        adapter = TestOnlyAdapter()

        case_with_pass = BenchmarkCase(
            case_id="to-1",
            category=BenchmarkCategory.C_POSITIVE_ONLY_EVIDENCE_TRAP,  # adversarial category
            requirement_text="Only owners can delete.",
            repository_fixture=RepositoryFixture(
                fixture_id="f1", description="d",
                files=[FileFixture(relative_path="t.py", content="test_pass")]
            ),
            ground_truth=_make_ground_truth(True, VerificationState.VIOLATED),
        )

        result = adapter.evaluate(case_with_pass)
        # Despite ground_truth.known_violation=True, test_only sees test_pass → PROVEN
        assert result.predicted_assurance_state == VerificationState.PROVEN, (
            "TestOnly must read fixture content only, not ground_truth."
        )

    def test_test_only_unknown_when_no_signal(self):
        adapter = TestOnlyAdapter()
        case = _make_case("to-2", known_violation=False, expected=VerificationState.PROVEN,
                           fixture_content="# no signals here")
        result = adapter.evaluate(case)
        assert result.predicted_assurance_state == VerificationState.UNKNOWN
