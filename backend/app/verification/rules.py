"""
SVA Verification Rules
======================

Filters valid evidence and computes verification decisions based on Phase 8 semantics.
"""

from app.evidence.integrity import verify_evidence_hash
from app.evidence.models import (
    Evidence,
    EvidenceResult,
    EvidenceStatus,
    EvidenceType,
    VerificationState,
    VERIFICATION_LADDER
)
from app.contracts.models import BehaviorExpectation

# Phase 8 threshold for PROVEN
_PROVEN_THRESHOLD = VERIFICATION_LADDER.index(EvidenceType.DETERMINISTIC_TEST)

def _evidence_ladder_level(evidence: Evidence) -> int:
    try:
        return VERIFICATION_LADDER.index(evidence.evidence_type)
    except ValueError:
        return -1


class EvidenceValidityFilter:
    """Filters evidence for validity against current verification context."""

    def filter_valid_evidence(
        self,
        evidence_list: list[Evidence],
        repository_id: str,
        commit_id: str,
    ) -> tuple[list[Evidence], list[Evidence], list[Evidence]]:
        """
        Returns (valid_evidence, stale_evidence, invalid_evidence).
        """
        valid = []
        stale = []
        invalid = []

        for ev in evidence_list:
            # 1. Invalid Integrity
            if ev.integrity is not None and not verify_evidence_hash(ev):
                invalid.append(ev)
                continue
            
            # 2. Wrong Repository -> Invalid
            if ev.repository_id != repository_id:
                invalid.append(ev)
                continue
            
            # 3. Wrong Commit -> Stale
            if ev.commit_id != commit_id:
                stale.append(ev)
                continue
            
            # 4. Invalidated state -> Invalid
            if ev.status == EvidenceStatus.INVALIDATED:
                invalid.append(ev)
                continue

            valid.append(ev)

        return valid, stale, invalid


class ObligationEvaluator:
    """Evaluates valid evidence to reach a deterministic decision."""

    def evaluate(
        self,
        obligation: BehaviorExpectation,
        valid_evidence: list[Evidence],
    ) -> tuple[VerificationState, list[Evidence], list[Evidence]]:
        """
        Returns (decision, supporting_evidence, contradicting_evidence).
        
        Evaluates evidence matching this obligation's intent.
        Positive obligation (expected_outcome="permitted"): PASS supports, FAIL contradicts.
        Negative obligation (expected_outcome="denied"): PASS supports, FAIL contradicts (assuming PASS means the denied behavior test passed, i.e., access was actually denied).
        """
        
        # We assume evidence is already filtered to only include evidence meant for THIS obligation.
        # This implies that the caller correctly matched `evidence.contract_id` and obligation targets.
        
        if not valid_evidence:
            return VerificationState.UNKNOWN, [], []

        supporting = []
        contradicting = []
        inconclusive = []

        for ev in valid_evidence:
            if ev.result == EvidenceResult.PASS:
                supporting.append(ev)
            elif ev.result == EvidenceResult.FAIL:
                contradicting.append(ev)
            elif ev.result in (EvidenceResult.INCONCLUSIVE, EvidenceResult.ERROR):
                inconclusive.append(ev)
            elif ev.result == EvidenceResult.NOT_RUN:
                # UNSUPPORTED execution translates to NOT_RUN
                pass

        if contradicting:
            return VerificationState.VIOLATED, supporting, contradicting

        if supporting:
            # Check strength
            max_level = max(_evidence_ladder_level(e) for e in supporting)
            if max_level >= _PROVEN_THRESHOLD:
                return VerificationState.PROVEN, supporting, contradicting
            return VerificationState.SUPPORTED, supporting, contradicting

        if inconclusive:
            return VerificationState.INCONCLUSIVE, supporting, contradicting

        return VerificationState.UNKNOWN, supporting, contradicting
