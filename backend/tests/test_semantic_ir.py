"""
Tests for SVA Phase 5: Semantic IR Foundation
=============================================
"""

import pytest

from app.repository.intent.models import CandidateStatus, IntentCandidate, Provenance, SourceLocation
from app.semantic_ir.builder import SemanticIRBuilder
from app.semantic_ir.ids import generate_semantic_requirement_id
from app.semantic_ir.models import (
    BehaviorState,
    EvidenceRef,
    ImplementationState,
    IntentState,
    SemanticRequirement,
    VerificationState,
)
from app.semantic_ir.validator import SemanticIRValidationError, SemanticIRValidator


@pytest.fixture
def builder() -> SemanticIRBuilder:
    return SemanticIRBuilder()

@pytest.fixture
def validator() -> SemanticIRValidator:
    return SemanticIRValidator()

@pytest.fixture
def candidate() -> IntentCandidate:
    return IntentCandidate(
        candidate_id="cand-123",
        analysis_id="run-1",
        sources=[SourceLocation(path="README.md", start_line=10, end_line=10)],
        original_statement="Users must log in.",
        provenance=Provenance.README,
        status=CandidateStatus.CANDIDATE,
        human_confirmed=False,
    )


class TestSemanticIRBuilder:
    def test_builds_semantic_requirement_from_candidate(self, builder: SemanticIRBuilder, candidate: IntentCandidate) -> None:
        req = builder.build_from_candidate("repo-1", candidate)
        
        assert req.candidate_id == "cand-123"
        assert req.original_statement == "Users must log in."
        assert req.provenance == Provenance.README
        assert req.sources[0].path == "README.md"
        assert req.status == CandidateStatus.CANDIDATE
        assert req.human_confirmed is False
        
        # Semantic interpretations remain unknown
        assert req.actor is None
        assert req.action is None
        assert req.resource is None
        assert len(req.assumptions) == 0
        assert len(req.preconditions) == 0
        assert len(req.evidence_refs) == 0
        
        # Verification states are correctly initialized
        assert req.verification_state.intent == IntentState.CANDIDATE
        assert req.verification_state.implementation == ImplementationState.UNKNOWN
        assert req.verification_state.behavior == BehaviorState.UNKNOWN

    def test_human_confirmed_candidate_maps_to_confirmed_intent(self, builder: SemanticIRBuilder, candidate: IntentCandidate) -> None:
        candidate.human_confirmed = True
        req = builder.build_from_candidate("repo-1", candidate)
        
        assert req.human_confirmed is True
        assert req.verification_state.intent == IntentState.HUMAN_CONFIRMED

    def test_contradictions_remain_separate(self, builder: SemanticIRBuilder) -> None:
        c1 = IntentCandidate(
            candidate_id="c1",
            analysis_id="run-1",
            sources=[],
            original_statement="Users can delete projects.",
            provenance=Provenance.DOCUMENT,
        )
        c2 = IntentCandidate(
            candidate_id="c2",
            analysis_id="run-1",
            sources=[],
            original_statement="Only owners can delete projects.",
            provenance=Provenance.DOCUMENT,
        )
        
        reqs = builder.build_all("repo-1", [c1, c2])
        assert len(reqs) == 2
        assert reqs[0].original_statement != reqs[1].original_statement
        assert reqs[0].requirement_id != reqs[1].requirement_id


class TestSemanticIRValidator:
    def test_human_confirmed_requires_correct_intent_state(self, validator: SemanticIRValidator, candidate: IntentCandidate, builder: SemanticIRBuilder) -> None:
        req = builder.build_from_candidate("repo-1", candidate)
        # Manually create invalid state
        req.human_confirmed = True
        req.verification_state.intent = IntentState.CANDIDATE
        
        with pytest.raises(SemanticIRValidationError, match="cannot be human_confirmed=True while intent state is CANDIDATE"):
            validator.validate(req)

    def test_proven_behavior_requires_evidence(self, validator: SemanticIRValidator, candidate: IntentCandidate, builder: SemanticIRBuilder) -> None:
        req = builder.build_from_candidate("repo-1", candidate)
        req.verification_state.behavior = BehaviorState.PROVEN
        # evidence_refs is empty
        
        with pytest.raises(SemanticIRValidationError, match="claims behavior is PROVEN but contains no evidence_refs"):
            validator.validate(req)
            
    def test_proven_behavior_with_evidence_is_valid(self, validator: SemanticIRValidator, candidate: IntentCandidate, builder: SemanticIRBuilder) -> None:
        req = builder.build_from_candidate("repo-1", candidate)
        req.verification_state.behavior = BehaviorState.PROVEN
        req.evidence_refs = [EvidenceRef(evidence_id="e1", evidence_type="TEST", description="test passed")]
        
        # Should not raise
        validator.validate(req)

    def test_missing_identity_fields_raises(self, validator: SemanticIRValidator, candidate: IntentCandidate, builder: SemanticIRBuilder) -> None:
        req = builder.build_from_candidate("repo-1", candidate)
        req.requirement_id = ""
        with pytest.raises(SemanticIRValidationError, match="Missing requirement_id"):
            validator.validate(req)


