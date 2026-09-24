"""
Tests: Metrics Calculator
==========================
Tests all metric formulas with controlled inputs.
Verifies UNKNOWN / INCONCLUSIVE / abstention handling.
Verifies anti-gaming: always-UNKNOWN systems don't score well.
"""

import pytest

from app.benchmark.metrics.calculator import (
    MetricsCalculator,
    false_assurance_rate,
    violation_recall,
    violation_precision,
    correct_positive_assurance_rate,
    ambiguity_recall,
    contradiction_recall,
    phantom_requirement_rate,
    stale_evidence_detection_rate,
    counterexample_discovery_rate,
    appropriate_uncertainty_rate,
    _POSITIVE_ASSURANCE_STATES,
    _VIOLATION_STATES,
    _UNCERTAIN_STATES,
)
from app.benchmark.models import (
    BenchmarkCase,
    BenchmarkCategory,
    CaseDifficulty,
    CaseResult,
    EvidenceSufficiency,
    FileFixture,
    GroundTruth,
    RepositoryFixture,
    SystemConfigurationMode,
)
from app.evidence.models import VerificationState
from app.drift.models import SemanticCIDecision


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_case(case_id: str, category: BenchmarkCategory, known_violation: bool,
               has_ambiguity: bool = False, has_contradiction: bool = False,
               expected_state: VerificationState = None) -> BenchmarkCase:
    if expected_state is None:
        expected_state = VerificationState.VIOLATED if known_violation else VerificationState.PROVEN
    ambig_interps = ["A", "B"] if has_ambiguity else []
    contradiction_pair = ["X", "Y"] if has_contradiction else []
    return BenchmarkCase(
        case_id=case_id,
        version="1",
        category=category,
        requirement_text=f"req for {case_id}",
        repository_fixture=RepositoryFixture(
            fixture_id=f"fix_{case_id}",
            description="test",
            files=[FileFixture(relative_path="a.py", content="pass")],
        ),
        ground_truth=GroundTruth(
            intent_truth="intent",
            behavioral_truth="behavior",
            has_ambiguity=has_ambiguity,
            ambiguity_interpretations=ambig_interps,
            has_contradiction=has_contradiction,
            contradiction_pair=contradiction_pair,
            known_violation=known_violation,
            evidence_sufficiency_truth=EvidenceSufficiency.SUFFICIENT,
            expected_assurance_state=expected_state,
            authored_by="manual_review",
            reviewed_by="manual_review",
        ),
    )


def _make_result(case_id: str, state: VerificationState,
                 ambiguity: bool = False, contradiction: bool = False,
                 ce_refs: list[str] | None = None,
                 ci_action: SemanticCIDecision | None = None) -> CaseResult:
    return CaseResult(
        case_id=case_id,
        system=SystemConfigurationMode.FULL_SVA,
        predicted_assurance_state=state,
        abstained=(state in _UNCERTAIN_STATES),
        ambiguity_detected=ambiguity,
        contradiction_detected=contradiction,
        counterexample_refs=ce_refs or [],
        predicted_ci_action=ci_action,
    )


# ---------------------------------------------------------------------------
# FAR Tests
# ---------------------------------------------------------------------------

class TestFalseAssuranceRate:

    def test_far_zero_on_no_false_assurances(self):
        cases = [_make_case("C1", BenchmarkCategory.A_CORRECT_IMPLEMENTATION, False)]
        results = [_make_result("C1", VerificationState.PROVEN)]
        metric = false_assurance_rate(results, cases)
        assert metric.value == 0.0

    def test_far_one_on_all_false_assurances(self):
        cases = [_make_case("C1", BenchmarkCategory.B_DIRECT_SEMANTIC_VIOLATION, True)]
        results = [_make_result("C1", VerificationState.PROVEN)]  # false assurance
        metric = false_assurance_rate(results, cases)
        assert metric.value == 1.0
        assert metric.numerator == 1
        assert metric.denominator == 1

    def test_far_undefined_when_no_positive_assurances(self):
        cases = [_make_case("C1", BenchmarkCategory.B_DIRECT_SEMANTIC_VIOLATION, True)]
        results = [_make_result("C1", VerificationState.UNKNOWN)]
        metric = false_assurance_rate(results, cases)
        assert metric.value is None
        assert metric.denominator == 0

    def test_far_ignores_unknown_results(self):
        cases = [
            _make_case("C1", BenchmarkCategory.B_DIRECT_SEMANTIC_VIOLATION, True),
            _make_case("C2", BenchmarkCategory.A_CORRECT_IMPLEMENTATION, False),
        ]
        results = [
            _make_result("C1", VerificationState.UNKNOWN),   # abstained, not counted
            _make_result("C2", VerificationState.PROVEN),    # correct positive
        ]
        metric = false_assurance_rate(results, cases)
        assert metric.value == 0.0
        assert metric.denominator == 1

    def test_far_mixed(self):
        cases = [
            _make_case("C1", BenchmarkCategory.B_DIRECT_SEMANTIC_VIOLATION, True),
            _make_case("C2", BenchmarkCategory.A_CORRECT_IMPLEMENTATION, False),
        ]
        results = [
            _make_result("C1", VerificationState.PROVEN),   # false assurance
            _make_result("C2", VerificationState.PROVEN),   # correct
        ]
        metric = false_assurance_rate(results, cases)
        assert metric.value == 0.5  # 1 false / 2 positive


