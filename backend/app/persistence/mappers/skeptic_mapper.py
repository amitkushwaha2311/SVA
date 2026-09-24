from app.skeptic.models import Counterexample, SkepticReport
from app.persistence.models.skeptic import CounterexampleRow, SkepticReportRow


class SkepticMapper:
    @staticmethod
    def counterexample_to_row(domain: Counterexample) -> CounterexampleRow:
        return CounterexampleRow(
            counterexample_id=domain.counterexample_id,
            requirement_id=domain.requirement_id,
            contract_id=domain.contract_id,
            obligation_id=domain.obligation_id,
            target_id=domain.target_id,
            scenario_id=domain.scenario_id,
            hypothesis=domain.hypothesis,
            preconditions=domain.preconditions if domain.preconditions else []
        )

    @staticmethod
    def report_to_row(domain: SkepticReport) -> SkepticReportRow:
        return SkepticReportRow(
            report_id=domain.report_id,
            requirement_id=domain.requirement_id,
            contract_id=domain.contract_id,
            total_generated=domain.total_generated,
            total_deduplicated=domain.total_deduplicated,
            strategies_applied=[s.value for s in domain.strategies_applied],
            counterexamples=[c.model_dump() for c in domain.counterexamples],
            generated_at=domain.generated_at.isoformat() if hasattr(domain.generated_at, 'isoformat') else str(domain.generated_at)
        )
