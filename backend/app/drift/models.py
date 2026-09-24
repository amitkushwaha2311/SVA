"""
SVA Semantic Drift Models
=========================

Strongly typed models for the Semantic Drift & Semantic CI Engine (Phase 12).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.repository.intent.models import Provenance
from app.repository.types import FileClassification


class DriftType(str, Enum):
    """Classification of the semantic meaning of a change."""
    NONE = "NONE"
    TEXTUAL = "TEXTUAL"
    STRUCTURAL = "STRUCTURAL"
    BEHAVIORAL = "BEHAVIORAL"
    CONTRACT = "CONTRACT"
    API = "API"
    AUTHORIZATION = "AUTHORIZATION"
    DATA = "DATA"
    INTENT = "INTENT"
    CONTRADICTION = "CONTRADICTION"
    CONFIGURATION = "CONFIGURATION"
    DOCUMENTATION = "DOCUMENTATION"
    UNKNOWN = "UNKNOWN"


class DriftSeverity(str, Enum):
    """
    Describes potential assurance impact, NOT probability of failure.
    LOW: Unlikely to affect verified assurances.
    MEDIUM: May affect assurances; review recommended.
    HIGH: Affects an assurance with evidence; re-verification required.
    CRITICAL: Affects a contract/obligation with PROVEN state.
    UNKNOWN: Severity cannot be determined.
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class FileChangeType(str, Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    MODIFIED = "MODIFIED"
    RENAMED = "RENAMED"
    UNCHANGED = "UNCHANGED"


class EntityChangeType(str, Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    MODIFIED = "MODIFIED"
    REIDENTIFIED = "REIDENTIFIED"
    UNCHANGED = "UNCHANGED"
    UNKNOWN = "UNKNOWN"


class ChangeRecord(BaseModel):
    """Represents a specific structural or file-level change."""
    change_id: str
    repository_id: str
    base_commit: str
    target_commit: str
    
    file_path: str
    file_classification: FileClassification
    file_change_type: FileChangeType
    
    entity_id: str | None = None
    entity_change_type: EntityChangeType = EntityChangeType.UNKNOWN
    
    drift_type: DriftType = DriftType.UNKNOWN
    drift_severity: DriftSeverity = DriftSeverity.UNKNOWN
    
    description: str = ""
    
    base_content_hash: str | None = None
    target_content_hash: str | None = None
    
    provenance: Provenance = Provenance.DEFAULT


class SemanticImpact(BaseModel):
    """Represents the explicit relationship between a change and assurance artifacts."""
    impact_id: str
    change_id: str
    
    artifact_type: str  # "REQUIREMENT", "CONTRACT", "OBLIGATION", "TARGET", "EVIDENCE", "VERIFICATION", "COUNTEREXAMPLE"
    artifact_id: str
    
    affected_requirements: list[str] = Field(default_factory=list)
    affected_contracts: list[str] = Field(default_factory=list)
    affected_obligations: list[str] = Field(default_factory=list)
    affected_targets: list[str] = Field(default_factory=list)
    affected_evidence: list[str] = Field(default_factory=list)
    affected_verifications: list[str] = Field(default_factory=list)
    affected_counterexamples: list[str] = Field(default_factory=list)
    
    reason: str = ""
    impact_type: str = "DIRECT"  # "DIRECT", "TRANSITIVE", "UNKNOWN_RELATIONSHIP"


class InvalidationRecord(BaseModel):
    """Tracks historical artifacts (evidence/verifications) affected by drift."""
    invalidation_id: str
    artifact_type: str
    artifact_id: str
    previous_commit: str
    target_commit: str
    reason: str = ""
    status: str = "UNKNOWN"  # "STALE", "AFFECTED", "REQUIRES_REVIEW", "UNKNOWN"
    related_change_ids: list[str] = Field(default_factory=list)
    provenance: Provenance = Provenance.DEFAULT


class SemanticCIDecision(str, Enum):
    """Action state for Semantic CI. Not verification truth."""
    PASS = "PASS"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class SemanticCIResult(BaseModel):
    """Overall outcome of Semantic CI evaluation."""
    decision: SemanticCIDecision = SemanticCIDecision.REVIEW
    reason: str = ""
    affected_assurance_ids: list[str] = Field(default_factory=list)
    re_verification_required: list[str] = Field(default_factory=list)
    human_confirmation_required: list[str] = Field(default_factory=list)


class DriftReport(BaseModel):
    """Top-level report containing all drift analysis results."""
    drift_id: str
    repository_id: str
    base_commit: str
    target_commit: str
    
    changes: list[ChangeRecord] = Field(default_factory=list)
    impacts: list[SemanticImpact] = Field(default_factory=list)
    invalidations: list[InvalidationRecord] = Field(default_factory=list)
    
    summary: str = ""
    semantic_ci_result: SemanticCIResult = Field(default_factory=SemanticCIResult)
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ---------------------------------------------------------------------------
# Deterministic Identity Helpers
# ---------------------------------------------------------------------------

def generate_change_id(
    repository_id: str,
    base_commit: str,
    target_commit: str,
    file_path: str,
    canonical_change: str,
) -> str:
    identity = f"{repository_id}:{base_commit}:{target_commit}:{file_path}:{canonical_change}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def generate_impact_id(
    change_id: str,
    artifact_type: str,
    artifact_id: str,
    reason: str,
) -> str:
    identity = f"{change_id}:{artifact_type}:{artifact_id}:{reason}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def generate_invalidation_id(
    artifact_type: str,
    artifact_id: str,
    previous_commit: str,
    target_commit: str,
) -> str:
    identity = f"{artifact_type}:{artifact_id}:{previous_commit}:{target_commit}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def generate_drift_id(
    repository_id: str,
    base_commit: str,
    target_commit: str,
) -> str:
    identity = f"{repository_id}:{base_commit}:{target_commit}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()
