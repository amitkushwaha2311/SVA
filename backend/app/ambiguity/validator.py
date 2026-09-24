"""
SVA Ambiguity Validator
=======================

Enforces strict rules on the ambiguity resolution state machine.
"""

from app.ambiguity.models import AmbiguityCase, InterpretationStatus
from app.repository.intent.models import Provenance


class AmbiguityValidationError(ValueError):
    """Raised when an AmbiguityCase violates SVA rules."""
    pass


class AmbiguityValidator:
    """Validates the state transitions of ambiguity resolution."""

    def validate(self, case: AmbiguityCase) -> None:
        """
        Validate the ambiguity case against strict SVA boundary rules.
        """
        
        if not case.ambiguity_id:
            raise AmbiguityValidationError("Missing ambiguity_id")
            
        for interpretation in case.interpretations:
            if not interpretation.interpretation_id:
                raise AmbiguityValidationError("Interpretation is missing interpretation_id")
                
            # Rule: AI Inference cannot be HUMAN_SELECTED
            # Only a human selection event (provenance = USER) can mark an interpretation HUMAN_SELECTED
            if interpretation.status == InterpretationStatus.HUMAN_SELECTED:
                if interpretation.provenance == Provenance.AI_INFERENCE:
                    raise AmbiguityValidationError(
                        f"Interpretation {interpretation.interpretation_id} cannot be HUMAN_SELECTED "
                        f"while provenance is AI_INFERENCE."
                    )
        
        if case.clarification_question:
            q = case.clarification_question
            if not q.question_id:
                raise AmbiguityValidationError("ClarificationQuestion is missing question_id")
                
            # Question options must map to existing interpretations if they have a mapping
            valid_interpretation_ids = {i.interpretation_id for i in case.interpretations}
            for opt in q.options:
                if opt.maps_to_interpretation_id and opt.maps_to_interpretation_id not in valid_interpretation_ids:
                    raise AmbiguityValidationError(
                        f"Option {opt.option_id} maps to unknown interpretation {opt.maps_to_interpretation_id}"
                    )
