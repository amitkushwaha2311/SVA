"""
SVA-Bench Ablation Configurations
===================================

Defines the ablation configurations for SVA-Bench.

Each ablation removes or disables one component of the SVA architecture.
The benchmark MEASURES whether removing a component changes results.
It does NOT assume that ablations perform worse — that is an empirical question.

IMPORTANT:
    These are configuration-level stubs for now (Phase 13 scope).
    Full ablation wiring to SVA internals is a future research extension.
    In this implementation they use the same deterministic adapter pattern
    as the baselines, but with component-specific failure simulation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from app.benchmark.models import SystemConfigurationMode


@dataclass(frozen=True)
class AblationConfig:
    """
    Describes a single ablation configuration.

    component_removed: The SVA component this ablation disables.
    research_hypothesis: What we expect will happen when removed.
    expected_failure_mode: How we expect the ablated system to fail.
    metrics_affected: Which benchmark metrics are expected to change most.
    """
    name: SystemConfigurationMode
    component_removed: str
    research_hypothesis: str
    expected_failure_mode: str
    metrics_affected: list[str] = field(default_factory=list)


ABLATION_REGISTRY: dict[SystemConfigurationMode, AblationConfig] = {
    SystemConfigurationMode.FULL_SVA: AblationConfig(
        name=SystemConfigurationMode.FULL_SVA,
        component_removed="None (full architecture)",
        research_hypothesis="Full SVA should produce the lowest False Assurance Rate.",
        expected_failure_mode="None expected, subject to empirical validation.",
        metrics_affected=[],
    ),
    SystemConfigurationMode.SVA_NO_PROVENANCE: AblationConfig(
        name=SystemConfigurationMode.SVA_NO_PROVENANCE,
        component_removed="Provenance tracking (Phase 4)",
        research_hypothesis=(
            "Without provenance, AI-inferred phantom requirements may be "
            "silently treated as human-confirmed intent, raising Phantom Requirement Rate."
        ),
        expected_failure_mode="Higher Phantom Requirement Rate; Intent Recall unchanged.",
        metrics_affected=["Phantom Requirement Rate", "Intent Precision"],
    ),
    SystemConfigurationMode.SVA_NO_AMBIGUITY_GATE: AblationConfig(
        name=SystemConfigurationMode.SVA_NO_AMBIGUITY_GATE,
        component_removed="Ambiguity Engine (Phase 6)",
        research_hypothesis=(
            "Without the ambiguity gate, ambiguous requirements will be silently "
            "resolved, potentially masking semantic errors and raising FAR."
        ),
        expected_failure_mode="Ambiguity Recall = 0; higher False Assurance Rate on category D.",
        metrics_affected=["Ambiguity Recall", "False Assurance Rate", "Phantom Requirement Rate"],
    ),
    SystemConfigurationMode.SVA_NO_NEGATIVE_OBLIGATIONS: AblationConfig(
        name=SystemConfigurationMode.SVA_NO_NEGATIVE_OBLIGATIONS,
        component_removed="Negative/forbidden obligation contracts (Phase 7)",
        research_hypothesis=(
            "Without negative obligations, positive-only evidence traps "
            "will not be caught, raising FAR on category C."
        ),
        expected_failure_mode="High FAR for category C (positive-only evidence trap).",
        metrics_affected=["False Assurance Rate", "Violation Recall"],
    ),
    SystemConfigurationMode.SVA_NO_EVIDENCE_INTEGRITY: AblationConfig(
        name=SystemConfigurationMode.SVA_NO_EVIDENCE_INTEGRITY,
        component_removed="Evidence integrity checks (Phase 8)",
        research_hypothesis=(
            "Without integrity checks, tampered or misidentified evidence "
            "may be accepted, raising FAR."
        ),
        expected_failure_mode="Evidence integrity failures are silently accepted as PROVEN.",
        metrics_affected=["False Assurance Rate", "Evidence Provenance Completeness"],
    ),
    SystemConfigurationMode.SVA_NO_STALE_DETECTION: AblationConfig(
        name=SystemConfigurationMode.SVA_NO_STALE_DETECTION,
        component_removed="Stale evidence detection (Phase 12)",
        research_hypothesis=(
            "Without stale detection, evidence from prior commits will still "
            "count toward current assurance, raising FAR on category G."
        ),
        expected_failure_mode="Stale Evidence Detection Rate = 0; high FAR on category G.",
        metrics_affected=["Stale Evidence Detection Rate", "False Assurance Rate"],
    ),
    SystemConfigurationMode.SVA_NO_SKEPTIC: AblationConfig(
        name=SystemConfigurationMode.SVA_NO_SKEPTIC,
        component_removed="Counterexample / Skeptic Engine (Phase 11)",
        research_hypothesis=(
            "Without the skeptic, boundary cases and authorization violations "
            "may go unchallenged, reducing Counterexample Discovery Rate."
        ),
        expected_failure_mode="Counterexample Discovery Rate = 0; possibly higher FAR on J, N, O, P.",
        metrics_affected=["Counterexample Discovery Rate", "Violation Recall"],
    ),
    SystemConfigurationMode.SVA_NO_DRIFT: AblationConfig(
        name=SystemConfigurationMode.SVA_NO_DRIFT,
        component_removed="Semantic Drift / Semantic CI (Phase 12)",
        research_hypothesis=(
            "Without drift analysis, repository changes will not invalidate "
            "prior assurances, leading to stale positive claims."
        ),
        expected_failure_mode="Semantic Drift Detection Rate = 0; stale CI states on category Q.",
        metrics_affected=["Semantic Drift Detection Rate", "Stale Evidence Detection Rate"],
    ),
    SystemConfigurationMode.SVA_NO_HUMAN_CONFIRMATION: AblationConfig(
        name=SystemConfigurationMode.SVA_NO_HUMAN_CONFIRMATION,
        component_removed="Human confirmation gate (Phase 5/6)",
        research_hypothesis=(
            "Without human confirmation, AI-inferred intents may be automatically "
            "treated as verified requirements, raising Phantom Requirement Rate."
        ),
        expected_failure_mode="Phantom Requirement Rate increases; category F becomes indistinguishable from A.",
        metrics_affected=["Phantom Requirement Rate", "False Assurance Rate", "Intent Precision"],
    ),
}


def get_ablation_config(mode: SystemConfigurationMode) -> AblationConfig | None:
    """Retrieve an ablation configuration by mode."""
    return ABLATION_REGISTRY.get(mode)


def list_ablation_modes() -> list[SystemConfigurationMode]:
    """Return all registered ablation modes."""
    return list(ABLATION_REGISTRY.keys())
