"""
SVA Semantic Verifier
=====================

Core engine that evaluates evidence against SemanticContracts.
"""

from app.contracts.models import ContractStatus, SemanticContract
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

        # We collect all obligations (positive, negative, invariants)
        # Note: In Phase 8/9, we used generate_obligation_id based on behavior descriptions.
        
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
            # Evidence matching this obligation (in Phase 9, ExecutionRequest links target/contract, 
            # ideally the evidence is linked to obligation_id. For now, since Phase 8 captures evidence
            # with description / target_id, we just evaluate all valid evidence for this contract.
            # In a robust implementation, evidence would have `obligation_id`).
            # We assume valid_ev is the subset of evidence relevant to THIS obligation.
            # We filter it by assuming evidence description or some target ref links it, 
            # but to keep it simple and deterministic for Phase 10: we pass valid_ev and let rules evaluate.
            
            # To strictly separate positive/negative in this mockup without breaking Phase 8:
            # We simulate filtering by `expected_outcome` if evidence carried it, or by test intent.
            # For this Phase, we'll assume the caller passes the right evidence list per obligation,
            # or we evaluate based on a mock matching. 
            # Let's say evidence descriptions distinguish them.
            
            # Match evidence to obligation (naive matching for foundation)
            # In a robust implementation, evidence would carry the explicit obligation_id.
            ob_valid = [e for e in valid_ev if behavior.description in e.description or (behavior.action and behavior.action in e.description)]

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
