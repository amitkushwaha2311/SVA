import pytest
from app.benchmark.models import BenchmarkCase, BenchmarkCategory, GroundTruth, CaseResult, RepositoryFixture, SystemConfigurationMode
from app.evidence.models import VerificationState
from app.benchmark.metrics.calculator import false_assurance_rate

def test_far_is_na_when_zero_positive_assurances():
    # If a system outputs NO positive assurances (0 PROVEN, 0 SUPPORTED),
    # FAR denominator is 0. It must be None (N/A), not 0.0.
    
    # Ground truth has 1 known violation
    case1 = BenchmarkCase(
        case_id="case-1",
        category=BenchmarkCategory.C_POSITIVE_ONLY_EVIDENCE_TRAP,
        requirement_text="test",
        repository_fixture=RepositoryFixture(fixture_id="f1", description="desc"),
        ground_truth=GroundTruth(
            intent_truth="intent",
            behavioral_truth="behavior",
            evidence_sufficiency_truth="SUFFICIENT",
            known_violation=True,
            expected_assurance_state=VerificationState.VIOLATED
        ),
    )
    
    # System predicts UNKNOWN (an abstention)
    res1 = CaseResult(
        case_id="case-1",
        system=SystemConfigurationMode.FULL_SVA,
        predicted_assurance_state=VerificationState.UNKNOWN,
        predicted_ci_action=None,
        counterexample_refs=[]
    )
    
    metric = false_assurance_rate([res1], [case1])
    assert metric.denominator == 0
    assert metric.value is None  # Ensures it's N/A in rendering
    
def test_far_is_1_when_all_positive_are_false():
    case1 = BenchmarkCase(
        case_id="case-1",
        category=BenchmarkCategory.C_POSITIVE_ONLY_EVIDENCE_TRAP,
        requirement_text="test",
        repository_fixture=RepositoryFixture(fixture_id="f1", description="desc"),
        ground_truth=GroundTruth(
            intent_truth="intent",
            behavioral_truth="behavior",
            evidence_sufficiency_truth="SUFFICIENT",
            known_violation=True,
            expected_assurance_state=VerificationState.VIOLATED
        ),
    )
    
    # System predicts PROVEN, which is a False Assurance
    res1 = CaseResult(
        case_id="case-1",
        system=SystemConfigurationMode.FULL_SVA,
        predicted_assurance_state=VerificationState.PROVEN,
        predicted_ci_action=None,
        counterexample_refs=[]
    )
    
    metric = false_assurance_rate([res1], [case1])
    assert metric.denominator == 1
    assert metric.numerator == 1
    assert metric.value == 1.0

def test_abstentions_do_not_count_as_false_assurance():
    # A system abstains on a violation. This is a Missed Violation, NOT False Assurance.
    case1 = BenchmarkCase(
        case_id="case-1",
        category=BenchmarkCategory.C_POSITIVE_ONLY_EVIDENCE_TRAP,
        requirement_text="test",
        repository_fixture=RepositoryFixture(fixture_id="f1", description="desc"),
        ground_truth=GroundTruth(
            intent_truth="intent",
            behavioral_truth="behavior",
            evidence_sufficiency_truth="SUFFICIENT",
            known_violation=True,
            expected_assurance_state=VerificationState.VIOLATED
        ),
    )
    
    # INCONCLUSIVE abstention
    res1 = CaseResult(
        case_id="case-1",
        system=SystemConfigurationMode.FULL_SVA,
        predicted_assurance_state=VerificationState.INCONCLUSIVE,
        predicted_ci_action=None,
        counterexample_refs=[]
    )
    
    metric = false_assurance_rate([res1], [case1])
    assert metric.numerator == 0
    assert metric.denominator == 0
    assert metric.value is None
