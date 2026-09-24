from __future__ import annotations
import dataclasses
from app.repository.intent.models import IntentCandidate
from app.persistence.models.intent import IntentCandidateRow


def _source_to_dict(s) -> dict:
    """Serialize a SourceLocation (frozen dataclass) to a plain dict."""
    if dataclasses.is_dataclass(s) and not isinstance(s, type):
        return dataclasses.asdict(s)
    return dict(s)


class IntentMapper:
    @staticmethod
    def to_row(domain: IntentCandidate) -> IntentCandidateRow:
        return IntentCandidateRow(
            candidate_id=domain.candidate_id,
            analysis_id=domain.analysis_id,
            original_statement=domain.original_statement,
            normalized_statement=domain.normalized_statement,
            status=domain.status.value,
            human_confirmed=domain.human_confirmed,
            extraction_method=domain.extraction_method,
            sources=[_source_to_dict(s) for s in domain.sources] if domain.sources else [],
            provenance=domain.provenance.value if domain.provenance else None,
            evidence=[_source_to_dict(e) for e in domain.evidence] if domain.evidence else [],
        )

    @staticmethod
    def from_row(row: IntentCandidateRow) -> IntentCandidate:
        from app.repository.intent.models import CandidateStatus, Provenance
        return IntentCandidate(
            candidate_id=row.candidate_id,
            analysis_id=row.analysis_id,
            original_statement=row.original_statement,
            normalized_statement=row.normalized_statement,
            status=CandidateStatus(row.status),
            human_confirmed=row.human_confirmed,
            extraction_method=row.extraction_method,
            sources=[],
            provenance=Provenance(row.provenance) if row.provenance else None,
            evidence=[]
        )
