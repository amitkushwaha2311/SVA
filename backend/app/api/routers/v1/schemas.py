"""
Phase 16 API v1 — Extended Pydantic schemas for all SVA domain objects.
All schemas are read-only (no SQLAlchemy models exposed directly).
"""

from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict


# ─── Repository & Analysis ────────────────────────────────────────────────────

class RepositoryResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    source_type: str
    repository_identifier: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RepositoryListResponse(BaseModel):
    repositories: List[RepositoryResponse]


class AnalysisResponse(BaseModel):
    id: str
    repository_id: str
    commit_id: str
    repository_manifest_hash: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisListResponse(BaseModel):
    analyses: List[AnalysisResponse]


# ─── Intent ───────────────────────────────────────────────────────────────────

class IntentResponse(BaseModel):
    id: str
    original_statement: str
    source_file: Optional[str]
    source_line: Optional[int]
    provenance: Optional[str]
    extraction_method: Optional[str]
    status: Optional[str]
    analysis_id: str

    model_config = ConfigDict(from_attributes=True)


class IntentListResponse(BaseModel):
    items: List[IntentResponse]


# ─── Contracts ────────────────────────────────────────────────────────────────

class BehaviorExpectationResponse(BaseModel):
    behavior_id: str
    contract_id: str
    is_allowed: str
    description: str
    actor: Optional[str]
    action: Optional[str]
    resource: Optional[str]
    expected_outcome: Optional[str]
    provenance: Optional[Any]

    model_config = ConfigDict(from_attributes=True)


class InvariantResponse(BaseModel):
    invariant_id: str
    contract_id: str
    statement: str
    provenance: Optional[Any]
    source_refs: List[Any]

    model_config = ConfigDict(from_attributes=True)


class ContractAssumptionResponse(BaseModel):
    assumption_id: str
    contract_id: str
    statement: str
    provenance: Optional[Any]

    model_config = ConfigDict(from_attributes=True)


class VerificationTargetResponse(BaseModel):
    target_id: str
    contract_id: str
    category: str
    description: str
    code_entity_ref: Optional[Any]

    model_config = ConfigDict(from_attributes=True)


class ContractResponse(BaseModel):
    contract_id: str
    contract_version: str
    parent_contract_id: Optional[str]
    requirement_id: Optional[str]
    candidate_id: Optional[str]
    analysis_id: str
    statement: str
    compilation_status: str
    source_refs: List[Any]
    behaviors: List[BehaviorExpectationResponse] = []
    invariants: List[InvariantResponse] = []
    assumptions: List[ContractAssumptionResponse] = []
    targets: List[VerificationTargetResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ContractListResponse(BaseModel):
    items: List[ContractResponse]


# ─── Evidence ─────────────────────────────────────────────────────────────────

class EvidenceIntegrityResponse(BaseModel):
    evidence_id: str
    evidence_hash: str
    hash_algorithm: str
    input_hashes: Dict[str, Any]
    parent_evidence_ids: List[str]

    model_config = ConfigDict(from_attributes=True)


class EnvironmentFingerprintResponse(BaseModel):
    evidence_id: str
    os_name: Optional[str]
    python_version: Optional[str]
    tool_name: Optional[str]
    tool_version: Optional[str]
    dependency_lock_hash: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class EvidenceResponse(BaseModel):
    evidence_id: str
    contract_id: Optional[str]
    requirement_id: Optional[str]
    repository_id: str
    commit_id: str
    evidence_type: str
    verification_method: str
    result: str
    status: str
    description: str
    observation: str
    collected_at: str
    integrity: Optional[EvidenceIntegrityResponse] = None
    environment: Optional[EnvironmentFingerprintResponse] = None

    model_config = ConfigDict(from_attributes=True)


class EvidenceListResponse(BaseModel):
    items: List[EvidenceResponse]
    total: int


# ─── Ambiguity ────────────────────────────────────────────────────────────────

class InterpretationResponse(BaseModel):
    interpretation_id: str
    ambiguity_id: str
    requirement_id: Optional[str]
    statement: str
    interpretation_method: str
    status: str
    semantic_fields: Optional[Any]
    assumptions: List[str]
    provenance: Optional[Any]

    model_config = ConfigDict(from_attributes=True)


class ClarificationQuestionResponse(BaseModel):
    question_id: str
    ambiguity_id: str
    question: str
    distinguishing_scenario_id: Optional[str]
    information_gain: Optional[float]
    status: str
    options: List[str]

    model_config = ConfigDict(from_attributes=True)


class AmbiguityCaseResponse(BaseModel):
    ambiguity_id: str
    statement: str
    requirement_ids: List[str]
    candidate_ids: List[str]
    ambiguity_types: List[str]
    interpretations: List[InterpretationResponse] = []
    questions: List[ClarificationQuestionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class AmbiguityListResponse(BaseModel):
    items: List[AmbiguityCaseResponse]


# ─── Verification ─────────────────────────────────────────────────────────────

class ObligationVerificationResponse(BaseModel):
    obligation_id: str
    contract_id: str
    requirement_id: Optional[str]
    decision: str
    explanation: Optional[str]
    supporting_evidence: List[str]
    contradicting_evidence: List[str]

    model_config = ConfigDict(from_attributes=True)


class RequirementVerificationResponse(BaseModel):
    id: str
    requirement_id: str
    contract_id: str
    decision: str
    explanation: Optional[str]
    limitations: List[str]
    obligation_results: List[Any]
    unresolved_obligations: List[str]

    model_config = ConfigDict(from_attributes=True)


class VerificationReportResponse(BaseModel):
    verification_id: str
    repository_id: str
    commit_id: str
    generated_at: str
    engine_version: str
    requirement_results: List[Any]

    model_config = ConfigDict(from_attributes=True)


class VerificationListResponse(BaseModel):
    requirement_verifications: List[RequirementVerificationResponse]
    obligation_verifications: List[ObligationVerificationResponse]


# ─── Drift ────────────────────────────────────────────────────────────────────

class DriftReportResponse(BaseModel):
    drift_id: str
    repository_id: str
    base_commit: str
    target_commit: str
    changes: List[Any]
    impacts: List[Any]
    invalidations: List[Any]
    summary: Optional[Any]

    model_config = ConfigDict(from_attributes=True)


class DriftListResponse(BaseModel):
    items: List[DriftReportResponse]


# ─── Activity ─────────────────────────────────────────────────────────────────

class ActivityEventResponse(BaseModel):
    id: str
    event_type: str
    actor: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    result: Optional[str]
    metadata: Optional[Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityListResponse(BaseModel):
    items: List[ActivityEventResponse]


# ─── Graph ────────────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    data: Dict[str, Any]


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str]
    relationship_type: str


class AssuranceGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

