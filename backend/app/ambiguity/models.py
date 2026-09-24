"""
SVA Ambiguity Engine Models
===========================

Strongly typed models for detecting, tracking, and resolving ambiguities.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.repository.intent.models import Provenance


class AmbiguityType(str, Enum):
    ACTOR = "ACTOR"
    ACTION = "ACTION"
    RESOURCE = "RESOURCE"
    SCOPE = "SCOPE"
    CONDITION = "CONDITION"
    AUTHORIZATION = "AUTHORIZATION"
    TEMPORAL = "TEMPORAL"
    QUANTITY = "QUANTITY"
    OPTIONALITY = "OPTIONALITY"
    BEHAVIOR = "BEHAVIOR"
    TERMINOLOGY = "TERMINOLOGY"
    CONTRADICTION = "CONTRADICTION"
    UNKNOWN = "UNKNOWN"


class InterpretationStatus(str, Enum):
    PROPOSED = "PROPOSED"
    HUMAN_SELECTED = "HUMAN_SELECTED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class ClarificationStatus(str, Enum):
    OPEN = "OPEN"
    HUMAN_CONFIRMED = "HUMAN_CONFIRMED"


class Interpretation(BaseModel):
    """
    A proposed interpretation of an ambiguous requirement.
    NOT a verified requirement.
    """
    interpretation_id: str
    requirement_id: str | None = None  # Could apply to multiple or one
    statement: str
    semantic_fields: dict[str, Any] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    
    provenance: Provenance = Field(default=Provenance.AI_INFERENCE)
    interpretation_method: str = Field(default="RULE_BASED")
    status: InterpretationStatus = Field(default=InterpretationStatus.PROPOSED)


class DistinguishingScenario(BaseModel):
    """
    A minimal semantic scenario that distinguishes competing interpretations.
    """
    scenario_id: str
    description: str
    expected_outcomes: dict[str, str] = Field(default_factory=dict)  # interpretation_id -> outcome


class QuestionOption(BaseModel):
    option_id: str
    text: str
    maps_to_interpretation_id: str | None = None


class ClarificationQuestion(BaseModel):
    """
    A minimal, decision-oriented question to resolve an ambiguity.
    """
    question_id: str
    ambiguity_id: str
    question: str
    options: list[QuestionOption] = Field(default_factory=list)
    distinguishing_scenario_id: str | None = None
    information_gain: float = 0.0
    status: ClarificationStatus = Field(default=ClarificationStatus.OPEN)


class AmbiguityCase(BaseModel):
    """
    Tracks an instance of ambiguity detected in the Semantic IR.
    """
    ambiguity_id: str
    requirement_ids: list[str] = Field(default_factory=list)
    candidate_ids: list[str] = Field(default_factory=list)
    
    statement: str
    ambiguity_types: list[AmbiguityType] = Field(default_factory=list)
    
    interpretations: list[Interpretation] = Field(default_factory=list)
    distinguishing_scenarios: list[DistinguishingScenario] = Field(default_factory=list)
    clarification_question: ClarificationQuestion | None = None
    
    resolution_status: ClarificationStatus = Field(default=ClarificationStatus.OPEN)
    provenance: Provenance = Field(default=Provenance.AI_INFERENCE)
