"""
SVA Semantic Contract Compiler
===============================

Transforms a confirmed SemanticRequirement into a SemanticContract.
"""

from app.contracts.ids import (
    generate_assumption_id,
    generate_behavior_id,
    generate_contract_id,
    generate_invariant_id,
    generate_target_id,
)
from app.contracts.models import (
    BehaviorExpectation,
    ContractAssumption,
    ContractStatus,
    Invariant,
    SemanticContract,
    VerificationTarget,
    VerificationTargetCategory,
)
from app.contracts.normalization import normalize_statement
from app.contracts.validator import ContractValidationError, ContractValidator
from app.repository.intent.models import CandidateStatus
from app.semantic_ir.models import (
    BehaviorState,
    ImplementationState,
    IntentState,
    SemanticRequirement,
    VerificationState,
)


class SemanticContractCompiler:
    """
    Compiles confirmed SemanticRequirements into structured SemanticContracts.

    Rules:
    - CANDIDATE → BLOCKED
    - CLARIFICATION_REQUIRED → BLOCKED
    - REJECTED → BLOCKED
    - Insufficient semantic structure → BLOCKED
    - HUMAN_CONFIRMED + sufficient structure → READY

    The compiler NEVER claims implementation correctness.
    """

    def __init__(self) -> None:
        self.validator = ContractValidator()

    def compile(self, repository_id: str, requirement: SemanticRequirement) -> SemanticContract:
        """Compile a SemanticRequirement into a SemanticContract."""

        contract_id = generate_contract_id(repository_id, requirement.requirement_id)

        # --- Ambiguity Gate ---
        block_reason = self._check_blocked(requirement)

        if block_reason:
            contract = SemanticContract(
                contract_id=contract_id,
                requirement_id=requirement.requirement_id,
                candidate_id=requirement.candidate_id,
                analysis_id=requirement.analysis_id,
                statement=requirement.statement,
                source_refs=list(requirement.sources),
                provenance=requirement.provenance,
                compilation_status=ContractStatus.BLOCKED,
                block_reason=block_reason,
                verification_state=VerificationState(
                    intent=requirement.verification_state.intent,
                    implementation=ImplementationState.UNKNOWN,
                    behavior=BehaviorState.UNKNOWN,
                ),
            )
            self.validator.validate(contract)
            return contract

        # --- Build READY contract ---
        normalized = normalize_statement(requirement.statement)

        # Allowed behaviors: derived from actor/action/resource if available
        allowed = []
        if requirement.actor and requirement.action and requirement.resource:
            b_desc = f"{requirement.actor.name} performs {requirement.action.name} on {requirement.resource.name}"
            allowed.append(BehaviorExpectation(
                behavior_id=generate_behavior_id(contract_id, b_desc),
                description=b_desc,
                actor=requirement.actor.name,
                action=requirement.action.name,
                resource=requirement.resource.name,
                expected_outcome="permitted",
                provenance=requirement.provenance,
            ))

        # Forbidden behaviors from Semantic IR
        forbidden = []
        for fb in requirement.forbidden_behaviors:
            forbidden.append(BehaviorExpectation(
                behavior_id=generate_behavior_id(contract_id, fb.statement),
                description=fb.statement,
                expected_outcome="denied",
                provenance=fb.provenance,
            ))

        # Invariants
        invariants = []
        if requirement.actor and requirement.action and requirement.resource:
            inv_stmt = (
                f"Every {requirement.action.name} of {requirement.resource.name} "
                f"must verify authorization before proceeding."
            )
            invariants.append(Invariant(
                invariant_id=generate_invariant_id(contract_id, inv_stmt),
                statement=inv_stmt,
                provenance=requirement.provenance,
                source_refs=list(requirement.sources),
            ))

        # Assumptions (preserved from Semantic IR)
        assumptions = [
            ContractAssumption(
                assumption_id=generate_assumption_id(contract_id, a.statement),
                statement=a.statement,
                provenance=a.provenance,
            )
            for a in requirement.assumptions
        ]

        # Verification targets (candidate pointers, not proof)
        targets = []
        if requirement.action and requirement.resource:
            desc = f"Verify {requirement.action.name} on {requirement.resource.name}"
            targets.append(VerificationTarget(
                target_id=generate_target_id(contract_id, desc),
                category=VerificationTargetCategory.BEHAVIOR,
                description=desc,
            ))

        # Code entity refs remain candidate references (not verified)
        # (passed through from Semantic IR code_entity_refs if needed in the future)

        contract = SemanticContract(
            contract_id=contract_id,
            requirement_id=requirement.requirement_id,
            candidate_id=requirement.candidate_id,
            analysis_id=requirement.analysis_id,
            statement=requirement.statement,
            source_refs=list(requirement.sources),
            provenance=requirement.provenance,
            allowed_behaviors=allowed,
            forbidden_behaviors=forbidden,
            preconditions=[p.statement for p in requirement.preconditions],
            postconditions=[p.statement for p in requirement.postconditions],
            invariants=invariants,
            assumptions=assumptions,
            verification_targets=targets,
            compilation_status=ContractStatus.READY,
            verification_state=VerificationState(
                intent=IntentState.HUMAN_CONFIRMED,
                implementation=ImplementationState.UNKNOWN,
                behavior=BehaviorState.UNKNOWN,
            ),
        )

        self.validator.validate(contract)
        return contract

    def _check_blocked(self, requirement: SemanticRequirement) -> str | None:
        """Returns a block_reason string if the requirement cannot be compiled, or None."""

        if requirement.verification_state.intent == IntentState.CANDIDATE:
            return "Requirement is still a CANDIDATE and has not been human-confirmed."

        if requirement.verification_state.intent == IntentState.CLARIFICATION_REQUIRED:
            return "Requirement requires human clarification before compilation."

        if requirement.verification_state.intent == IntentState.REJECTED:
            return "Requirement has been rejected and cannot be compiled."

        if not requirement.human_confirmed:
            return "Requirement has not been explicitly human-confirmed."

        return None
