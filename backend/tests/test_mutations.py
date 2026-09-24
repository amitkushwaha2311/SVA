"""
Tests: Mutation Framework
==========================
Tests that the mutator applies declarative mutations correctly
and never executes repository code.
"""

import pytest

from app.benchmark.models import (
    BenchmarkCategory,
    CaseDifficulty,
    EvidenceSufficiency,
    FileFixture,
    GroundTruth,
    MutationDefinition,
    MutationType,
    RepositoryFixture,
    BenchmarkCase,
)
from app.benchmark.mutator import (
    apply_text_mutation,
    apply_mutation_to_fixture,
    derive_mutated_case,
)
from app.evidence.models import VerificationState
from app.benchmark.seed_cases import CASE_A1, A1_MUTATION_REMOVE_AUTH


def _make_gt(**kwargs) -> GroundTruth:
    defaults = dict(
        intent_truth="X does Y.",
        behavioral_truth="Impl does Y.",
        known_violation=False,
        evidence_sufficiency_truth=EvidenceSufficiency.SUFFICIENT,
        expected_assurance_state=VerificationState.PROVEN,
        authored_by="manual_review",
        reviewed_by="manual_review",
    )
    defaults.update(kwargs)
    return GroundTruth(**defaults)


class TestTextMutation:

    def test_applies_mutation_when_pattern_found(self):
        content = "if user.id != project.owner_id:\n    raise PermissionError\n"
        target = "if user.id != project.owner_id:\n    raise PermissionError\n"
        replacement = ""
        new_content, applied = apply_text_mutation(
            content, MutationType.REMOVE_AUTHORIZATION_CHECK, target, replacement
        )
        assert applied is True
        assert "PermissionError" not in new_content

    def test_returns_false_when_pattern_not_found(self):
        content = "def f(): pass\n"
        new_content, applied = apply_text_mutation(
            content, MutationType.REMOVE_AUTHORIZATION_CHECK,
            "if user.is_admin:", ""
        )
        assert applied is False
        assert new_content == content

    def test_only_first_occurrence_replaced(self):
        content = "check()\ncheck()\n"
        new_content, applied = apply_text_mutation(
            content, MutationType.REMOVE_AUTHORIZATION_CHECK,
            "check()", "pass()"
        )
        assert applied is True
        assert new_content.count("check()") == 1
        assert new_content.count("pass()") == 1

    def test_no_subprocess_in_mutation(self):
        """Mutation must never invoke subprocesses."""
        import subprocess
        original_run = subprocess.run
        called = []
        def fake_run(*a, **kw):
            called.append(True)
            return original_run(*a, **kw)
        subprocess.run = fake_run
        try:
            apply_text_mutation("x", MutationType.CHANGE_API_BEHAVIOR, "x", "y")
        finally:
            subprocess.run = original_run
        assert not called, "Mutation must not call subprocess.run"


class TestFixtureMutation:

    def _make_fixture(self) -> RepositoryFixture:
        return RepositoryFixture(
            fixture_id="fix-test",
            description="test",
            files=[
                FileFixture(
                    relative_path="src/delete.py",
                    content=(
                        "def delete_project(user, project):\n"
                        "    if user.id != project.owner_id:\n"
                        "        raise PermissionError\n"
                        "    project.delete()\n"
                    ),
                ),
            ],
        )

    def test_fixture_mutation_produces_new_fixture(self):
        fixture = self._make_fixture()
        mutated = apply_mutation_to_fixture(
            fixture,
            MutationType.REMOVE_AUTHORIZATION_CHECK,
            "src/delete.py",
            "    if user.id != project.owner_id:\n        raise PermissionError\n",
            "",
        )
        assert mutated is not fixture
        assert "PermissionError" not in mutated.files[0].content

    def test_original_fixture_not_modified(self):
        fixture = self._make_fixture()
        original_content = fixture.files[0].content
        apply_mutation_to_fixture(
            fixture,
            MutationType.REMOVE_AUTHORIZATION_CHECK,
            "src/delete.py",
            "    if user.id != project.owner_id:\n        raise PermissionError\n",
            "",
        )
        assert fixture.files[0].content == original_content

    def test_raises_on_missing_pattern(self):
        fixture = self._make_fixture()
        with pytest.raises(ValueError, match="pattern not found"):
            apply_mutation_to_fixture(
                fixture,
                MutationType.REMOVE_AUTHORIZATION_CHECK,
                "src/delete.py",
                "DOES_NOT_EXIST",
                "",
            )

    def test_mutated_fixture_has_new_id(self):
        fixture = self._make_fixture()
        mutated = apply_mutation_to_fixture(
            fixture,
            MutationType.REMOVE_AUTHORIZATION_CHECK,
            "src/delete.py",
            "    if user.id != project.owner_id:\n        raise PermissionError\n",
            "",
        )
        assert mutated.fixture_id != fixture.fixture_id


class TestDerivedMutatedCase:

    def test_derived_case_references_parent(self):
        mutation_def = MutationDefinition(
            mutation_id="mut-001",
            parent_case_id=CASE_A1.case_id,
            mutation_type=MutationType.REMOVE_AUTHORIZATION_CHECK,
            affected_requirement="Only project owners can delete.",
            description="Remove the auth check.",
            expected_behavioral_effect="Anyone can delete.",
            ground_truth_result=_make_gt(
                known_violation=True,
                expected_assurance_state=VerificationState.VIOLATED,
            ),
        )
        derived = derive_mutated_case(
            parent_case=CASE_A1,
            mutation_def=mutation_def,
            target_file_path="src/projects.py",
            target_pattern="    if user.id != project.owner_id:\n        raise PermissionError('Only owners can delete.')\n",
            replacement="",
        )
        assert derived.metadata["parent_case_id"] == CASE_A1.case_id
        assert derived.metadata["mutation_type"] == MutationType.REMOVE_AUTHORIZATION_CHECK.value

    def test_derived_case_has_independent_ground_truth(self):
        mutation_def = MutationDefinition(
            mutation_id="mut-002",
            parent_case_id=CASE_A1.case_id,
            mutation_type=MutationType.REMOVE_AUTHORIZATION_CHECK,
            affected_requirement="Only project owners can delete.",
            description="Remove auth check.",
            expected_behavioral_effect="Violation.",
            ground_truth_result=_make_gt(
                known_violation=True,
                expected_assurance_state=VerificationState.VIOLATED,
            ),
        )
        derived = derive_mutated_case(
            parent_case=CASE_A1,
            mutation_def=mutation_def,
            target_file_path="src/projects.py",
            target_pattern="    if user.id != project.owner_id:\n        raise PermissionError('Only owners can delete.')\n",
            replacement="",
        )
        assert derived.ground_truth.known_violation is True
        assert derived.ground_truth.authored_by == "manual_review"

    def test_mutation_provenance_is_recorded(self):
        mutation_def = A1_MUTATION_REMOVE_AUTH
        derived = derive_mutated_case(
            parent_case=CASE_A1,
            mutation_def=mutation_def,
            target_file_path="src/projects.py",
            target_pattern="    if user.id != project.owner_id:\n        raise PermissionError('Only owners can delete.')\n",
            replacement="",
        )
        assert "parent_case_id" in derived.metadata
        assert "mutation_id" in derived.metadata
