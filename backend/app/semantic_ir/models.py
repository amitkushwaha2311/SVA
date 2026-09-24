"""
SVA Semantic IR Models
======================

Strongly typed intermediate representation models using Pydantic.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.repository.intent.models import CandidateStatus, Provenance, SourceLocation


class IntentState(str, Enum):
    CANDIDATE = "CANDIDATE"
    HUMAN_CONFIRMED = "HUMAN_CONFIRMED"
    REJECTED = "REJECTED"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"


class ImplementationState(str, Enum):
    UNKNOWN = "UNKNOWN"
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    STALE = "STALE"


class BehaviorState(str, Enum):
    UNKNOWN = "UNKNOWN"
    PROVEN = "PROVEN"
    SUPPORTED = "SUPPORTED"
    VIOLATED = "VIOLATED"
    INCONCLUSIVE = "INCONCLUSIVE"


class VerificationState(BaseModel):
    intent: IntentState = Field(default=IntentState.CANDIDATE)
    implementation: ImplementationState = Field(default=ImplementationState.UNKNOWN)
    behavior: BehaviorState = Field(default=BehaviorState.UNKNOWN)


class SemanticElement(BaseModel):
    """Base for generic semantic interpretation elements."""
    name: str
    source: str | None = None


class Actor(SemanticElement):
    pass


class Action(SemanticElement):
    pass


class Resource(SemanticElement):
    pass


class SemanticCondition(BaseModel):
    id: str
    statement: str
    provenance: Provenance
    source_refs: list[SourceLocation] = Field(default_factory=list)
    status: CandidateStatus = Field(default=CandidateStatus.CANDIDATE)


class Precondition(SemanticCondition):
    pass


class Postcondition(SemanticCondition):
    pass


class ForbiddenBehavior(SemanticCondition):
    pass


class Assumption(SemanticCondition):
    pass


class EvidenceRef(BaseModel):
    evidence_id: str
    evidence_type: str
    description: str


class CodeEntityRef(BaseModel):
    entity_id: str
    match_reason: str


class SemanticRequirement(BaseModel):
    """
    A strongly typed representation of an intent candidate.
    
    This is an interpretation, NOT proof of behavior.
    """
    requirement_id: str
    candidate_id: str
    analysis_id: str
    
    # Textual representation
    statement: str
    original_statement: str
    
    # Provenance mapping
    provenance: Provenance
    sources: list[SourceLocation] = Field(default_factory=list)
    
    # Human confirmation boundary
    status: CandidateStatus = Field(default=CandidateStatus.CANDIDATE)
    human_confirmed: bool = Field(default=False)
    
    # Semantic interpretations (often unknown)
    actor: Actor | None = None
    action: Action | None = None
    resource: Resource | None = None
    
    # Structured conditions
    preconditions: list[Precondition] = Field(default_factory=list)
    postconditions: list[Postcondition] = Field(default_factory=list)
    forbidden_behaviors: list[ForbiddenBehavior] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    
    interpretation_notes: str | None = None
    
    # References to evidence and code
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    code_entity_refs: list[CodeEntityRef] = Field(default_factory=list)
    
    # Explicit verification dimensions
    verification_state: VerificationState = Field(default_factory=VerificationState)
