from app.ambiguity.models import AmbiguityCase, Interpretation, ClarificationQuestion
from app.persistence.models.ambiguity import AmbiguityCaseRow, InterpretationRow, ClarificationQuestionRow

class AmbiguityMapper:
    @staticmethod
    def case_to_row(domain: AmbiguityCase) -> AmbiguityCaseRow:
        return AmbiguityCaseRow(
            ambiguity_id=domain.ambiguity_id,
            statement=domain.statement,
            requirement_ids=domain.requirement_ids,
            candidate_ids=domain.candidate_ids,
            ambiguity_types=[t.value for t in domain.ambiguity_types]
        )

    @staticmethod
    def interpretation_to_row(ambiguity_id: str, domain: Interpretation) -> InterpretationRow:
        return InterpretationRow(
            interpretation_id=domain.interpretation_id,
            ambiguity_id=ambiguity_id,
            requirement_id=domain.requirement_id,
            statement=domain.statement,
            interpretation_method=domain.interpretation_method,  # plain str field
            status=domain.status.value,
            semantic_fields=domain.semantic_fields,
            assumptions=domain.assumptions,
            provenance=domain.provenance.value if domain.provenance else None
        )

    @staticmethod
    def question_to_row(ambiguity_id: str, domain: ClarificationQuestion) -> ClarificationQuestionRow:
        return ClarificationQuestionRow(
            question_id=domain.question_id,
            ambiguity_id=ambiguity_id,
            question=domain.question,
            distinguishing_scenario_id=domain.distinguishing_scenario_id,
            information_gain=domain.information_gain,
            status=domain.status.value,
            options=[o.model_dump() for o in domain.options]
        )
