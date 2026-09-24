"""
SVA-Bench Models
================

Typed data structures for the Phase 13 benchmark framework.

CRITICAL DESIGN PRINCIPLE:
    GroundTruth must be created and reviewed independently from the evaluated
    system. Ground truth must NEVER be derived from SVA output, SVA verifiers,
    SVA contracts, SVA evidence, or SVA predictions.

    SVA's VerificationState and SemanticCIDecision may be used to *map*
    evaluation outputs, but they are not themselves the oracle.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.evidence.models import VerificationState
from app.drift.models import SemanticCIDecision


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class BenchmarkCategory(str, Enum):
    """
    Case categories from the approved Phase 13 plan (A–Q).
    Each category exercises a distinct SVA weakness or capability.
    """
    A_CORRECT_IMPLEMENTATION = "A_CORRECT_IMPLEMENTATION"
    B_DIRECT_SEMANTIC_VIOLATION = "B_DIRECT_SEMANTIC_VIOLATION"
    C_POSITIVE_ONLY_EVIDENCE_TRAP = "C_POSITIVE_ONLY_EVIDENCE_TRAP"
    D_AMBIGUOUS_REQUIREMENT = "D_AMBIGUOUS_REQUIREMENT"
    E_CONTRADICTORY_REQUIREMENTS = "E_CONTRADICTORY_REQUIREMENTS"
    F_PHANTOM_REQUIREMENT = "F_PHANTOM_REQUIREMENT"
    G_STALE_EVIDENCE = "G_STALE_EVIDENCE"
    H_CONFIGURATION_DRIFT = "H_CONFIGURATION_DRIFT"
    I_INTENT_DRIFT = "I_INTENT_DRIFT"
    J_COUNTEREXAMPLE_DISCOVERY = "J_COUNTEREXAMPLE_DISCOVERY"
    K_MALICIOUS_REPOSITORY_TEXT = "K_MALICIOUS_REPOSITORY_TEXT"
    L_MISSING_EVIDENCE = "L_MISSING_EVIDENCE"
    M_SCOPE_BOUNDARY_VIOLATION = "M_SCOPE_BOUNDARY_VIOLATION"
    N_AUTHORIZATION_BOUNDARY_VIOLATION = "N_AUTHORIZATION_BOUNDARY_VIOLATION"
    O_INPUT_BOUNDARY_VIOLATION = "O_INPUT_BOUNDARY_VIOLATION"
    P_CONDITION_FLIPPING_VIOLATION = "P_CONDITION_FLIPPING_VIOLATION"
    Q_SEMANTIC_DRIFT = "Q_SEMANTIC_DRIFT"


class CaseDifficulty(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    ADVERSARIAL = "ADVERSARIAL"


class MutationType(str, Enum):
    REMOVE_AUTHORIZATION_CHECK = "REMOVE_AUTHORIZATION_CHECK"
    INVERT_AUTHORIZATION_CONDITION = "INVERT_AUTHORIZATION_CONDITION"
    CHANGE_OWNERSHIP_SCOPE = "CHANGE_OWNERSHIP_SCOPE"
    BYPASS_VALIDATION = "BYPASS_VALIDATION"
    ALTER_RESOURCE_SCOPE = "ALTER_RESOURCE_SCOPE"
    ALTER_TENANT_ISOLATION = "ALTER_TENANT_ISOLATION"
    CHANGE_API_BEHAVIOR = "CHANGE_API_BEHAVIOR"
    ALTER_DATABASE_CONSTRAINT = "ALTER_DATABASE_CONSTRAINT"
    CHANGE_CONFIGURATION = "CHANGE_CONFIGURATION"
    REMOVE_NEGATIVE_TEST = "REMOVE_NEGATIVE_TEST"
    MODIFY_CONDITION_BOUNDARY = "MODIFY_CONDITION_BOUNDARY"
    CHANGE_ERROR_BEHAVIOR = "CHANGE_ERROR_BEHAVIOR"
    CHANGE_DEFAULT_BEHAVIOR = "CHANGE_DEFAULT_BEHAVIOR"


class EvidenceSufficiency(str, Enum):
    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"
    UNKNOWN = "UNKNOWN"


class SystemConfigurationMode(str, Enum):
    """Which system configuration is being evaluated."""
    FULL_SVA = "FULL_SVA"
    SVA_NO_PROVENANCE = "SVA_NO_PROVENANCE"
    SVA_NO_AMBIGUITY_GATE = "SVA_NO_AMBIGUITY_GATE"
    SVA_NO_NEGATIVE_OBLIGATIONS = "SVA_NO_NEGATIVE_OBLIGATIONS"
    SVA_NO_EVIDENCE_INTEGRITY = "SVA_NO_EVIDENCE_INTEGRITY"
    SVA_NO_STALE_DETECTION = "SVA_NO_STALE_DETECTION"
    SVA_NO_SKEPTIC = "SVA_NO_SKEPTIC"
    SVA_NO_DRIFT = "SVA_NO_DRIFT"
    SVA_NO_HUMAN_CONFIRMATION = "SVA_NO_HUMAN_CONFIRMATION"
    BASELINE_LLM_JUDGE = "BASELINE_LLM_JUDGE"
    BASELINE_TEST_ONLY = "BASELINE_TEST_ONLY"


class EvaluationMode(str, Enum):
    """
    DETERMINISTIC: fully offline, reproducible, no network/LLM calls.
    EXTERNAL: optional real LLM evaluation, requires explicit configuration.
    """
    DETERMINISTIC = "DETERMINISTIC"
    EXTERNAL = "EXTERNAL"


# ---------------------------------------------------------------------------
# Independent Ground Truth
# ---------------------------------------------------------------------------

class GroundTruth(BaseModel):
    """
    Independent ground truth for a benchmark case.

    INVARIANT: This model must be manually authored and reviewed.
    It must never be derived from SVA predictions, SVA verifiers,
    SVA contracts, SVA evidence, or SVA output of any kind.

    The `expected_assurance_state` field uses SVA's VerificationState enum
    ONLY as a mapping vocabulary, not as a prediction.
    """
    # Human-auditable description of the intended behavior
    intent_truth: str = Field(
        description="Human-written statement of what the correct intended behavior is."
    )

    # Human-auditable description of what the code actually does
    behavioral_truth: str = Field(
        description="Human-written statement of the actual implementation behavior."
    )

    # Whether this case contains genuinely ambiguous requirements
    has_ambiguity: bool = Field(
        default=False,
        description="True if the requirement is genuinely ambiguous and should not be silently resolved."
    )

    # Competing interpretations if ambiguous
    ambiguity_interpretations: list[str] = Field(
        default_factory=list,
        description="Human-specified list of competing interpretations when ambiguity is present."
    )

    # Whether this case contains contradictory requirements
    has_contradiction: bool = Field(
        default=False,
        description="True if conflicting requirements exist that must be surfaced."
    )

    # Which requirements conflict, if applicable
    contradiction_pair: list[str] = Field(
        default_factory=list,
        description="Pair of requirement IDs or descriptions that contradict each other."
    )

    # Is there a known behavioral violation?
    known_violation: bool = Field(
        description="True if there is a known behavioral violation relative to the stated intent."
    )

    # Is the evidence in this case sufficient for any positive assurance?
    evidence_sufficiency_truth: EvidenceSufficiency = Field(
        description="Independent assessment of whether evidence is sufficient for positive assurance."
    )

    # What state should a correctly-functioning system arrive at?
    expected_assurance_state: VerificationState = Field(
        description=(
            "The assurance state a correctly-functioning verifier should reach "
            "given the fixture. Uses SVA's VerificationState only as vocabulary. "
            "Must NOT be derived from SVA's own output."
        )
    )

    # What Semantic CI action should result?
    expected_ci_action: SemanticCIDecision | None = Field(
        default=None,
        description="Expected CI action for drift-related categories, if applicable."
    )

    # Ground truth provenance: who authored and reviewed this
    authored_by: str = Field(
        default="manual_review",
        description="Author of the ground truth. Must be a human reviewer, never 'sva'."
    )
    reviewed_by: str = Field(
        default="pending_review",
        description="Reviewer who independently validated the ground truth."
    )
    ground_truth_version: str = Field(
        default="1",
        description="Ground truth version. Must be incremented when corrected."
    )

    @model_validator(mode="after")
    def validate_independence(self) -> "GroundTruth":
        if self.authored_by.lower() in {"sva", "sva_output", "sva_verifier"}:
            raise ValueError(
                "GroundTruth.authored_by must never be SVA. "
                "Ground truth must be independently authored."
            )
        if self.has_ambiguity and not self.ambiguity_interpretations:
            raise ValueError(
                "When has_ambiguity=True, at least one ambiguity_interpretation must be provided."
            )
        if self.has_contradiction and len(self.contradiction_pair) < 2:
            raise ValueError(
                "When has_contradiction=True, contradiction_pair must contain at least two entries."
            )
        return self


# ---------------------------------------------------------------------------
# Mutation Definitions
# ---------------------------------------------------------------------------

class MutationDefinition(BaseModel):
    """
    A declarative semantic mutation applied to a fixture.
    Mutations are purely declarative and must never execute arbitrary code.
    """
    mutation_id: str
    parent_case_id: str
    mutation_type: MutationType
    affected_requirement: str
    description: str
    expected_behavioral_effect: str
    ground_truth_result: GroundTruth

    def deterministic_id(self) -> str:
        """Compute deterministic mutation ID from parent + type."""
        raw = f"{self.parent_case_id}:{self.mutation_type.value}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Repository Fixture
# ---------------------------------------------------------------------------

class FileFixture(BaseModel):
    """A single file in a mock repository fixture."""
    relative_path: str
    content: str
    description: str = ""


class RepositoryFixture(BaseModel):
    """
    A mock repository used as input for benchmark evaluation.

    SECURITY: Fixture content is UNTRUSTED DATA.
    It must never be executed, imported, or installed.
    Fixtures may contain adversarial/malicious text to test prompt-injection
    resistance.
    """
    fixture_id: str
    description: str
    files: list[FileFixture] = Field(default_factory=list)
    commit_ref: str = "fixture-v1"
    version: str = "1"

    def content_hash(self) -> str:
        """Deterministic hash of all fixture content. Version-stable."""
        raw = json.dumps(
            [{"path": f.relative_path, "content": f.content} for f in sorted(self.files, key=lambda x: x.relative_path)],
            sort_keys=True
        )
        return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Benchmark Case
# ---------------------------------------------------------------------------

class BenchmarkCase(BaseModel):
    """
    A single benchmark case.

    Ground truth is independently authored; it must never be derived from SVA.
    """
    case_id: str
    version: str = "1"
    category: BenchmarkCategory
    difficulty: CaseDifficulty = CaseDifficulty.MEDIUM

    # The human requirement under evaluation
    requirement_text: str
    requirement_sources: list[str] = Field(default_factory=list)

    # The fixture representing the repository to be evaluated
    repository_fixture: RepositoryFixture

    # INDEPENDENT ground truth — never from SVA
    ground_truth: GroundTruth

    # Mutations derived from this case
    mutations: list[MutationDefinition] = Field(default_factory=list)

    # Optional notes on what this case specifically tests
    notes: str = ""

    # Metadata: authorship, dates, traceability
    metadata: dict[str, Any] = Field(default_factory=dict)

    def deterministic_id(self) -> str:
        """
        Compute a deterministic case ID from its content.
        Timestamps are excluded. This must be stable across runs.
        """
        raw = json.dumps({
            "category": self.category.value,
            "requirement_text": self.requirement_text,
            "fixture_hash": self.repository_fixture.content_hash(),
        }, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:20]


# ---------------------------------------------------------------------------
# Evaluation Results
# ---------------------------------------------------------------------------

class CaseResult(BaseModel):
    """
    The result of running one system against one benchmark case.

    This is a measurement record, not a prediction.
    """
    case_id: str
    system: SystemConfigurationMode

    # The system's predicted assurance state
    predicted_assurance_state: VerificationState | None = None

    # The system's predicted CI action
    predicted_ci_action: SemanticCIDecision | None = None

    # Did the system abstain / return UNKNOWN?
    abstained: bool = False

    # Did the system detect ambiguity?
    ambiguity_detected: bool = False

    # Did the system detect the contradiction?
    contradiction_detected: bool = False

    # Evidence refs the system cited
    evidence_refs: list[str] = Field(default_factory=list)

    # Counterexample refs the system produced
    counterexample_refs: list[str] = Field(default_factory=list)

    # --- Computed from ground truth comparison ---
    # Computed by the evaluator, not by the tested system

    is_false_assurance: bool = False
    """
    True when:
        system produced a positive assurance (PROVEN or equivalent)
        AND ground_truth.known_violation is True
        (i.e. the implementation violates intent).
    """

    missed_violation: bool = False
    """
    True when:
        ground_truth.known_violation is True
        AND the system did NOT produce a VIOLATED finding.
    """

    correct_assurance: bool = False
    """
    True when the system's predicted_assurance_state matches the
    ground_truth.expected_assurance_state.
    """

    # Raw notes from the evaluator
    evaluator_notes: str = ""


class ReproducibilityMetadata(BaseModel):
    """
    All metadata required to reproduce an evaluation run.
    Timestamps are informational metadata only and must NOT influence identity.
    """
    run_id: str
    benchmark_version: str
    case_ids: list[str]
    sva_commit: str
    configuration_hash: str
    system: SystemConfigurationMode
    evaluation_mode: EvaluationMode

    # For external LLM runs only; null for deterministic SVA runs
    model_provider: str | None = None
    model_name: str | None = None
    model_version: str | None = None
    prompt_version: str | None = None

    random_seed: int | None = None
    tool_versions: dict[str, str] = Field(default_factory=dict)
    environment_fingerprint: str | None = None
    result_hash: str | None = None


class EvaluationRun(BaseModel):
    """
    A complete evaluation run: one system across all evaluated cases.
    """
    metadata: ReproducibilityMetadata
    case_results: list[CaseResult] = Field(default_factory=list)

    def result_hash(self) -> str:
        raw = json.dumps(
            [r.model_dump() for r in self.case_results],
            sort_keys=True, default=str
        )
        return hashlib.sha256(raw.encode()).hexdigest()
