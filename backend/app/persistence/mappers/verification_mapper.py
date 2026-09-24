from app.verification.models import ObligationVerification, RequirementVerification, VerificationReport, VerificationDecision
from app.persistence.models.verification import ObligationVerificationRow, RequirementVerificationRow, VerificationReportRow

class VerificationMapper:
    @staticmethod
    def obl_to_row(domain: ObligationVerification) -> ObligationVerificationRow:
        return ObligationVerificationRow(
            obligation_id=domain.obligation_id,
            contract_id=domain.contract_id,
            requirement_id=domain.requirement_id,
            decision=domain.decision.value,
            explanation=domain.explanation,
            supporting_evidence=[e.model_dump() for e in domain.supporting_evidence],
            contradicting_evidence=[e.model_dump() for e in domain.contradicting_evidence]
        )

    @staticmethod
    def req_to_row(domain: RequirementVerification) -> RequirementVerificationRow:
        row = RequirementVerificationRow(
            id=f"{domain.requirement_id}_{domain.contract_id}",
            requirement_id=domain.requirement_id,
            contract_id=domain.contract_id,
            decision=domain.decision.value,
            explanation=domain.explanation,
            limitations=domain.limitations,
            obligation_results=[r.model_dump() for r in domain.obligation_results],
            unresolved_obligations=domain.unresolved_obligations
        )
        return row

    @staticmethod
    def report_to_row(domain: VerificationReport) -> VerificationReportRow:
        return VerificationReportRow(
            verification_id=domain.verification_id,
            repository_id=domain.repository_id,
            commit_id=domain.commit_id,
            generated_at=domain.generated_at,
            engine_version=domain.engine_version,
            requirement_results=[r.model_dump() for r in domain.requirement_results]
        )
