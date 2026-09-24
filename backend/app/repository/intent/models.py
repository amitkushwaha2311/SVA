"""
SVA Intent Models
=================

Defines the core data structures for Intent Candidates and Provenance.
"""

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Provenance(str, Enum):
    """The source category providing the intent."""

    USER = "USER"
    PRD = "PRD"
    JIRA = "JIRA"
    README = "README"
    DOCUMENT = "DOCUMENT"
    API_CONTRACT = "API_CONTRACT"
    POLICY = "POLICY"
    TEST = "TEST"
    CODE = "CODE"
    AI_INFERENCE = "AI_INFERENCE"
    DEFAULT = "DEFAULT"


class CandidateStatus(str, Enum):
    """The status of the extracted candidate."""

    CANDIDATE = "CANDIDATE"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class SourceLocation:
    """Exact source location in a file."""

    path: str
    start_line: int
    end_line: int


@dataclass
class IntentCandidate:
    """
    A discovered statement that MAY represent software intent.
    
    IMPORTANT: An IntentCandidate is NOT a Requirement. It has not been
    human-confirmed, and it does not make any semantic claims about whether
    the implementation satisfies it.
    """

    candidate_id: str
    analysis_id: str
    
    # We maintain a list of sources so identical statements can be merged logically
    # while preserving exact provenance for every occurrence.
    sources: list[SourceLocation] = field(default_factory=list)
    
    original_statement: str = ""
    normalized_statement: str | None = None
    
    provenance: Provenance = Provenance.DEFAULT
    status: CandidateStatus = CandidateStatus.CANDIDATE
    human_confirmed: bool = False
    
    extraction_method: str = "UNKNOWN"
    evidence: dict[str, Any] = field(default_factory=dict)


def generate_candidate_id(
    repository_id: str,
    original_statement: str,
) -> str:
    """
    Generate a deterministic, stable ID for an intent candidate.
    
    Because the same textual statement might appear in multiple locations,
    we base the ID on the repository and the exact text. Multiple sources
    will attach to this single logical candidate ID.
    """
    identity_string = f"{repository_id}:{original_statement}"
    return hashlib.sha256(identity_string.encode("utf-8")).hexdigest()
