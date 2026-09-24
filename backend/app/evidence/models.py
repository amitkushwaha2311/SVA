"""
SVA Evidence Models
===================

Strongly typed models for the Evidence Engine.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.repository.intent.models import Provenance, SourceLocation


class EvidenceType(str, Enum):
    STATIC_ANALYSIS = "STATIC_ANALYSIS"
    DETERMINISTIC_TEST = "DETERMINISTIC_TEST"
    PROPERTY_TEST = "PROPERTY_TEST"
    ADVERSARIAL_TEST = "ADVERSARIAL_TEST"
    RUNTIME_OBSERVATION = "RUNTIME_OBSERVATION"
    FORMAL_PROOF = "FORMAL_PROOF"
    MODEL_CHECK = "MODEL_CHECK"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    DOCUMENTATION = "DOCUMENTATION"
    CODE_MAPPING = "CODE_MAPPING"
    UNKNOWN = "UNKNOWN"


class VerificationMethod(str, Enum):
    STATIC_ANALYSIS = "STATIC_ANALYSIS"
    UNIT_TEST = "UNIT_TEST"
    INTEGRATION_TEST = "INTEGRATION_TEST"
    API_TEST = "API_TEST"
    PROPERTY_TEST = "PROPERTY_TEST"
    ADVERSARIAL_TEST = "ADVERSARIAL_TEST"
    RUNTIME_OBSERVATION = "RUNTIME_OBSERVATION"
    FORMAL_VERIFICATION = "FORMAL_VERIFICATION"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class EvidenceResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    ERROR = "ERROR"
    NOT_RUN = "NOT_RUN"


class EvidenceStatus(str, Enum):
    OBSERVED = "OBSERVED"
    VERIFIED = "VERIFIED"
    INVALIDATED = "INVALIDATED"
    STALE = "STALE"
    INCONCLUSIVE = "INCONCLUSIVE"


class VerificationState(str, Enum):
    PROVEN = "PROVEN"
    SUPPORTED = "SUPPORTED"
    VIOLATED = "VIOLATED"
    INCONCLUSIVE = "INCONCLUSIVE"
    UNKNOWN = "UNKNOWN"
    STALE = "STALE"
    UNSUPPORTED = "UNSUPPORTED"


# Verification ladder: lower index = weaker evidence
VERIFICATION_LADDER: list[EvidenceType] = [
    EvidenceType.MANUAL_REVIEW,
    EvidenceType.CODE_MAPPING,
    EvidenceType.DOCUMENTATION,
    EvidenceType.STATIC_ANALYSIS,
    EvidenceType.RUNTIME_OBSERVATION,
    EvidenceType.PROPERTY_TEST,
    EvidenceType.DETERMINISTIC_TEST,
    EvidenceType.ADVERSARIAL_TEST,
    EvidenceType.MODEL_CHECK,
    EvidenceType.FORMAL_PROOF,
]


class EvidenceIntegrity(BaseModel):
    """Cryptographic integrity metadata for an evidence item."""
    evidence_hash: str
    hash_algorithm: str = "SHA-256"
    input_hashes: dict[str, str] = Field(default_factory=dict)
    parent_evidence_ids: list[str] = Field(default_factory=list)


class EnvironmentFingerprint(BaseModel):
    """Deterministic environment metadata — no secrets."""
    os_name: str | None = None
    python_version: str | None = None
    tool_name: str | None = None
    tool_version: str | None = None
    dependency_lock_hash: str | None = None


class Evidence(BaseModel):
    """
    A single provenance-aware evidence item.

    Distinguishes WHAT WAS OBSERVED from WHAT IT MEANS.
    """
    evidence_id: str
    contract_id: str
    requirement_id: str
    repository_id: str
    
    # Execution bindings
    execution_id: str | None = None
    job_id: str | None = None
    analysis_id: str | None = None
    snapshot_id: str | None = None
    obligation_id: str | None = None

    evidence_type: EvidenceType = EvidenceType.UNKNOWN
    verification_method: VerificationMethod = VerificationMethod.STATIC_ANALYSIS

    # What was evaluated
    description: str
    observation: str          # Raw observed data — not interpretation
    interpretation: str | None = None   # Optional separate interpretation

    result: EvidenceResult = EvidenceResult.NOT_RUN
    status: EvidenceStatus = EvidenceStatus.OBSERVED

    source_refs: list[SourceLocation] = Field(default_factory=list)
    target_refs: list[str] = Field(default_factory=list)   # VerificationTarget IDs

    # Repository/environment identity
    commit_id: str = "UNKNOWN"
    environment: EnvironmentFingerprint = Field(default_factory=EnvironmentFingerprint)

    # Integrity
    integrity: EvidenceIntegrity | None = None

    # Lifecycle metadata (non-identity fields)
    provenance: Provenance = Provenance.DEFAULT
    collected_at: str | None = None      # ISO timestamp — metadata, not in hash

    parent_evidence_ids: list[str] = Field(default_factory=list)


class ObligationResult(BaseModel):
    """Evidence result for a single contract obligation."""
    obligation_id: str
    description: str
    state: VerificationState = VerificationState.UNKNOWN
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str | None = None


class VerificationResult(BaseModel):
    """
    Aggregate verification result for an entire contract.

    Does NOT automatically collapse obligations into a single boolean.
    """
    contract_id: str
    requirement_id: str
    state: VerificationState = VerificationState.UNKNOWN
    evidence_ids: list[str] = Field(default_factory=list)
    obligation_results: list[ObligationResult] = Field(default_factory=list)
    explanation: str | None = None
    verification_method: VerificationMethod | None = None