# ---------------------------------------------------------------------------
# Violation Recall Tests
# ---------------------------------------------------------------------------

class TestViolationRecall:

    def test_recall_one_when_all_violations_found(self):
        cases = [_make_case("C1", BenchmarkCategory.B_DIRECT_SEMANTIC_VIOLATION, True)]
        results = [_make_result("C1", VerificationState.VIOLATED)]
        metric = violation_recall(results, cases)
        assert metric.value == 1.0

    def test_recall_zero_when_no_violations_found(self):
        cases = [_make_case("C1", BenchmarkCategory.B_DIRECT_SEMANTIC_VIOLATION, True)]
        results = [_make_result("C1", VerificationState.UNKNOWN)]
        metric = violation_recall(results, cases)
        assert metric.value == 0.0

    def test_recall_undefined_no_violations_in_ground_truth(self):
        cases = [_make_case("C1", BenchmarkCategory.A_CORRECT_IMPLEMENTATION, False)]
        results = [_make_result("C1", VerificationState.PROVEN)]
        metric = violation_recall(results, cases)
        assert metric.value is None


# ---------------------------------------------------------------------------
# Anti-gaming: always-UNKNOWN system
# ---------------------------------------------------------------------------

class TestAntiGaming:

    def test_always_unknown_has_zero_correct_positive_assurance(self):
        cases = [
            _make_case("C1", BenchmarkCategory.A_CORRECT_IMPLEMENTATION, False),
            _make_case("C2", BenchmarkCategory.A_CORRECT_IMPLEMENTATION, False),
        ]
        results = [
            _make_result("C1", VerificationState.UNKNOWN),
            _make_result("C2", VerificationState.UNKNOWN),
        ]
        metric = correct_positive_assurance_rate(results, cases)
        assert metric.value == 0.0

    def test_always_unknown_has_undefined_far(self):
        cases = [_make_case("C1", BenchmarkCategory.B_DIRECT_SEMANTIC_VIOLATION, True)]
        results = [_make_result("C1", VerificationState.UNKNOWN)]
        metric = false_assurance_rate(results, cases)
        assert metric.value is None  # undefined because no positive assurances

    def test_always_unknown_has_zero_violation_recall(self):
        cases = [_make_case("C1", BenchmarkCategory.B_DIRECT_SEMANTIC_VIOLATION, True)]
        results = [_make_result("C1", VerificationState.UNKNOWN)]
        metric = violation_recall(results, cases)
        assert metric.value == 0.0


# ---------------------------------------------------------------------------
# Ambiguity Recall
# ---------------------------------------------------------------------------

class TestAmbiguityRecall:

    def test_correctly_detects_ambiguity(self):
        cases = [_make_case("C1", BenchmarkCategory.D_AMBIGUOUS_REQUIREMENT, False, has_ambiguity=True)]
        results = [_make_result("C1", VerificationState.UNKNOWN, ambiguity=True)]
        metric = ambiguity_recall(results, cases)
        assert metric.value == 1.0

    def test_fails_to_detect_ambiguity(self):
        cases = [_make_case("C1", BenchmarkCategory.D_AMBIGUOUS_REQUIREMENT, False, has_ambiguity=True)]
        results = [_make_result("C1", VerificationState.PROVEN, ambiguity=False)]
        metric = ambiguity_recall(results, cases)
        assert metric.value == 0.0


