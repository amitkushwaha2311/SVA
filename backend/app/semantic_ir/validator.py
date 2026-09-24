"""
SVA Semantic IR Validator
=========================

Enforces strict rules on the semantic intermediate representation.
"""

from app.semantic_ir.models import BehaviorState, IntentState, SemanticRequirement


class SemanticIRValidationError(ValueError):
    """Raised when a SemanticRequirement violates SVA rules."""
    pass


class SemanticIRValidator:
    """Validates the state of a SemanticRequirement."""

    def validate(self, req: SemanticRequirement) -> None:
        """
        Validate the requirement against strict SVA boundary rules.
        Raises SemanticIRValidationError if invalid.
        """
        
        # 1. Human Confirmation Boundary
        if req.human_confirmed and req.verification_state.intent == IntentState.CANDIDATE:
            raise SemanticIRValidationError(
                f"Requirement {req.requirement_id} cannot be human_confirmed=True "
                f"while intent state is CANDIDATE."
            )
            
        # 2. Proven Evidence Boundary
        if req.verification_state.behavior == BehaviorState.PROVEN:
            if not req.evidence_refs:
                raise SemanticIRValidationError(
                    f"Requirement {req.requirement_id} claims behavior is PROVEN "
                    f"but contains no evidence_refs."
                )
                
        # 3. Required Identity Fields
        if not req.requirement_id:
            raise SemanticIRValidationError("Missing requirement_id")
        if not req.candidate_id:
            raise SemanticIRValidationError("Missing candidate_id")
        if not req.original_statement:
            raise SemanticIRValidationError("Missing original_statement")
