"""
SVA Evidence Verifier
=====================

Aggregates evidence into obligation-level and contract-level results.
"""

from app.evidence.ids import generate_obligation_id
from app.evidence.models import (
    Evidence,
    EvidenceResult,
    EvidenceType,
    ObligationResult,
    VerificationResult,
    VerificationState,
    VERIFICATION_LADDER,
)
from app.contracts.models import SemanticContract


# Minimum evidence type index on the ladder required to claim PROVEN
# DETERMINISTIC_TEST (index 6) is required for PROVEN.
_PROVEN_THRESHOLD = VERIFICATION_LADDER.index(EvidenceType.DETERMINISTIC_TEST)


def _evidence_ladder_level(evidence: Evidence) -> int:
    try:
        return VERIFICATION_LADDER.index(evidence.evidence_type)
    except ValueError:
        return -1


def _aggregate_state(evidence_list: list[Evidence]) -> VerificationState:
    """
    Conservatively aggregate evidence into a verification state.

    Rules:
    - Any FAIL → VIOLATED
    - PASS from sufficiently strong evidence (>= DETERMINISTIC_TEST) → PROVEN
    - PASS from weaker evidence → SUPPORTED
    - All INCONCLUSIVE/NOT_RUN → UNKNOWN
    """
    if not evidence_list:
        return VerificationState.UNKNOWN

    results = [e.result for e in evidence_list]

    if EvidenceResult.FAIL in results:
        return VerificationState.VIOLATED

    passing = [e for e in evidence_list if e.result == EvidenceResult.PASS]
    if passing:
        max_level = max(_evidence_ladder_level(e) for e in passing)
        if max_level >= _PROVEN_THRESHOLD:
            return VerificationState.PROVEN
        return VerificationState.SUPPORTED

    inconclusive = [e for e in evidence_list if e.result in (
        EvidenceResult.INCONCLUSIVE, EvidenceResult.ERROR
    )]
    if inconclusive:
        return VerificationState.INCONCLUSIVE

    return VerificationState.UNKNOWN


class EvidenceVerifier:
    """Aggregates evidence into structured obligation and contract results."""

    def verify_contract(
        self,
        contract: SemanticContract,
        evidence: list[Evidence],
    ) -> VerificationResult:
        """
        Produce a VerificationResult for an entire contract.

        Does NOT collapse obligations into a single boolean.
        """
        obligation_results: list[ObligationResult] = []

        # Positive obligations (allowed behaviors)
        for behavior in contract.allowed_behaviors:
            ob_id = generate_obligation_id(contract.contract_id, behavior.description)
            relevant = [
                e for e in evidence if e.contract_id == contract.contract_id
            ]
            obligation_results.append(ObligationResult(
                obligation_id=ob_id,
                description=f"POSITIVE: {behavior.description}",
                state=_aggregate_state(relevant),
                evidence_ids=[e.evidence_id for e in relevant],
            ))

        # Negative obligations (forbidden behaviors)
        for fb in contract.forbidden_behaviors:
            ob_id = generate_obligation_id(contract.contract_id, f"FORBIDDEN: {fb.description}")
            # Negative obligations require their own dedicated evidence; cannot reuse positive
            obligation_results.append(ObligationResult(
                obligation_id=ob_id,
                description=f"FORBIDDEN: {fb.description}",
                state=VerificationState.UNKNOWN,  # No dedicated negative evidence collected yet
                evidence_ids=[],
                notes=(
                    "Negative obligation requires dedicated evidence. "
                    "Positive test PASS does NOT establish negative behavior."
                ),
            ))

        # Contract-level state: most conservative aggregation
        all_states = [o.state for o in obligation_results]

        if VerificationState.VIOLATED in all_states:
            contract_state = VerificationState.VIOLATED
        elif VerificationState.UNKNOWN in all_states:
            contract_state = VerificationState.UNKNOWN
        elif all_states and all(s == VerificationState.PROVEN for s in all_states):
            contract_state = VerificationState.PROVEN
        elif VerificationState.SUPPORTED in all_states or VerificationState.PROVEN in all_states:
            contract_state = VerificationState.SUPPORTED
        else:
            contract_state = VerificationState.INCONCLUSIVE

        return VerificationResult(
            contract_id=contract.contract_id,
            requirement_id=contract.requirement_id,
            state=contract_state,
            evidence_ids=[e.evidence_id for e in evidence],
            obligation_results=obligation_results,
            explanation=(
                f"{len(obligation_results)} obligation(s) evaluated. "
                f"Final state: {contract_state.value}. "
                f"Code mapping evidence is CANDIDATE-level (not proof of behavior)."
            ),
        )
