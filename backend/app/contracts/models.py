"""
SVA Semantic Contract Models
============================

Strongly typed models for the Semantic Contract Compiler.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.repository.intent.models import Provenance, SourceLocation
from app.semantic_ir.models import (
    BehaviorState,
    ImplementationState,
    IntentState,
    VerificationState,
)


class ContractStatus(str, Enum):
    """Compilation status of a semantic contract."""
    DRAFT = "DRAFT"
    READY = "READY"
    BLOCKED = "BLOCKED"
    SUPERSEDED = "SUPERSEDED"


class VerificationTargetCategory(str, Enum):
    API_ENDPOINT = "API_ENDPOINT"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    DATABASE_OPERATION = "DATABASE_OPERATION"
    USER_FLOW = "USER_FLOW"
    BEHAVIOR = "BEHAVIOR"
    POLICY = "POLICY"


class BehaviorExpectation(BaseModel):
    """An expected (allowed or forbidden) behavioral obligation."""
    behavior_id: str
    description: str
    actor: str | None = None
    action: str | None = None
    resource: str | None = None
    expected_outcome: str | None = None
    provenance: Provenance = Provenance.DEFAULT


class Invariant(BaseModel):
    """A structural invariant that must hold in all cases."""
    invariant_id: str
    statement: str
    provenance: Provenance = Provenance.DEFAULT
    source_refs: list[SourceLocation] = Field(default_factory=list)


class ContractAssumption(BaseModel):
    """An explicit assumption the contract depends on but does not verify."""
    assumption_id: str
    statement: str
    provenance: Provenance = Provenance.DEFAULT


class VerificationTarget(BaseModel):
    """
    A potential future verification target.

    A target is NOT proof. It is a pointer to where evidence
    could be collected later.
    """
    target_id: str
    category: VerificationTargetCategory
    description: str
    code_entity_ref: str | None = None  # Candidate Phase-3 entity ID, NOT verified match


class SemanticContract(BaseModel):
    """
    A structured semantic contract derived from a confirmed SemanticRequirement.

    Defines what satisfaction would mean.
    Does NOT claim the implementation satisfies this.
    """
    contract_id: str
    contract_version: str = "1"
    parent_contract_id: str | None = None

    requirement_id: str
    candidate_id: str
    analysis_id: str

    statement: str
    source_refs: list[SourceLocation] = Field(default_factory=list)
    provenance: Provenance = Provenance.DEFAULT

    # Semantic structure
    allowed_behaviors: list[BehaviorExpectation] = Field(default_factory=list)
    forbidden_behaviors: list[BehaviorExpectation] = Field(default_factory=list)
    preconditions: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    invariants: list[Invariant] = Field(default_factory=list)
    assumptions: list[ContractAssumption] = Field(default_factory=list)

    # Verification metadata
    verification_targets: list[VerificationTarget] = Field(default_factory=list)

    # Compilation result
    compilation_status: ContractStatus = ContractStatus.DRAFT
    block_reason: str | None = None

    # Verification states (always UNKNOWN at compile time)
    verification_state: VerificationState = Field(
        default_factory=lambda: VerificationState(
            intent=IntentState.HUMAN_CONFIRMED,
            implementation=ImplementationState.UNKNOWN,
            behavior=BehaviorState.UNKNOWN,
        )
    )
