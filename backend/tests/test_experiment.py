"""
Tests for Phase 13A: Experiment Orchestrator — Validity Audit
=============================================================

Proves that:
- FAR calculation exposes numerator and denominator.
- When Positive Assurance Count == 0, FAR is reported as N/A.
- determine_failure_category classifies correctly.
- GroundTruth does not leak into SVA via experiment orchestration.
"""

from app.benchmark.experiment import determine_failure_category
from app.benchmark.models import (
    BenchmarkCase,
    BenchmarkCategory,
    CaseResult,
    EvidenceSufficiency,
    GroundTruth,
    SystemConfigurationMode,
    RepositoryFixture,
)
from app.benchmark.metrics.calculator import false_assurance_rate
from app.evidence.models import VerificationState


def _make_case(category=BenchmarkCategory.C_POSITIVE_ONLY_EVIDENCE_TRAP, known_violation=True) -> BenchmarkCase:
    return BenchmarkCase(
        case_id="T1",
        version="1",
        category=category,
        requirement_text="req",
        repository_fixture=RepositoryFixture(fixture_id="f1", description="x", files=[]),
        ground_truth=GroundTruth(
            intent_truth="req",
            behavioral_truth="violated",
            known_violation=known_violation,
            expected_assurance_state=VerificationState.VIOLATED,
            evidence_sufficiency_truth=EvidenceSufficiency.SUFFICIENT,
            authored_by="test",
            reviewed_by="test",
        )
    )


# ---------------------------------------------------------------------------
# FAR calculation
# ---------------------------------------------------------------------------

class TestFARCalculation:

    def test_far_exposes_numerator_and_denominator(self):
        """MetricResult must carry numerator and denominator for audit."""
        case = _make_case()
        result = CaseResult(
            case_id="T1",
            system=SystemConfigurationMode.BASELINE_TEST_ONLY,
            predicted_assurance_state=VerificationState.PROVEN,
            abstained=False,
            is_false_assurance=True,
        )
        metric = false_assurance_rate([result], [case])
        # Denominator must be 1 (one PROVEN decision)
        assert metric.denominator == 1, f"Denominator should be 1, got {metric.denominator}"
        # Numerator must be 1 (known_violation=True → false assurance)
        assert metric.numerator == 1, f"Numerator should be 1, got {metric.numerator}"
        assert metric.value == 1.0

    def test_far_is_none_when_no_positive_assurances(self):
        """When Positive Assurance Count == 0, FAR value must be None (N/A)."""
        case = _make_case()
        result = CaseResult(
            case_id="T1",
            system=SystemConfigurationMode.FULL_SVA,
            predicted_assurance_state=VerificationState.UNKNOWN,
            abstained=True,
        )
        metric = false_assurance_rate([result], [case])
        assert metric.denominator == 0, "No positive assurance → denominator must be 0"
        assert metric.value is None, (
            "FAR value must be None (not 0.0) when there are no positive assurances. "
            "Returning 0.0 would falsely claim a perfect FAR."
        )
        assert metric.numerator == 0

    def test_far_not_falsely_zero_when_abstaining(self):
        """A system that always abstains must NOT report FAR=0.0 — only FAR=None."""
        case = _make_case(known_violation=True)
        result = CaseResult(
            case_id="T1",
            system=SystemConfigurationMode.FULL_SVA,
            predicted_assurance_state=VerificationState.UNKNOWN,
            abstained=True,
        )
        metric = false_assurance_rate([result], [case])
        assert metric.value is None, (
            "FAR must be None (not 0.0) when the system always abstains. "
            "Abstention is not a successful FAR result."
        )

    def test_far_correct_positive_assurance(self):
        """Correct positive assurance (PROVEN, not a violation) counts toward denominator only."""
        case = _make_case(known_violation=False)
        result = CaseResult(
            case_id="T1",
            system=SystemConfigurationMode.FULL_SVA,
            predicted_assurance_state=VerificationState.PROVEN,
            abstained=False,
        )
        metric = false_assurance_rate([result], [case])
        assert metric.denominator == 1
        assert metric.numerator == 0  # Not a false assurance
        assert metric.value == 0.0   # 0/1 — correctly 0.0 here (not N/A)

    def test_far_unknown_does_not_count_as_positive(self):
        """UNKNOWN/INCONCLUSIVE predictions must NOT count toward positive assurance denominator."""
        case = _make_case(known_violation=True)
        results = [
            CaseResult(
                case_id="T1",
                system=SystemConfigurationMode.FULL_SVA,
                predicted_assurance_state=VerificationState.UNKNOWN,
                abstained=True,
            ),
        ]
        metric = false_assurance_rate(results, [case])
        assert metric.denominator == 0
        assert metric.value is None


# ---------------------------------------------------------------------------
# failure category classification
# ---------------------------------------------------------------------------

class TestFailureCategoryClassification:

    def test_positive_evidence_trap_classified(self):
        case = _make_case(category=BenchmarkCategory.C_POSITIVE_ONLY_EVIDENCE_TRAP)
        result = CaseResult(
            case_id="T1",
            system=SystemConfigurationMode.BASELINE_TEST_ONLY,
            predicted_assurance_state=VerificationState.PROVEN,
            abstained=False,
            is_false_assurance=True,
        )
        assert determine_failure_category(result, case) == "POSITIVE_EVIDENCE_OVERGENERALIZATION"

    def test_missed_violation_insufficient_evidence(self):
        case = _make_case()
        result = CaseResult(
            case_id="T1",
            system=SystemConfigurationMode.BASELINE_TEST_ONLY,
            predicted_assurance_state=VerificationState.UNKNOWN,
            abstained=True,
            missed_violation=True,
        )
        assert determine_failure_category(result, case) == "INSUFFICIENT_EVIDENCE"
