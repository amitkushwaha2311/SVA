"""
SVA Semantic CI Manager
=======================

Determines the overall Semantic CI action state (PASS, REVIEW, BLOCK).
These are CI action states, NOT verification truth states.
"""

from __future__ import annotations

from app.drift.models import (
    ChangeRecord,
    DriftType,
    InvalidationRecord,
    SemanticCIDecision,
    SemanticCIResult,
    SemanticImpact,
)
from app.evidence.models import VerificationState
from app.verification.models import RequirementVerification


class SemanticCIManager:
    """Evaluates CI action states based on deterministic policy."""

    def decide(
        self,
        changes: list[ChangeRecord],
        impacts: list[SemanticImpact],
        invalidations: list[InvalidationRecord],
        verifications: list[RequirementVerification],
    ) -> SemanticCIResult:
        """
        Evaluate all drift findings to produce a single Semantic CI result.
        """
        if not changes:
            return SemanticCIResult(decision=SemanticCIDecision.PASS, reason="No changes detected.")

        reasons = []
        decision = SemanticCIDecision.PASS
        affected_reqs = set()
        
        # Maps requirement_id -> verification state
        ver_map = {vr.requirement_id: vr.decision for vr in verifications}

        # 1. Evaluate Changes
        for change in changes:
            if change.drift_type in (DriftType.TEXTUAL, DriftType.DOCUMENTATION):
                # Textual changes might be PASS unless they have impacts
                pass
                
            elif change.drift_type == DriftType.INTENT:
                decision = self._escalate(decision, SemanticCIDecision.REVIEW)
                reasons.append(f"Intent source changed in {change.file_path}. Review required.")
                
            elif change.drift_type == DriftType.CONTRACT:
                decision = self._escalate(decision, SemanticCIDecision.REVIEW)
                reasons.append(f"Semantic contract affected by changes in {change.file_path}.")
                
            elif change.drift_type == DriftType.UNKNOWN:
                decision = self._escalate(decision, SemanticCIDecision.REVIEW)
                reasons.append(f"Unknown drift type for {change.file_path}. Review required.")

        # 2. Evaluate Impacts
        for impact in impacts:
            if impact.impact_type == "UNKNOWN_RELATIONSHIP":
                decision = self._escalate(decision, SemanticCIDecision.REVIEW)
                reasons.append(f"Unknown relationship impact: {impact.reason}")
                
            affected_reqs.update(impact.affected_requirements)
            
            for req_id in impact.affected_requirements:
                state = ver_map.get(req_id, VerificationState.UNKNOWN)
                
                if state in (VerificationState.PROVEN, VerificationState.SUPPORTED):
                    decision = self._escalate(decision, SemanticCIDecision.REVIEW)
                    reasons.append(f"Verified requirement {req_id} ({state.value}) is affected by changes. Re-verification recommended.")
                    
                elif state == VerificationState.VIOLATED:
                    # Known confirmed violation that is still present (and possibly affected)
                    # We block because an explicitly known violation exists.
                    decision = self._escalate(decision, SemanticCIDecision.BLOCK)
                    reasons.append(f"Requirement {req_id} has a confirmed VIOLATED state. Fix required before proceeding.")

        # 3. Handle Configuration rule (Correction 1)
        config_changes = [c for c in changes if c.drift_type == DriftType.CONFIGURATION]
        for config_change in config_changes:
            # Did this config change generate any explicit impacts?
            has_impacts = any(imp.change_id == config_change.change_id for imp in impacts)
            if has_impacts:
                decision = self._escalate(decision, SemanticCIDecision.REVIEW)
                reasons.append(f"Configuration change in {config_change.file_path} affects assurance relationships.")
            # If no impacts, it remains PASS (unless escalated by something else)

        # 4. Handle Entity-level Unknown (Correction 2)
        unknown_entity_changes = [c for c in changes if c.entity_id and c.drift_type == DriftType.UNKNOWN]
        if unknown_entity_changes:
             decision = self._escalate(decision, SemanticCIDecision.REVIEW)
             reasons.append("Entity-level modifications could not be deterministically compared.")

        if decision == SemanticCIDecision.PASS:
            if not reasons:
                reasons.append("All changes are structurally safe or have no assurance impact.")

        return SemanticCIResult(
            decision=decision,
            reason=" | ".join(set(reasons)),
            affected_assurance_ids=sorted(list(affected_reqs)),
            re_verification_required=sorted(list(affected_reqs)) if decision != SemanticCIDecision.PASS else [],
        )

    def _escalate(self, current: SemanticCIDecision, new: SemanticCIDecision) -> SemanticCIDecision:
        """Helper to safely escalate severity (PASS -> REVIEW -> BLOCK)."""
        order = {SemanticCIDecision.PASS: 0, SemanticCIDecision.REVIEW: 1, SemanticCIDecision.BLOCK: 2}
        if order[new] > order[current]:
            return new
        return current
