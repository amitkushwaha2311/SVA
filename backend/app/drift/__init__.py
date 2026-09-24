"""
SVA Semantic Drift & Semantic CI Engine
=======================================

Transforms SVA from point-in-time verification to continuous semantic assurance.
"""

from app.drift.analyzer import DriftAnalyzer
from app.drift.diff import RepositoryDiff
from app.drift.impact import ImpactAnalyzer
from app.drift.invalidation import EvidenceInvalidator
from app.drift.manager import SemanticCIManager
from app.drift.models import (
    ChangeRecord,
    DriftReport,
    DriftSeverity,
    DriftType,
    EntityChangeType,
    FileChangeType,
    InvalidationRecord,
    SemanticCIDecision,
    SemanticCIResult,
    SemanticImpact,
    generate_change_id,
    generate_drift_id,
    generate_impact_id,
    generate_invalidation_id,
)

__all__ = [
    "DriftAnalyzer",
    "RepositoryDiff",
    "ImpactAnalyzer",
    "EvidenceInvalidator",
    "SemanticCIManager",
    "ChangeRecord",
    "DriftReport",
    "DriftSeverity",
    "DriftType",
    "EntityChangeType",
    "FileChangeType",
    "InvalidationRecord",
    "SemanticCIDecision",
    "SemanticCIResult",
    "SemanticImpact",
    "generate_change_id",
    "generate_drift_id",
    "generate_impact_id",
    "generate_invalidation_id",
]
