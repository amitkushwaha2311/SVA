from app.drift.models import DriftReport, ChangeRecord, SemanticImpact, InvalidationRecord
from app.persistence.models.drift import DriftReportRow, ChangeRecordRow, SemanticImpactRow, InvalidationRecordRow


class DriftMapper:
    @staticmethod
    def report_to_row(domain: DriftReport) -> DriftReportRow:
        return DriftReportRow(
            drift_id=domain.drift_id,
            repository_id=domain.repository_id,
            base_commit=domain.base_commit,
            target_commit=domain.target_commit,
            changes=[c.model_dump() for c in domain.changes],
            impacts=[i.model_dump() for i in domain.impacts],
            invalidations=[inv.model_dump() for inv in domain.invalidations],
            summary=domain.summary.model_dump() if domain.summary else None
        )

    @staticmethod
    def change_to_row(domain: ChangeRecord) -> ChangeRecordRow:
        return ChangeRecordRow(
            change_id=domain.change_id,
            repository_id=domain.repository_id,
            base_commit=domain.base_commit,
            target_commit=domain.target_commit,
            file_path=str(domain.file_path) if domain.file_path else None,
            file_classification=domain.file_classification.value if domain.file_classification else None,
            file_change_type=domain.file_change_type.value if domain.file_change_type else None,
            entity_id=domain.entity_id
        )

    @staticmethod
    def impact_to_row(domain: SemanticImpact) -> SemanticImpactRow:
        return SemanticImpactRow(
            impact_id=domain.impact_id,
            change_id=domain.change_id,
            artifact_type=domain.artifact_type,
            artifact_id=domain.artifact_id,
            affected_requirements=domain.affected_requirements,
            affected_contracts=domain.affected_contracts,
            affected_obligations=domain.affected_obligations,
            affected_targets=domain.affected_targets
        )

    @staticmethod
    def invalidation_to_row(domain: InvalidationRecord) -> InvalidationRecordRow:
        return InvalidationRecordRow(
            invalidation_id=domain.invalidation_id,
            artifact_type=domain.artifact_type,
            artifact_id=domain.artifact_id,
            previous_commit=domain.previous_commit,
            target_commit=domain.target_commit,
            reason=domain.reason,
            status=domain.status.value if hasattr(domain.status, 'value') else str(domain.status),
            related_change_ids=domain.related_change_ids
        )
