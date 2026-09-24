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
