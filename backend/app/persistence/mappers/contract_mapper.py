from __future__ import annotations
import dataclasses

from app.contracts.models import SemanticContract, BehaviorExpectation, Invariant, ContractAssumption, VerificationTarget
from app.persistence.models.contract import (
    SemanticContractRow, BehaviorExpectationRow, InvariantRow,
    ContractAssumptionRow, VerificationTargetRow
)


def _source_to_dict(s) -> dict:
    """Serialize a SourceLocation (frozen dataclass) to a plain dict."""
    if dataclasses.is_dataclass(s) and not isinstance(s, type):
        return dataclasses.asdict(s)
    return dict(s)

class ContractMapper:
    @staticmethod
    def contract_to_row(domain: SemanticContract) -> SemanticContractRow:
        return SemanticContractRow(
            contract_id=domain.contract_id,
            contract_version=str(domain.contract_version),
            parent_contract_id=domain.parent_contract_id,
            requirement_id=domain.requirement_id,
            candidate_id=domain.candidate_id,
            analysis_id=domain.analysis_id,
            statement=domain.statement,
            compilation_status=domain.compilation_status.value if hasattr(domain, 'compilation_status') and domain.compilation_status else "DRAFT",
            source_refs=[_source_to_dict(s) for s in domain.source_refs] if domain.source_refs else []
        )

    @staticmethod
    def behavior_to_row(contract_id: str, domain: BehaviorExpectation) -> BehaviorExpectationRow:
        return BehaviorExpectationRow(
            behavior_id=domain.behavior_id,
            contract_id=contract_id,
            is_allowed="ALLOWED",
            description=domain.description,
            actor=domain.actor,
            action=domain.action,
            resource=domain.resource,
            expected_outcome=domain.expected_outcome,
            provenance=domain.provenance.value if domain.provenance else None
        )

    @staticmethod
    def invariant_to_row(contract_id: str, domain: Invariant) -> InvariantRow:
        return InvariantRow(
            invariant_id=domain.invariant_id,
            contract_id=contract_id,
            statement=domain.statement,
            provenance=domain.provenance.value if domain.provenance else None,
            source_refs=[_source_to_dict(s) for s in domain.source_refs] if domain.source_refs else []
        )
    @staticmethod
    def assumption_to_row(contract_id: str, domain: ContractAssumption) -> ContractAssumptionRow:
        return ContractAssumptionRow(
            assumption_id=domain.assumption_id,
            contract_id=contract_id,
            statement=domain.statement,
            provenance=domain.provenance.value if domain.provenance else None
        )

    @staticmethod
    def target_to_row(contract_id: str, domain: VerificationTarget) -> VerificationTargetRow:
        return VerificationTargetRow(
            target_id=domain.target_id,
            contract_id=contract_id,
            category=domain.category.value,
            description=domain.description,
            code_entity_ref=domain.code_entity_ref
        )
