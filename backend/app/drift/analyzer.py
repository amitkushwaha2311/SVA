"""
SVA Semantic Drift Analyzer
===========================

Top-level orchestrator for the Semantic Drift & Semantic CI Engine.
"""

from __future__ import annotations

from app.contracts.models import SemanticContract
from app.drift.diff import RepositoryDiff
from app.drift.impact import ImpactAnalyzer
from app.drift.invalidation import EvidenceInvalidator
from app.drift.manager import SemanticCIManager
from app.drift.models import DriftReport, generate_drift_id
from app.evidence.graph import EvidenceGraph
from app.evidence.models import Evidence
from app.repository.intent.models import IntentCandidate
from app.repository.parser.models import CodeEntity
from app.repository.types import FileRecord
from app.semantic_ir.models import SemanticRequirement
from app.verification.models import RequirementVerification


class DriftAnalyzer:
    """Coordinates change detection, impact analysis, and CI evaluation."""

    def __init__(self, graph: EvidenceGraph | None = None) -> None:
        self.graph = graph or EvidenceGraph()
        self.diff = RepositoryDiff()
        self.impact = ImpactAnalyzer(self.graph)
        self.invalidator = EvidenceInvalidator()
        self.manager = SemanticCIManager()

    def analyze(
        self,
        repository_id: str,
        base_commit: str,
        target_commit: str,
        base_files: list[FileRecord],
        target_files: list[FileRecord],
        base_entities: list[CodeEntity],
        target_entities: list[CodeEntity],
        contracts: list[SemanticContract],
        requirements: list[SemanticRequirement],
        intent_candidates: list[IntentCandidate],
        evidence_items: list[Evidence],
        verifications: list[RequirementVerification],
    ) -> DriftReport:
        """
        Run the full Semantic Drift pipeline.
        """
        # 1. Detect Changes (Deterministic Diff)
        changes = self.diff.detect_changes(
            repository_id, base_commit, target_commit,
            base_files, target_files,
            base_entities, target_entities
        )
        
        # 2. Analyze Impact (Propagation)
        impacts = []
        for change in changes:
            imp = self.impact.analyze(change, contracts, requirements, intent_candidates)
            impacts.extend(imp)
            
        # 3. Invalidate Evidence (Staleness/Materiality)
        invalidations = self.invalidator.invalidate(
            impacts, evidence_items, verifications, target_commit
        )
        
        # 4. Determine Semantic CI State
        ci_result = self.manager.decide(changes, impacts, invalidations, verifications)
        
        # 5. Build Report
        drift_id = generate_drift_id(repository_id, base_commit, target_commit)
        
        summary = (
            f"Detected {len(changes)} changes. "
            f"Found {len(impacts)} assurance impacts. "
            f"Invalidated {len(invalidations)} artifacts. "
            f"CI Decision: {ci_result.decision.value}."
        )

        return DriftReport(
            drift_id=drift_id,
            repository_id=repository_id,
            base_commit=base_commit,
            target_commit=target_commit,
            changes=changes,
            impacts=impacts,
            invalidations=invalidations,
            summary=summary,
            semantic_ci_result=ci_result,
        )
