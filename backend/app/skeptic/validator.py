"""
SVA Skeptic Validator
=====================

Validates the structural soundness of generated counterexamples.
Ensures they are properly linked and do NOT mutate verification state.
"""

from __future__ import annotations

from app.contracts.models import ContractStatus, SemanticContract
from app.skeptic.models import Counterexample, CounterexampleStatus


class CounterexampleValidationError(ValueError):
    """Raised when a counterexample fails structural validation."""
    pass


class CounterexampleValidator:
    """Validates counterexample candidates before they enter the pipeline."""

    def validate(
        self,
        counterexample: Counterexample,
        contract: SemanticContract,
    ) -> None:
        """
        Validate structural soundness.
        Raises CounterexampleValidationError on any violation.
        """
        # 1. Contract linkage
        if counterexample.contract_id != contract.contract_id:
            raise CounterexampleValidationError(
                f"Counterexample {counterexample.counterexample_id} links to contract "
                f"'{counterexample.contract_id}' but was validated against '{contract.contract_id}'."
            )

        # 2. Requirement linkage
        if counterexample.requirement_id != contract.requirement_id:
            raise CounterexampleValidationError(
                f"Counterexample {counterexample.counterexample_id} links to requirement "
                f"'{counterexample.requirement_id}' but contract requires '{contract.requirement_id}'."
            )

        # 3. Must start as PROPOSED — cannot be CONFIRMED/VIOLATED without evidence
        if counterexample.status in (CounterexampleStatus.CONFIRMED,):
            raise CounterexampleValidationError(
                f"Counterexample {counterexample.counterexample_id} cannot be CONFIRMED "
                "without Phase 8 Evidence. It must remain PROPOSED until evidence establishes this."
            )

        # 4. Hypothesis must not be empty
        if not counterexample.hypothesis.strip():
            raise CounterexampleValidationError(
                f"Counterexample {counterexample.counterexample_id} has an empty hypothesis."
            )

        # 5. Expected and violating behavior must be distinct
        if counterexample.expected_behavior.strip() == counterexample.violating_behavior.strip():
            raise CounterexampleValidationError(
                f"Counterexample {counterexample.counterexample_id}: expected_behavior and "
                "violating_behavior must be distinct."
            )

        # 6. Blocked/rejected contracts should not accept counterexamples for execution
        # (they can still be generated as hypotheses, but should be marked REJECTED)
        if contract.compilation_status == ContractStatus.BLOCKED:
            if counterexample.status not in (CounterexampleStatus.PROPOSED, CounterexampleStatus.REJECTED):
                raise CounterexampleValidationError(
                    f"Counterexample {counterexample.counterexample_id} cannot be validated/executed "
                    "because the contract is BLOCKED."
                )

        # 7. Deterministic ID must not contain timestamps (checked by format length only here)
        if not counterexample.counterexample_id or len(counterexample.counterexample_id) != 64:
            raise CounterexampleValidationError(
                f"Counterexample has non-standard ID '{counterexample.counterexample_id}'. "
                "Expected a 64-char SHA-256 hex digest."
            )
