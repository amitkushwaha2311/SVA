"""
SVA Semantic Verifier
=====================

Core engine that evaluates evidence against SemanticContracts.
"""

from app.contracts.models import ContractStatus, SemanticContract, VerificationTargetCategory
from app.evidence.ids import generate_obligation_id
from app.evidence.models import Evidence, VerificationState
from app.verification.aggregator import RequirementAggregator
from app.verification.explain import generate_obligation_explanation, generate_requirement_explanation
from app.verification.models import ObligationVerification, RequirementVerification
from app.verification.rules import EvidenceValidityFilter, ObligationEvaluator


class SemanticVerifier:
    """Evaluates evidence against a compiled SemanticContract."""
    
    def __init__(self) -> None:
        self.filter = EvidenceValidityFilter()
        self.evaluator = ObligationEvaluator()
        self.aggregator = RequirementAggregator()

    def verify(
        self,
        repository_id: str,
        commit_id: str,
        contract: SemanticContract,
        available_evidence: list[Evidence],
    ) -> RequirementVerification:
        """
        Verify a contract against available evidence.
        """
        # Ambiguity / Confirmation Gate
        if contract.compilation_status != ContractStatus.READY:
            return RequirementVerification(
                requirement_id=contract.requirement_id,
                contract_id=contract.contract_id,
                decision=VerificationState.UNKNOWN,
                explanation=f"Requirement cannot be verified because contract status is {contract.compilation_status.value}.",
                limitations=["Contract is blocked or unconfirmed. Resolve ambiguity first."]
            )

        obligation_results: list[ObligationVerification] = []

        all_obligations = []
        for b in contract.allowed_behaviors:
            ob_id = generate_obligation_id(contract.contract_id, b.description)
            all_obligations.append((ob_id, b))
            
        for fb in contract.forbidden_behaviors:
            ob_id = generate_obligation_id(contract.contract_id, f"FORBIDDEN: {fb.description}")
            all_obligations.append((ob_id, fb))

        # We need to filter evidence specific to this contract.
        contract_evidence = [e for e in available_evidence if e.contract_id == contract.contract_id]
        
        valid_ev, stale_ev, invalid_ev = self.filter.filter_valid_evidence(
            contract_evidence, repository_id, commit_id
        )

        for ob_id, behavior in all_obligations:
            # Build explicit, validated target mapping for THIS specific obligation:
            # 1. Target directly stores this obligation_id
            # 2. Or target category is BEHAVIOR and its action/resource matches this behavior
            # 3. Or target description explicitly matches this behavior
            mapped_target_ids = {
                t.target_id for t in contract.verification_targets
                if getattr(t, "obligation_id", None) == ob_id
                or (
                    t.category == VerificationTargetCategory.BEHAVIOR
                    and behavior.action
                    and behavior.resource
                    and t.description == f"Verify {behavior.action} on {behavior.resource}"
                )
                or (
                    t.category == VerificationTargetCategory.BEHAVIOR
                    and t.description in (f"Verify {behavior.description}", behavior.description)
                )
            }

            # Associate evidence with this obligation:
            # 1. Prefer exact obligation_id match.
            # 2. Otherwise use explicit, validated mapping between specific verification target and obligation.
            # 3. For targetless/obligationless evidence, fall back to exact behavior description match.
            ob_valid = []
            for e in valid_ev:
                if getattr(e, "obligation_id", None) is not None:
                    if e.obligation_id == ob_id:
                        ob_valid.append(e)
                elif e.target_refs:
                    if any(t_id in mapped_target_ids for t_id in e.target_refs):
                        ob_valid.append(e)
                else:
                    if e.description in (behavior.description, f"FORBIDDEN: {behavior.description}"):
                        ob_valid.append(e)

            decision, supporting, contradicting = self.evaluator.evaluate(behavior, ob_valid)


            explanation = generate_obligation_explanation(
                obligation_id=ob_id,
                decision=decision,
                supporting=supporting,
                contradicting=contradicting,
                stale=stale_ev,
                invalid=invalid_ev,
            )

            # Check if there are assumptions
            limitations = []
            if contract.assumptions:
                limitations.append("Contract relies on assumptions that are not independently verified.")

            obligation_results.append(
                ObligationVerification(
                    obligation_id=ob_id,
                    contract_id=contract.contract_id,
                    requirement_id=contract.requirement_id,
                    decision=decision,
                    evidence_refs=[e.evidence_id for e in ob_valid],
                    supporting_evidence=[e.evidence_id for e in supporting],
                    contradicting_evidence=[e.evidence_id for e in contradicting],
                    explanation=explanation,
                    limitations=limitations,
                )
            )

        # Aggregate
        overall_decision = self.aggregator.aggregate(obligation_results)
        
        unresolved = [o.obligation_id for o in obligation_results if o.decision not in (VerificationState.PROVEN, VerificationState.SUPPORTED)]
        
        explanation = generate_requirement_explanation(
            requirement_id=contract.requirement_id,
            decision=overall_decision,
            total_obligations=len(obligation_results),
            proven=len([o for o in obligation_results if o.decision == VerificationState.PROVEN]),
            violated=len([o for o in obligation_results if o.decision == VerificationState.VIOLATED]),
            unresolved=len(unresolved),
        )

        return RequirementVerification(
            requirement_id=contract.requirement_id,
            contract_id=contract.contract_id,
            decision=overall_decision,
            obligation_results=obligation_results,
            evidence_refs=[e.evidence_id for e in contract_evidence],
            explanation=explanation,
            unresolved_obligations=unresolved,
            limitations=["Phase 9 Sandbox is UNSUPPORTED; runtime verification relies on static/external evidence."] if not valid_ev else []
        )
