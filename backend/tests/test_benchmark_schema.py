"""
Tests: Benchmark Schema Validation
====================================
Validates that BenchmarkCase, GroundTruth, and related models
enforce correctness, determinism, and independence.
"""

import pytest
from pydantic import ValidationError

from app.benchmark.models import (
    BenchmarkCase,
    BenchmarkCategory,
    CaseDifficulty,
    EvidenceSufficiency,
    FileFixture,
    GroundTruth,
    MutationDefinition,
    MutationType,
    RepositoryFixture,
    SystemConfigurationMode,
    EvaluationMode,
    ReproducibilityMetadata,
)
from app.evidence.models import VerificationState
from app.drift.models import SemanticCIDecision
from app.benchmark.seed_cases import SEED_CASES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fixture(fixture_id: str = "fix-test") -> RepositoryFixture:
    return RepositoryFixture(
        fixture_id=fixture_id,
        description="Test fixture",
        files=[FileFixture(relative_path="src/main.py", content="def f(): pass")],
    )


def _make_gt(**kwargs) -> GroundTruth:
    defaults = dict(
        intent_truth="A does B.",
        behavioral_truth="Implementation does B.",
        known_violation=False,
        evidence_sufficiency_truth=EvidenceSufficiency.SUFFICIENT,
        expected_assurance_state=VerificationState.PROVEN,
        authored_by="manual_review",
        reviewed_by="manual_review",
    )
    defaults.update(kwargs)
    return GroundTruth(**defaults)


def _make_case(**kwargs) -> BenchmarkCase:
    defaults = dict(
        case_id="TEST-001",
        version="1",
        category=BenchmarkCategory.A_CORRECT_IMPLEMENTATION,
        requirement_text="Only owners can delete.",
        repository_fixture=_make_fixture(),
        ground_truth=_make_gt(),
    )
    defaults.update(kwargs)
    return BenchmarkCase(**defaults)


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------

class TestBenchmarkCaseSchema:

    def test_valid_case_creates_successfully(self):
        case = _make_case()
        assert case.case_id == "TEST-001"
        assert case.category == BenchmarkCategory.A_CORRECT_IMPLEMENTATION

    def test_case_id_required(self):
        with pytest.raises(ValidationError):
            BenchmarkCase(
                version="1",
                category=BenchmarkCategory.A_CORRECT_IMPLEMENTATION,
                requirement_text="test",
                repository_fixture=_make_fixture(),
                ground_truth=_make_gt(),
            )

    def test_requirement_text_required(self):
        with pytest.raises(ValidationError):
            BenchmarkCase(
                case_id="X",
                version="1",
                category=BenchmarkCategory.A_CORRECT_IMPLEMENTATION,
                repository_fixture=_make_fixture(),
                ground_truth=_make_gt(),
            )

    def test_all_categories_valid(self):
        for cat in BenchmarkCategory:
            case = _make_case(category=cat)
            assert case.category == cat


class TestGroundTruthSchema:

    def test_sva_authored_by_rejected(self):
        """Ground truth must never be authored by SVA itself."""
        with pytest.raises(ValidationError, match="authored_by"):
            _make_gt(authored_by="sva")

    def test_sva_output_authored_by_rejected(self):
        with pytest.raises(ValidationError):
            _make_gt(authored_by="sva_output")

    def test_manual_review_accepted(self):
        gt = _make_gt(authored_by="manual_review")
        assert gt.authored_by == "manual_review"

    def test_ambiguity_requires_interpretations(self):
        with pytest.raises(ValidationError, match="ambiguity_interpretation"):
            _make_gt(has_ambiguity=True, ambiguity_interpretations=[])

    def test_ambiguity_with_interpretations_valid(self):
        gt = _make_gt(
            has_ambiguity=True,
            ambiguity_interpretations=["interp A", "interp B"],
        )
        assert gt.has_ambiguity is True

    def test_contradiction_requires_pair(self):
        with pytest.raises(ValidationError, match="contradiction_pair"):
            _make_gt(has_contradiction=True, contradiction_pair=["only one"])

    def test_contradiction_with_pair_valid(self):
        gt = _make_gt(
            has_contradiction=True,
            contradiction_pair=["REQ-A says X", "REQ-B says not X"],
        )
        assert gt.has_contradiction is True

    def test_evidence_sufficiency_values(self):
        for ev in EvidenceSufficiency:
            gt = _make_gt(evidence_sufficiency_truth=ev)
            assert gt.evidence_sufficiency_truth == ev


