"""
SVA Skeptic Models
==================

Strongly typed models for the Counterexample & Skeptic Engine.

A Counterexample is a HYPOTHESIS, not a VIOLATION.
Only valid Phase 8 Evidence can establish a violation.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CounterexampleStatus(str, Enum):
    """
    Lifecycle states for a counterexample.

    PROPOSED   — A hypothesis has been generated but not yet validated or executed.
    VALIDATED  — The scenario is structurally sound and ready for execution planning.
    EXECUTED   — An execution attempt was made (result not yet fully assessed).
    CONFIRMED  — Valid evidence has established the violation the counterexample predicted.
    REFUTED    — Valid evidence has proven the counterexample hypothesis is false.
    INCONCLUSIVE — Execution or evidence is inconclusive.
    UNSUPPORTED  — Execution environment cannot support this scenario (Phase 9 fail-closed).
    REJECTED   — The counterexample was structurally invalid or not applicable.
    """
    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    EXECUTED = "EXECUTED"
    CONFIRMED = "CONFIRMED"
    REFUTED = "REFUTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    UNSUPPORTED = "UNSUPPORTED"
    REJECTED = "REJECTED"


class CounterexamplePriority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class SkepticStrategy(str, Enum):
    NEGATIVE_SPACE = "NEGATIVE_SPACE"
    AUTHORIZATION_BOUNDARY = "AUTHORIZATION_BOUNDARY"
    INPUT_BOUNDARY = "INPUT_BOUNDARY"
    RESOURCE_BOUNDARY = "RESOURCE_BOUNDARY"
    SCOPE_BOUNDARY = "SCOPE_BOUNDARY"
    CONDITION_FLIPPING = "CONDITION_FLIPPING"
    NEGATIVE_OBLIGATION_CHALLENGE = "NEGATIVE_OBLIGATION_CHALLENGE"
    DISTINGUISHING_SCENARIO = "DISTINGUISHING_SCENARIO"


class CounterexampleActor(BaseModel):
    """Represents the actor in a counterexample scenario."""
    role: str
    is_authenticated: bool = True
    is_owner: bool = False
    additional_context: dict[str, Any] = Field(default_factory=dict)


class Counterexample(BaseModel):
    """
    A strongly typed counterexample hypothesis.

    IMPORTANT: A Counterexample is PROPOSED only. It is NOT evidence.
    It must NEVER automatically create VIOLATED verification state.
    Only Phase 8 Evidence + Phase 10 Verifier can establish violations.
    """
    counterexample_id: str
    requirement_id: str
    contract_id: str
    obligation_id: str
    target_id: str | None = None

    # Optional linkage to Phase 6 distinguishing scenario
    scenario_id: str | None = None

    # The hypothesis being tested
    hypothesis: str
    preconditions: list[str] = Field(default_factory=list)

    # Scenario components
    actor: CounterexampleActor
    action: str
    resource: str

    # Expected vs violating behavior
    expected_behavior: str   # What the contract requires
    violating_behavior: str  # What would violate it

    # Strategy and provenance
    strategy: SkepticStrategy
    priority: CounterexamplePriority = CounterexamplePriority.MEDIUM
    priority_reason: str = ""

    # Lifecycle
    status: CounterexampleStatus = CounterexampleStatus.PROPOSED
    evidence_refs: list[str] = Field(default_factory=list)

    # Generation metadata
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    generation_method: str = "RULE_BASED_DETERMINISTIC"

    # Assumptions that must hold for this counterexample to be valid
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class SkepticReport(BaseModel):
    """Report produced by the Skeptic Engine for a single contract."""
    report_id: str
    requirement_id: str
    contract_id: str
    counterexamples: list[Counterexample] = Field(default_factory=list)
    total_generated: int = 0
    total_deduplicated: int = 0
    strategies_applied: list[SkepticStrategy] = Field(default_factory=list)
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def generate_counterexample_id(
    repository_id: str,
    contract_id: str,
    obligation_id: str,
    strategy: str,
    canonical_scenario: str,
) -> str:
    """
    Deterministic SHA-256 identity.
    Timestamps are excluded to ensure reproducibility.
    """
    identity = "|".join([
        repository_id,
        contract_id,
        obligation_id,
        strategy,
        canonical_scenario,
    ])
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()
