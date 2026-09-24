"""
SVA Verification Models
=======================

Strongly typed models for the Semantic Verification Engine.
"""

from typing import Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import hashlib

from app.evidence.models import VerificationState


class VerificationDecision(str):
    """
    Verification decision mapping directly to Phase 8 VerificationState.
    """
    pass


class ObligationVerification(BaseModel):
    """Result for a single verification obligation."""
    obligation_id: str
    contract_id: str
    requirement_id: str
    decision: VerificationState = VerificationState.UNKNOWN
    evidence_refs: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    explanation: str
    limitations: list[str] = Field(default_factory=list)


class RequirementVerification(BaseModel):
    """Aggregated result at the semantic requirement level."""
    requirement_id: str
    contract_id: str
    decision: VerificationState = VerificationState.UNKNOWN
    obligation_results: list[ObligationVerification] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    explanation: str
    unresolved_obligations: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class VerificationReport(BaseModel):
    """Top-level report encapsulating a verification run."""
    verification_id: str
    repository_id: str
    commit_id: str
    requirement_results: list[RequirementVerification] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    engine_version: str = "1.0.0"

def generate_verification_report_id(repository_id: str, commit_id: str) -> str:
    identity = f"VERIFICATION:{repository_id}:{commit_id}:{datetime.now(timezone.utc).isoformat()}"
    return hashlib.sha256(identity.encode('utf-8')).hexdigest()
