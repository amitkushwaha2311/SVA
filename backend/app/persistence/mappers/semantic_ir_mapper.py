from __future__ import annotations
import dataclasses

from app.semantic_ir.models import SemanticRequirement, SemanticCondition, Precondition, Postcondition, ForbiddenBehavior, Assumption
from app.persistence.models.semantic_ir import SemanticRequirementRow, SemanticConditionRow


def _source_to_dict(s) -> dict:
    """Serialize a SourceLocation (frozen dataclass) to a plain dict."""
    if dataclasses.is_dataclass(s) and not isinstance(s, type):
        return dataclasses.asdict(s)
    return dict(s)


class SemanticIRMapper:
    @staticmethod
    def req_to_row(domain: SemanticRequirement) -> SemanticRequirementRow:
        return SemanticRequirementRow(
            requirement_id=domain.requirement_id,
            candidate_id=domain.candidate_id,
            analysis_id=domain.analysis_id,
            statement=domain.statement,
            original_statement=domain.original_statement,
            status=domain.status.value,
            sources=[_source_to_dict(s) for s in domain.sources],
            provenance=domain.provenance.value if domain.provenance else None
        )

    @staticmethod
    def cond_to_row(requirement_id: str, domain: SemanticCondition) -> SemanticConditionRow:
        return SemanticConditionRow(
            id=domain.id,
            requirement_id=requirement_id,
            statement=domain.statement,
            status=domain.status.value,
            source_refs=[_source_to_dict(s) for s in domain.source_refs],
            provenance=domain.provenance.value if domain.provenance else None
        )
