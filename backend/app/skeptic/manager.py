"""
SVA Skeptic Manager
===================

Manages counterexample prioritization and Phase 9/10 integration semantics.

Does NOT mutate Phase 10 verification state or Phase 8 Evidence.
"""

from __future__ import annotations

from app.contracts.models import ContractStatus, SemanticContract
from app.evidence.models import VerificationState
from app.skeptic.models import (
    Counterexample,
    CounterexamplePriority,
    CounterexampleStatus,
    SkepticReport,
    SkepticStrategy,
)
from app.verification.models import ObligationVerification


class SkepticManager:
    """
    Prioritizes counterexamples and applies Phase 9 / Phase 10 integration semantics.
    """

    def prioritize(
        self,
        report: SkepticReport,
        obligation_results: list[ObligationVerification] | None = None,
    ) -> SkepticReport:
        """
        Apply deterministic, rule-based prioritization to counterexamples in the report.
        """
        obligation_state_map: dict[str, VerificationState] = {}
        if obligation_results:
            for ob in obligation_results:
                obligation_state_map[ob.obligation_id] = ob.decision

        updated = []
        for cx in report.counterexamples:
            cx = cx.model_copy()
            ob_state = obligation_state_map.get(cx.obligation_id)

            # Rule 1: If the obligation is PROVEN, the Skeptic should challenge it → HIGH
            if ob_state == VerificationState.PROVEN:
                if cx.strategy in (SkepticStrategy.AUTHORIZATION_BOUNDARY, SkepticStrategy.NEGATIVE_OBLIGATION_CHALLENGE):
                    cx.priority = CounterexamplePriority.HIGH
                    cx.priority_reason = "Obligation is PROVEN but no negative evidence has been independently tested."

            # Rule 2: If the obligation is UNKNOWN and strategy is negative space → HIGH
            elif ob_state == VerificationState.UNKNOWN:
                if cx.strategy == SkepticStrategy.NEGATIVE_SPACE:
                    cx.priority = CounterexamplePriority.HIGH
                    cx.priority_reason = "No evidence for this obligation — negative-space challenge is critical."

            # Rule 3: Already VIOLATED — still worth surfacing but lower urgency
            elif ob_state == VerificationState.VIOLATED:
                cx.priority = CounterexamplePriority.LOW
                cx.priority_reason = "Obligation is already VIOLATED; counterexample confirms existing violation."

            updated.append(cx)

        # Sort by priority: HIGH → MEDIUM → LOW
        priority_order = {
            CounterexamplePriority.HIGH: 0,
            CounterexamplePriority.MEDIUM: 1,
            CounterexamplePriority.LOW: 2,
        }
        updated.sort(key=lambda cx: priority_order[cx.priority])

        return report.model_copy(update={"counterexamples": updated})

    def apply_phase9_unsupported(
        self,
        counterexample: Counterexample,
    ) -> Counterexample:
        """
        If Phase 9 returns UNSUPPORTED for this counterexample's execution,
        mark it UNSUPPORTED — never REFUTED and never CONFIRMED/VIOLATED.
        """
        if counterexample.status == CounterexampleStatus.EXECUTED:
            return counterexample.model_copy(update={
                "status": CounterexampleStatus.UNSUPPORTED,
                "limitations": counterexample.limitations + [
                    "Execution was UNSUPPORTED by the Phase 9 Sandbox. "
                    "This counterexample remains unresolved and does not constitute disproof."
                ],
            })
        return counterexample

    def challenge_proven_obligations(
        self,
        report: SkepticReport,
        obligation_results: list[ObligationVerification],
    ) -> list[Counterexample]:
        """
        Specifically surface counterexamples that challenge PROVEN obligations.
        """
        proven_ids = {
            ob.obligation_id
            for ob in obligation_results
            if ob.decision == VerificationState.PROVEN
        }
        return [
            cx for cx in report.counterexamples
            if cx.obligation_id in proven_ids and cx.priority == CounterexamplePriority.HIGH
        ]
