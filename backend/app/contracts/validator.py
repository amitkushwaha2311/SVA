"""
SVA Contract Validator
======================

Enforces strict rules on SemanticContract state.
"""

from app.contracts.models import ContractStatus, SemanticContract
from app.semantic_ir.models import BehaviorState


class ContractValidationError(ValueError):
    """Raised when a SemanticContract violates SVA rules."""
    pass


class ContractValidator:
    """Validates a SemanticContract against strict SVA boundary rules."""

    def validate(self, contract: SemanticContract) -> None:
        # 1. Identity
        if not contract.contract_id:
            raise ContractValidationError("Missing contract_id")
        if not contract.requirement_id:
            raise ContractValidationError("Missing requirement_id")

        # 2. Ambiguity gate: READY contracts must not have a block_reason
        if contract.compilation_status == ContractStatus.READY:
            if contract.block_reason:
                raise ContractValidationError(
                    f"Contract {contract.contract_id} is READY but has a block_reason set."
                )

        # 3. BLOCKED contracts must have a block_reason
        if contract.compilation_status == ContractStatus.BLOCKED:
            if not contract.block_reason:
                raise ContractValidationError(
                    f"Contract {contract.contract_id} is BLOCKED but no block_reason provided."
                )

        # 4. PROVEN behavior requires evidence (reuse Phase 5 boundary)
        if contract.verification_state.behavior == BehaviorState.PROVEN:
            raise ContractValidationError(
                f"Contract {contract.contract_id} claims behavior is PROVEN — "
                "the Contract Compiler never generates proof."
            )

        # 5. Verification targets must not claim verification
        for target in contract.verification_targets:
            if not target.target_id:
                raise ContractValidationError("VerificationTarget missing target_id")