# ---------------------------------------------------------------------------
# Contradiction Recall
# ---------------------------------------------------------------------------

class TestContradictionRecall:

    def test_correctly_detects_contradiction(self):
        cases = [_make_case("C1", BenchmarkCategory.E_CONTRADICTORY_REQUIREMENTS, False, has_contradiction=True)]
        results = [_make_result("C1", VerificationState.UNKNOWN, contradiction=True)]
        metric = contradiction_recall(results, cases)
        assert metric.value == 1.0


# ---------------------------------------------------------------------------
# Phantom Requirement Rate
# ---------------------------------------------------------------------------

class TestPhantomRequirementRate:

    def test_phantom_treated_as_proven_registers(self):
        cases = [_make_case("C1", BenchmarkCategory.F_PHANTOM_REQUIREMENT, False)]
        results = [_make_result("C1", VerificationState.PROVEN)]  # phantom incorrectly PROVEN
        metric = phantom_requirement_rate(results, cases)
        assert metric.value == 1.0

    def test_phantom_returned_unknown_is_correct(self):
        cases = [_make_case("C1", BenchmarkCategory.F_PHANTOM_REQUIREMENT, False)]
        results = [_make_result("C1", VerificationState.UNKNOWN)]
        metric = phantom_requirement_rate(results, cases)
        assert metric.value == 0.0


# ---------------------------------------------------------------------------
# Stale Evidence Detection Rate
# ---------------------------------------------------------------------------

class TestStaleEvidenceDetectionRate:

    def test_stale_case_returning_unknown_is_correct(self):
        cases = [_make_case("C1", BenchmarkCategory.G_STALE_EVIDENCE, True, expected_state=VerificationState.UNKNOWN)]
        results = [_make_result("C1", VerificationState.UNKNOWN)]
        metric = stale_evidence_detection_rate(results, cases)
        assert metric.value == 1.0

    def test_stale_case_returning_proven_is_failure(self):
        cases = [_make_case("C1", BenchmarkCategory.G_STALE_EVIDENCE, True, expected_state=VerificationState.UNKNOWN)]
        results = [_make_result("C1", VerificationState.PROVEN)]
        metric = stale_evidence_detection_rate(results, cases)
        assert metric.value == 0.0


# ---------------------------------------------------------------------------
# Counterexample Discovery Rate
# ---------------------------------------------------------------------------

class TestCounterexampleDiscoveryRate:

    def test_counterexample_discovered(self):
        cases = [_make_case("C1", BenchmarkCategory.J_COUNTEREXAMPLE_DISCOVERY, False)]
        results = [_make_result("C1", VerificationState.UNKNOWN, ce_refs=["CE-1"])]
        metric = counterexample_discovery_rate(results, cases)
        assert metric.value == 1.0

    def test_no_counterexample(self):
        cases = [_make_case("C1", BenchmarkCategory.J_COUNTEREXAMPLE_DISCOVERY, False)]
        results = [_make_result("C1", VerificationState.UNKNOWN)]
        metric = counterexample_discovery_rate(results, cases)
        assert metric.value == 0.0


# ---------------------------------------------------------------------------
# MetricsCalculator Integration
# ---------------------------------------------------------------------------

class TestMetricsCalculator:

    def test_calculator_produces_report(self):
        calc = MetricsCalculator()
        cases = [
            _make_case("C1", BenchmarkCategory.A_CORRECT_IMPLEMENTATION, False),
            _make_case("C2", BenchmarkCategory.B_DIRECT_SEMANTIC_VIOLATION, True),
        ]
        results = [
            _make_result("C1", VerificationState.PROVEN),
            _make_result("C2", VerificationState.VIOLATED),
        ]
        report = calc.compute("FULL_SVA", results, cases)
        assert report.total_cases == 2
        assert len(report.metrics) > 0
        assert report.system == "FULL_SVA"

    def test_no_single_aggregate_score(self):
        """A MetricsReport is a vector, not a single score."""
        calc = MetricsCalculator()
        cases = [_make_case("C1", BenchmarkCategory.A_CORRECT_IMPLEMENTATION, False)]
        results = [_make_result("C1", VerificationState.PROVEN)]
        report = calc.compute("FULL_SVA", results, cases)
        # There is no 'aggregate_score' field — this is by design.
        assert not hasattr(report, "aggregate_score"), (
            "MetricsReport must NOT have an aggregate_score field."
        )
