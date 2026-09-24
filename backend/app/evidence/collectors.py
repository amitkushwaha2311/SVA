"""
SVA Evidence Collectors
=======================

Coordinates static evidence collection and dynamic execution evidence.
"""

from datetime import datetime, timezone
import logging

from app.contracts.models import SemanticContract, VerificationTargetCategory
from app.evidence.ids import generate_evidence_id
from app.evidence.integrity import compute_evidence_hash
from app.evidence.models import (
    Evidence,
    EvidenceIntegrity,
    EvidenceResult,
    EvidenceStatus,
    EvidenceType,
    VerificationMethod,
)
from app.repository.intent.models import Provenance
from app.repository.parser.models import CodeEntity, EntityType

from app.execution.planner import VerificationPlanner
from app.execution.policy import get_default_policy
from app.execution.sandbox import LocalSafeFallbackSandbox
from app.execution.docker import DockerSandboxBackend
from app.execution.capture import EvidenceCapture
from app.execution.models import ExecutionObservation

logger = logging.getLogger(__name__)

class StaticEvidenceCollector:
    """
    Collects static, non-execution evidence by inspecting code entities.

    Evidence strength: CODE_MAPPING (candidate match, not proof).
    """

    def collect_code_mapping(
        self,
        repository_id: str,
        commit_id: str,
        contract: SemanticContract,
        code_entities: list[CodeEntity],
    ) -> list[Evidence]:
        """
        Generate CODE_MAPPING evidence for each candidate code entity
        that could plausibly correspond to a verification target.

        IMPORTANT: A code mapping is a candidate pointer, NOT proof of correctness.
        """
        results: list[Evidence] = []

        for target in contract.verification_targets:
            for entity in code_entities:
                if not self._is_candidate_match(target.category, entity):
                    continue

                description = (
                    f"Static candidate match: {entity.entity_type.value} "
                    f"'{entity.name}' in {entity.file_path}"
                )

                e_id = generate_evidence_id(
                    repository_id=repository_id,
                    contract_id=contract.contract_id,
                    evidence_type=EvidenceType.CODE_MAPPING.value,
                    description=description,
                )

                ev = Evidence(
                    evidence_id=e_id,
                    contract_id=contract.contract_id,
                    requirement_id=contract.requirement_id,
                    repository_id=repository_id,
                    evidence_type=EvidenceType.CODE_MAPPING,
                    verification_method=VerificationMethod.STATIC_ANALYSIS,
                    description=description,
                    # Observation records what was statically found
                    observation=(
                        f"Entity '{entity.name}' of type {entity.entity_type.value} "
                        f"found at {entity.file_path}:{entity.start_line}"
                    ),
                    # Interpretation is explicitly separate from observation
                    interpretation=(
                        "This entity is a CANDIDATE match for the verification target. "
                        "It does NOT confirm that the contract is satisfied."
                    ),
                    result=EvidenceResult.INCONCLUSIVE,
                    status=EvidenceStatus.OBSERVED,
                    target_refs=[target.target_id],
                    commit_id=commit_id,
                    provenance=Provenance.CODE,
                    collected_at=datetime.now(timezone.utc).isoformat(),
                )

                # Attach integrity hash
                h = compute_evidence_hash(ev)
                ev.integrity = EvidenceIntegrity(
                    evidence_hash=h,
                    hash_algorithm="SHA-256",
                )
                results.append(ev)

        return results

    def _is_candidate_match(
        self,
        target_category: VerificationTargetCategory,
        entity: CodeEntity,
    ) -> bool:
        """Conservative static matching heuristic."""
        if target_category in (VerificationTargetCategory.API_ENDPOINT,):
            return entity.entity_type == EntityType.API_ROUTE
        if target_category in (VerificationTargetCategory.FUNCTION,):
            return entity.entity_type == EntityType.FUNCTION
        if target_category in (VerificationTargetCategory.METHOD,):
            return entity.entity_type in (EntityType.METHOD, EntityType.FUNCTION)
        if target_category == VerificationTargetCategory.DATABASE_OPERATION:
            return entity.entity_type == EntityType.DATABASE_MODEL
        if target_category == VerificationTargetCategory.BEHAVIOR:
            return entity.entity_type in (
                EntityType.FUNCTION, EntityType.METHOD, EntityType.API_ROUTE
            )
        return False


class EvidenceCollector:
    """
    Coordinates static mapping and dynamic execution to produce Evidence.
    """
    
    def __init__(self, sandbox_backend=None):
        self.static_collector = StaticEvidenceCollector()
        self.planner = VerificationPlanner()
        self.capture = EvidenceCapture()
        self.sandbox_backend = sandbox_backend

    def collect(
        self,
        repository_id: str,
        analysis_id: str,
        scan_result,
        contracts: list[SemanticContract],
        commit_id: str = "HEAD",
        snapshot_path: str = ".",
        snapshot_id: str | None = None,
        job_id: str | None = None,
    ) -> list[Evidence]:
        
        evidence_items = []
        
        # Determine actual backend if not provided
        backend = self.sandbox_backend
        if backend is None:
            backend = DockerSandboxBackend(snapshot_path=snapshot_path)
            
        policy = get_default_policy()

        for contract in contracts:
            # 1. Static Evidence (Candidate mappings)
            static_evs = self.static_collector.collect_code_mapping(
                repository_id=repository_id,
                commit_id=commit_id,
                contract=contract,
                code_entities=scan_result.entities,
            )
            evidence_items.extend(static_evs)
            
            # 2. Dynamic Execution Evidence (Tests)
            for target in contract.verification_targets:
                if target.category == VerificationTargetCategory.TEST:
                    # Plan execution
                    request = self.planner.plan(
                        contract=contract,
                        obligation_id="derived-obligation-id", # Placeholder
                        target_id=target.target_id,
                        repository_id=repository_id,
                        commit_id=commit_id,
                        test_file=target.identifier,
                        command_id="pytest",
                        expected_outcome="PASS",
                        job_id=job_id,
                        analysis_id=analysis_id,
                        snapshot_id=snapshot_id,
                    )
                    
                    if request:
                        backend.create()
                        try:
                            # Execute safely
                            observation = backend.execute(request, policy)
                            # Convert to Evidence
                            ev = self.capture.capture(request, observation)
                            evidence_items.append(ev)
                        except Exception as e:
                            logger.error(f"Execution failed for {request.execution_id}: {e}")
                        finally:
                            backend.destroy()
        
        return evidence_items