class TestDeterministicCaseIds:

    def test_same_inputs_produce_same_id(self):
        case1 = _make_case(case_id="X")
        case2 = _make_case(case_id="X")
        assert case1.deterministic_id() == case2.deterministic_id()

    def test_different_requirements_produce_different_ids(self):
        case1 = _make_case(requirement_text="Only owners can delete.")
        case2 = _make_case(requirement_text="Any user can delete.")
        assert case1.deterministic_id() != case2.deterministic_id()

    def test_different_fixture_content_produces_different_ids(self):
        fix1 = RepositoryFixture(
            fixture_id="f1", description="d",
            files=[FileFixture(relative_path="src/a.py", content="v1")]
        )
        fix2 = RepositoryFixture(
            fixture_id="f1", description="d",
            files=[FileFixture(relative_path="src/a.py", content="v2")]
        )
        case1 = _make_case(repository_fixture=fix1)
        case2 = _make_case(repository_fixture=fix2)
        assert case1.deterministic_id() != case2.deterministic_id()


class TestFixtureContentHash:

    def test_same_content_same_hash(self):
        fix1 = _make_fixture()
        fix2 = _make_fixture()
        assert fix1.content_hash() == fix2.content_hash()

    def test_different_content_different_hash(self):
        fix1 = RepositoryFixture(
            fixture_id="f", description="d",
            files=[FileFixture(relative_path="a.py", content="v1")]
        )
        fix2 = RepositoryFixture(
            fixture_id="f", description="d",
            files=[FileFixture(relative_path="a.py", content="v2")]
        )
        assert fix1.content_hash() != fix2.content_hash()


class TestSeedCasesIntegrity:

    def test_all_seed_cases_have_manual_ground_truth(self):
        for case in SEED_CASES:
            assert case.ground_truth.authored_by == "manual_review", (
                f"{case.case_id}: ground truth must be authored by manual_review, "
                f"not by '{case.ground_truth.authored_by}'"
            )

    def test_seed_cases_have_unique_ids(self):
        ids = [c.case_id for c in SEED_CASES]
        assert len(ids) == len(set(ids)), "Seed case IDs must be unique."

    def test_seed_cases_cover_expected_categories(self):
        covered = {c.category for c in SEED_CASES}
        required = {
            BenchmarkCategory.A_CORRECT_IMPLEMENTATION,
            BenchmarkCategory.B_DIRECT_SEMANTIC_VIOLATION,
            BenchmarkCategory.C_POSITIVE_ONLY_EVIDENCE_TRAP,
            BenchmarkCategory.D_AMBIGUOUS_REQUIREMENT,
            BenchmarkCategory.E_CONTRADICTORY_REQUIREMENTS,
            BenchmarkCategory.F_PHANTOM_REQUIREMENT,
            BenchmarkCategory.G_STALE_EVIDENCE,
            BenchmarkCategory.K_MALICIOUS_REPOSITORY_TEXT,
            BenchmarkCategory.L_MISSING_EVIDENCE,
        }
        missing = required - covered
        assert not missing, f"Seed cases missing categories: {missing}"

    def test_known_violation_cases_have_violated_or_unknown_expected_state(self):
        for case in SEED_CASES:
            if case.ground_truth.known_violation:
                assert case.ground_truth.expected_assurance_state in {
                    VerificationState.VIOLATED,
                    VerificationState.UNKNOWN,
                    VerificationState.INCONCLUSIVE,
                }, (
                    f"{case.case_id}: known_violation=True but expected_assurance_state "
                    f"is {case.ground_truth.expected_assurance_state.value}"
                )
