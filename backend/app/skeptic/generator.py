"""
SVA Skeptic Generator
=====================

Orchestrates counterexample generation across all strategies.
Prevents duplicate scenarios using deterministic ID tracking.
"""

from __future__ import annotations

from app.contracts.models import SemanticContract
from app.evidence.ids import generate_obligation_id
from app.skeptic.models import (
    Counterexample,
    SkepticReport,
    SkepticStrategy,
    generate_counterexample_id,
)
from app.skeptic.strategies import (
    strategy_authorization_boundary,
    strategy_condition_flipping,
    strategy_input_boundary,
    strategy_negative_obligation_challenge,
    strategy_negative_space,
    strategy_resource_boundary,
    strategy_scope_boundary,
)

import hashlib


class SkepticGenerator:
    """
    Generates deterministic counterexample candidates for a SemanticContract.

    Operates completely independently of the Phase 10 Verifier.
    Cannot mutate SemanticContracts, verification state, or Evidence.
    """

    def generate(
        self,
        repository_id: str,
        contract: SemanticContract,
    ) -> SkepticReport:
        """
        Run all applicable strategies and return a de-duplicated SkepticReport.
        """
        seen_ids: set[str] = set()
        all_candidates: list[Counterexample] = []
        strategies_applied: set[SkepticStrategy] = set()

        # ── Positive behavior obligations ──────────────────────────────────
        for behavior in contract.allowed_behaviors:
            ob_id = generate_obligation_id(contract.contract_id, behavior.description)

            batches: list[list[Counterexample]] = [
                strategy_negative_space(repository_id, contract, behavior, ob_id),
                strategy_authorization_boundary(repository_id, contract, behavior, ob_id),
                strategy_input_boundary(repository_id, contract, behavior, ob_id),
                strategy_resource_boundary(repository_id, contract, behavior, ob_id),
                strategy_scope_boundary(repository_id, contract, behavior, ob_id),
                strategy_condition_flipping(repository_id, contract, behavior, ob_id),
            ]

            for batch in batches:
                for cx in batch:
                    if cx.counterexample_id not in seen_ids:
                        seen_ids.add(cx.counterexample_id)
                        all_candidates.append(cx)
                        strategies_applied.add(cx.strategy)

        # ── Negative/forbidden behavior obligations ────────────────────────
        for forbidden in contract.forbidden_behaviors:
            ob_id = generate_obligation_id(contract.contract_id, f"FORBIDDEN: {forbidden.description}")

            for cx in strategy_negative_obligation_challenge(repository_id, contract, forbidden, ob_id):
                if cx.counterexample_id not in seen_ids:
                    seen_ids.add(cx.counterexample_id)
                    all_candidates.append(cx)
                    strategies_applied.add(cx.strategy)

        # ── Phase 6 distinguishing scenarios (reuse if present) ────────────
        # SemanticContract does not currently carry distinguishing_scenarios directly.
        # Future integration point: when Phase 6 distinguishing scenarios are stored,
        # this block will convert them into DISTINGUISHING_SCENARIO counterexamples.
        # strategies_applied.add(SkepticStrategy.DISTINGUISHING_SCENARIO) when integrated.

        report_identity = hashlib.sha256(
            f"{repository_id}:{contract.contract_id}".encode()
        ).hexdigest()

        return SkepticReport(
            report_id=report_identity,
            requirement_id=contract.requirement_id,
            contract_id=contract.contract_id,
            counterexamples=all_candidates,
            total_generated=len(all_candidates),
            total_deduplicated=len(seen_ids),
            strategies_applied=sorted(strategies_applied),
        )