class TestDeterministicIdentity:
    def test_same_inputs_same_id(self) -> None:
        id1 = generate_semantic_requirement_id("repo-1", "cand-1", "Users must login")
        id2 = generate_semantic_requirement_id("repo-1", "cand-1", "Users must login")
        assert id1 == id2

    def test_different_candidate_different_id(self) -> None:
        id1 = generate_semantic_requirement_id("repo-1", "cand-1", "Users must login")
        id2 = generate_semantic_requirement_id("repo-1", "cand-2", "Users must login")
        assert id1 != id2


class TestSemanticExtraction:
    """
    Tests for the _extract_semantics() rule-based extraction logic.

    These tests verify that:
    - The project-owner requirement is correctly structured.
    - Unrecognized sentences return None for all fields.
    - Ambiguous sentences do not produce guessed semantics.
    - Provenance is always inherited from the candidate — never invented.
    - human_confirmed is never set to True by the builder.
    - Output is fully deterministic across repeated calls.
    """

    def _make_candidate(
        self,
        statement: str,
        provenance: Provenance = Provenance.DOCUMENT,
        human_confirmed: bool = False,
    ) -> IntentCandidate:
        from app.repository.intent.models import SourceLocation
        return IntentCandidate(
            candidate_id="test-cand",
            analysis_id="test-run",
            sources=[SourceLocation(path="requirements.md", start_line=42, end_line=42)],
            original_statement=statement,
            provenance=provenance,
            status=CandidateStatus.CANDIDATE,
            human_confirmed=human_confirmed,
        )

    # ── Project-owner requirement ───────────────────────────────────────────

    def test_project_owner_extracts_actor(self, builder: SemanticIRBuilder) -> None:
        c = self._make_candidate("Only project owners can delete projects.")
        req = builder.build_from_candidate("repo-x", c)
        assert req.actor is not None
        assert req.actor.name == "project owner"

    def test_project_owner_extracts_action(self, builder: SemanticIRBuilder) -> None:
        c = self._make_candidate("Only project owners can delete projects.")
        req = builder.build_from_candidate("repo-x", c)
        assert req.action is not None
        assert req.action.name == "delete"

    def test_project_owner_extracts_resource(self, builder: SemanticIRBuilder) -> None:
        c = self._make_candidate("Only project owners can delete projects.")
        req = builder.build_from_candidate("repo-x", c)
        assert req.resource is not None
        assert req.resource.name == "project"

    def test_project_owner_extracts_ownership_assumption(self, builder: SemanticIRBuilder) -> None:
        c = self._make_candidate("Only project owners can delete projects.")
        req = builder.build_from_candidate("repo-x", c)
        assert len(req.assumptions) == 1
        assert req.assumptions[0].statement == "owner = resource.owner_id"

    def test_project_owner_assumption_provenance_is_document(self, builder: SemanticIRBuilder) -> None:
        c = self._make_candidate("Only project owners can delete projects.", provenance=Provenance.DOCUMENT)
        req = builder.build_from_candidate("repo-x", c)
        assert req.assumptions[0].provenance == Provenance.DOCUMENT

    # ── Unrecognized / non-matching sentences return None ──────────────────

    def test_plain_must_sentence_leaves_actor_none(self, builder: SemanticIRBuilder) -> None:
        """A normal must-requirement that does not match the 'only X can Y Z' pattern."""
        c = self._make_candidate("Users must log in before accessing any resource.")
        req = builder.build_from_candidate("repo-x", c)
        assert req.actor is None
        assert req.action is None
        assert req.resource is None
        assert req.assumptions == []

    def test_system_shall_sentence_leaves_fields_none(self, builder: SemanticIRBuilder) -> None:
        c = self._make_candidate("The system shall log all errors to the audit trail.")
        req = builder.build_from_candidate("repo-x", c)
        assert req.actor is None
        assert req.action is None
        assert req.resource is None

    def test_ambiguous_can_sentence_without_only_leaves_fields_none(self, builder: SemanticIRBuilder) -> None:
        """'Users can delete projects.' is ambiguous (no 'only') — must not produce semantics."""
        c = self._make_candidate("Users can delete projects.")
        req = builder.build_from_candidate("repo-x", c)
        assert req.actor is None
        assert req.action is None
        assert req.resource is None
        assert req.assumptions == []

    def test_empty_statement_leaves_fields_none(self, builder: SemanticIRBuilder) -> None:
        c = self._make_candidate("Short.")
        req = builder.build_from_candidate("repo-x", c)
        assert req.actor is None
        assert req.action is None
        assert req.resource is None

    # ── human_confirmed is never set by the builder ─────────────────────────

    def test_extraction_does_not_set_human_confirmed(self, builder: SemanticIRBuilder) -> None:
        c = self._make_candidate("Only project owners can delete projects.", human_confirmed=False)
        req = builder.build_from_candidate("repo-x", c)
        assert req.human_confirmed is False
        assert req.verification_state.intent == IntentState.CANDIDATE

    def test_human_confirmed_candidate_still_extracts_semantics(self, builder: SemanticIRBuilder) -> None:
        """Even a human-confirmed candidate still gets semantics extracted."""
        c = self._make_candidate("Only project owners can delete projects.", human_confirmed=True)
        req = builder.build_from_candidate("repo-x", c)
        # human_confirmed is preserved faithfully
        assert req.human_confirmed is True
        assert req.verification_state.intent == IntentState.HUMAN_CONFIRMED
        # Semantics are still populated
        assert req.actor is not None
        assert req.action is not None
        assert req.resource is not None

    # ── Provenance is always inherited ─────────────────────────────────────

    def test_extracted_requirement_provenance_matches_candidate(self, builder: SemanticIRBuilder) -> None:
        c = self._make_candidate("Only project owners can delete projects.", provenance=Provenance.DOCUMENT)
        req = builder.build_from_candidate("repo-x", c)
        assert req.provenance == Provenance.DOCUMENT

    def test_readme_provenance_preserved(self, builder: SemanticIRBuilder) -> None:
        c = self._make_candidate("Only project owners can delete projects.", provenance=Provenance.README)
        req = builder.build_from_candidate("repo-x", c)
        assert req.provenance == Provenance.README
        # Assumption provenance also matches the source
        assert req.assumptions[0].provenance == Provenance.README

    # ── Determinism ─────────────────────────────────────────────────────────

    def test_extraction_is_deterministic(self, builder: SemanticIRBuilder) -> None:
        """Repeated calls with identical input must produce identical output."""
        c = self._make_candidate("Only project owners can delete projects.")
        req1 = builder.build_from_candidate("repo-x", c)
        req2 = builder.build_from_candidate("repo-x", c)
        assert req1.requirement_id == req2.requirement_id
        assert req1.actor.name == req2.actor.name
        assert req1.action.name == req2.action.name
        assert req1.resource.name == req2.resource.name
        assert req1.assumptions[0].id == req2.assumptions[0].id
        assert req1.assumptions[0].statement == req2.assumptions[0].statement

    def test_different_only_pattern_extracts_correctly(self, builder: SemanticIRBuilder) -> None:
        """Test a second 'only X can Y Z' sentence to confirm pattern generality."""
        c = self._make_candidate("Only admins can access the dashboard.")
        req = builder.build_from_candidate("repo-x", c)
        assert req.actor is not None
        assert req.actor.name == "admin"
        assert req.action is not None
        assert req.action.name == "access"
        assert req.resource is not None
        assert req.resource.name == "the dashboard"
        # "admin" does not contain "owner" → no ownership assumption
        assert req.assumptions == []

