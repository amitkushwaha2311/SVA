"""
SVA Semantic IR Builder
=======================

Constructs SemanticRequirement objects from IntentCandidates.
"""

from app.repository.intent.models import IntentCandidate
from app.semantic_ir.ids import generate_semantic_requirement_id
from app.semantic_ir.models import (
    BehaviorState,
    ImplementationState,
    IntentState,
    SemanticRequirement,
    VerificationState,
)
from app.semantic_ir.validator import SemanticIRValidator


class SemanticIRBuilder:
    """Safely constructs SemanticRequirements without inflating intent."""

    def __init__(self) -> None:
        self.validator = SemanticIRValidator()

    def build_from_candidate(self, repository_id: str, candidate: IntentCandidate) -> SemanticRequirement:
        """
        Builds a conservative SemanticRequirement from a candidate.
        
        This initial builder does NOT use an LLM, so it leaves semantic interpretation
        fields (actor, action, resource) empty. It preserves the original provenance
        and explicitly defines the VerificationState as UNKNOWN/CANDIDATE.
        """
        
        # Use the normalized statement if available, otherwise the original
        statement = candidate.normalized_statement or candidate.original_statement
        
        req_id = generate_semantic_requirement_id(
            repository_id=repository_id,
            candidate_id=candidate.candidate_id,
            semantic_statement=statement,
        )
        
        # Map CandidateStatus to IntentState safely
        intent_state_map = {
            "CANDIDATE": IntentState.CANDIDATE,
            "CLARIFICATION_REQUIRED": IntentState.CLARIFICATION_REQUIRED,
            "REJECTED": IntentState.REJECTED,
        }
        mapped_intent_state = intent_state_map.get(candidate.status.value, IntentState.CANDIDATE)
        
        # Determine human confirmation
        # If the candidate was human confirmed, the intent state should be HUMAN_CONFIRMED
        if candidate.human_confirmed:
            mapped_intent_state = IntentState.HUMAN_CONFIRMED
            
        verification_state = VerificationState(
            intent=mapped_intent_state,
            implementation=ImplementationState.UNKNOWN,
            behavior=BehaviorState.UNKNOWN,
        )
        
        req = SemanticRequirement(
            requirement_id=req_id,
            candidate_id=candidate.candidate_id,
            analysis_id=candidate.analysis_id,
            statement=statement,
            original_statement=candidate.original_statement,
            provenance=candidate.provenance,
            sources=list(candidate.sources),  # Create a copy of the list
            status=candidate.status,
            human_confirmed=candidate.human_confirmed,
            
            # The following are left empty/None intentionally because
            # we do not invent semantics in Phase 5 without safe extraction.
            actor=None,
            action=None,
            resource=None,
            preconditions=[],
            postconditions=[],
            forbidden_behaviors=[],
            assumptions=[],
            interpretation_notes=None,
            
            evidence_refs=[],
            code_entity_refs=[],
            verification_state=verification_state,
        )
        
        # Validate the constructed object against strict boundaries
        self.validator.validate(req)
        
        return req

    def build_all(self, repository_id: str, candidates: list[IntentCandidate]) -> list[SemanticRequirement]:
        """Builds semantic requirements for a list of candidates."""
        reqs = []
        for c in candidates:
            # We don't resolve contradictions. Every candidate gets a SemanticRequirement.
            reqs.append(self.build_from_candidate(repository_id, c))
        return reqs
