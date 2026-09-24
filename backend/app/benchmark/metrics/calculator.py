"""
SVA-Bench Metrics Calculator
==============================

Computes evaluation metrics from a set of CaseResults and BenchmarkCases.

Each metric has:
  - Formal definition
  - Numerator
  - Denominator
  - Interpretation
  - Limitations
  - Explicit UNKNOWN / INCONCLUSIVE / abstention handling

ANTI-GAMING PRINCIPLE:
    A system must not receive a favorable evaluation by refusing to decide.
    Both SAFETY (FAR) and USEFULNESS (Violation Recall, Correct Assurance)
    metrics are required.

    There is no single aggregate score. The result is a metric vector.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from app.benchmark.models import BenchmarkCase, BenchmarkCategory, CaseResult
from app.evidence.models import VerificationState


# ---------------------------------------------------------------------------
# Metric result container
# ---------------------------------------------------------------------------

@dataclass
class MetricResult:
    """
    A single computed metric.

    numerator and denominator are preserved for audit.
    value is None when the denominator is zero (undefined).
    """
    name: str
    value: float | None
    numerator: int
    denominator: int
    interpretation: str
    limitation: str
    notes: str = ""


@dataclass
class MetricsReport:
    """
    The full metric vector for one evaluation run.
    There is NO aggregate score — results must be read as a vector.
    """
    system: str
    total_cases: int
    per_category_counts: dict[str, int] = field(default_factory=dict)
    metrics: list[MetricResult] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "system": self.system,
            "total_cases": self.total_cases,
            "per_category_counts": self.per_category_counts,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "numerator": m.numerator,
                    "denominator": m.denominator,
                    "interpretation": m.interpretation,
                    "limitation": m.limitation,
                    "notes": m.notes,
                }
                for m in self.metrics
            ],
        }


# ---------------------------------------------------------------------------
# Helper: positive assurance states
# ---------------------------------------------------------------------------

_POSITIVE_ASSURANCE_STATES = {VerificationState.PROVEN, VerificationState.SUPPORTED}
_VIOLATION_STATES = {VerificationState.VIOLATED}
_UNCERTAIN_STATES = {VerificationState.UNKNOWN, VerificationState.INCONCLUSIVE}


def _safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


# ---------------------------------------------------------------------------
# Metric 1: False Assurance Rate (FAR)
# ---------------------------------------------------------------------------

def false_assurance_rate(
    results: Sequence[CaseResult],
    cases: Sequence[BenchmarkCase],
) -> MetricResult:
    """
    FAR = False Assurance Decisions / All Positive Assurance Decisions

    False Assurance: system predicts PROVEN (or equivalent positive)
    while ground truth has known_violation = True.

    UNKNOWN / INCONCLUSIVE / abstentions are NOT counted as positive assurances.

    Limitations:
    - A system that always returns UNKNOWN achieves FAR = 0 but is useless.
      See also: Violation Recall, Correct Positive Assurance Rate.
    """
    case_map = {c.case_id: c for c in cases}
    false_assurance_count = 0
    positive_assurance_count = 0

    for result in results:
        if result.predicted_assurance_state not in _POSITIVE_ASSURANCE_STATES:
            continue
        positive_assurance_count += 1
        bcase = case_map.get(result.case_id)
        if bcase and bcase.ground_truth.known_violation:
            false_assurance_count += 1

    return MetricResult(
        name="False Assurance Rate (FAR)",
        value=_safe_rate(false_assurance_count, positive_assurance_count),
        numerator=false_assurance_count,
        denominator=positive_assurance_count,
        interpretation=(
            "Proportion of positive assurance decisions that were incorrect. "
            "Lower is better. 0.0 is ideal but trivially achieved by abstaining."
        ),
        limitation=(
            "A system that always abstains achieves FAR=None (undefined). "
            "Must be read alongside Violation Recall and Correct Assurance Rate."
        ),
        notes=(
            f"False assurance count: {false_assurance_count}. "
            f"Positive assurance count: {positive_assurance_count}."
        ),
    )


# ---------------------------------------------------------------------------
# Metric 2: Violation Recall
# ---------------------------------------------------------------------------

def violation_recall(
    results: Sequence[CaseResult],
    cases: Sequence[BenchmarkCase],
) -> MetricResult:
    """
    Violation Recall = Violations correctly identified / Total ground-truth violations

    Measures usefulness: can the system find real violations?
    UNKNOWN / INCONCLUSIVE are NOT counted as correctly identifying a violation.

    Limitations:
    - A system that always returns VIOLATED achieves high recall but is useless
      (it would also have zero Correct Positive Assurances).
    """
    case_map = {c.case_id: c for c in cases}
    total_violations = sum(1 for c in cases if c.ground_truth.known_violation)
    correctly_identified = sum(
        1 for r in results
        if r.predicted_assurance_state in _VIOLATION_STATES
        and case_map.get(r.case_id)
        and case_map[r.case_id].ground_truth.known_violation
    )

    return MetricResult(
        name="Violation Recall",
        value=_safe_rate(correctly_identified, total_violations),
        numerator=correctly_identified,
        denominator=total_violations,
        interpretation=(
            "Proportion of true violations the system correctly identified. "
            "Higher is better. Must be read alongside FAR to prevent gaming."
        ),
        limitation=(
            "A system that always returns VIOLATED achieves recall=1.0 "
            "while also having many false assurances for correct implementations."
        ),
    )


# ---------------------------------------------------------------------------
# Metric 3: Violation Precision
# ---------------------------------------------------------------------------

def violation_precision(
    results: Sequence[CaseResult],
    cases: Sequence[BenchmarkCase],
) -> MetricResult:
    """
    Violation Precision = Correct VIOLATED predictions / All VIOLATED predictions
    """
    case_map = {c.case_id: c for c in cases}
    total_violated_predictions = sum(
        1 for r in results if r.predicted_assurance_state in _VIOLATION_STATES
    )
    correct_violated = sum(
        1 for r in results
        if r.predicted_assurance_state in _VIOLATION_STATES
        and case_map.get(r.case_id)
        and case_map[r.case_id].ground_truth.known_violation
    )

    return MetricResult(
        name="Violation Precision",
        value=_safe_rate(correct_violated, total_violated_predictions),
        numerator=correct_violated,
        denominator=total_violated_predictions,
        interpretation=(
            "Of all cases where the system said VIOLATED, what fraction actually were. "
            "Higher is better."
        ),
        limitation=(
            "A system that never predicts VIOLATED has precision=None. "
            "Must be read alongside Violation Recall."
        ),
    )


# ---------------------------------------------------------------------------
# Metric 4: Correct Positive Assurance Rate
# ---------------------------------------------------------------------------

def correct_positive_assurance_rate(
    results: Sequence[CaseResult],
    cases: Sequence[BenchmarkCase],
) -> MetricResult:
    """
    Correct Positive Assurance Rate =
        Correct positive assurance decisions / All ground-truth non-violations

    Measures usefulness on correct implementations.
    """
    case_map = {c.case_id: c for c in cases}
    non_violations = [c for c in cases if not c.ground_truth.known_violation]
    correctly_assured = sum(
        1 for r in results
        if r.predicted_assurance_state in _POSITIVE_ASSURANCE_STATES
        and case_map.get(r.case_id)
        and not case_map[r.case_id].ground_truth.known_violation
    )

    return MetricResult(
        name="Correct Positive Assurance Rate",
        value=_safe_rate(correctly_assured, len(non_violations)),
        numerator=correctly_assured,
        denominator=len(non_violations),
        interpretation=(
            "Proportion of correct implementations that the system correctly assured. "
            "Higher is better."
        ),
        limitation=(
            "A system that always returns UNKNOWN achieves 0. "
            "Must be read alongside FAR."
        ),
    )


# ---------------------------------------------------------------------------
# Metric 5: Ambiguity Recall
# ---------------------------------------------------------------------------

def ambiguity_recall(
    results: Sequence[CaseResult],
    cases: Sequence[BenchmarkCase],
) -> MetricResult:
    """
    Ambiguity Recall = Ambiguities correctly detected / Total ambiguous benchmark cases
    """
    case_map = {c.case_id: c for c in cases}
    total_ambiguous = sum(1 for c in cases if c.ground_truth.has_ambiguity)
    correctly_detected = sum(
        1 for r in results
        if r.ambiguity_detected
        and case_map.get(r.case_id)
        and case_map[r.case_id].ground_truth.has_ambiguity
    )

    return MetricResult(
        name="Ambiguity Recall",
        value=_safe_rate(correctly_detected, total_ambiguous),
        numerator=correctly_detected,
        denominator=total_ambiguous,
        interpretation=(
            "Proportion of genuinely ambiguous requirements that the system flagged as ambiguous. "
            "Higher is better."
        ),
        limitation=(
            "A system that always says ambiguous would achieve recall=1.0 at the cost "
            "of enormous false-positive ambiguity signals."
        ),
    )


# ---------------------------------------------------------------------------
# Metric 6: Contradiction Recall
# ---------------------------------------------------------------------------

def contradiction_recall(
    results: Sequence[CaseResult],
    cases: Sequence[BenchmarkCase],
) -> MetricResult:
    """
    Contradiction Recall = Contradictions correctly detected / Total contradictory benchmark cases
    """
    case_map = {c.case_id: c for c in cases}
    total_contradictory = sum(1 for c in cases if c.ground_truth.has_contradiction)
    correctly_detected = sum(
        1 for r in results
        if r.contradiction_detected
        and case_map.get(r.case_id)
        and case_map[r.case_id].ground_truth.has_contradiction
    )

    return MetricResult(
        name="Contradiction Recall",
        value=_safe_rate(correctly_detected, total_contradictory),
        numerator=correctly_detected,
        denominator=total_contradictory,
        interpretation=(
            "Proportion of contradictory requirements that the system surfaced. "
            "Higher is better."
        ),
        limitation=(
            "May be zero if the benchmark dataset has few contradiction cases."
        ),
    )


# ---------------------------------------------------------------------------
# Metric 7: Phantom Requirement Rate
# ---------------------------------------------------------------------------

def phantom_requirement_rate(
    results: Sequence[CaseResult],
    cases: Sequence[BenchmarkCase],
) -> MetricResult:
    """
    Phantom Requirement Rate =
        Phantom requirements incorrectly treated as confirmed /
        Total phantom requirement cases (Category F)

    A phantom requirement is one that appears in documentation or is inferred
    by an AI system but is NOT a confirmed human requirement.

    A system that produces PROVEN on a Category F case without proper
    human confirmation is treating a phantom as confirmed.
    """
    case_map = {c.case_id: c for c in cases}
    phantom_cases = [c for c in cases if c.category == BenchmarkCategory.F_PHANTOM_REQUIREMENT]
    phantom_incorrectly_treated = sum(
        1 for r in results
        if r.predicted_assurance_state in _POSITIVE_ASSURANCE_STATES
        and case_map.get(r.case_id)
        and case_map[r.case_id].category == BenchmarkCategory.F_PHANTOM_REQUIREMENT
    )

    return MetricResult(
        name="Phantom Requirement Rate",
        value=_safe_rate(phantom_incorrectly_treated, len(phantom_cases)),
        numerator=phantom_incorrectly_treated,
        denominator=len(phantom_cases),
        interpretation=(
            "Proportion of phantom requirements that were incorrectly treated as "
            "confirmed, producing positive assurance without human confirmation. "
            "Lower is better. 0.0 is ideal."
        ),
        limitation=(
            "Requires at least one Category F case to be meaningful. "
            "May be undefined with zero F cases."
        ),
    )


# ---------------------------------------------------------------------------
# Metric 8: Stale Evidence Detection Rate
# ---------------------------------------------------------------------------

def stale_evidence_detection_rate(
    results: Sequence[CaseResult],
    cases: Sequence[BenchmarkCase],
) -> MetricResult:
    """
    Stale Evidence Detection Rate =
        Stale evidence cases correctly NOT assured /
        Total stale evidence cases (Category G)

    A system correctly handles stale evidence when it does NOT produce a
    positive assurance on a Category G case.
    UNKNOWN, INCONCLUSIVE, or VIOLATED are all acceptable non-positive outcomes.
    """
    case_map = {c.case_id: c for c in cases}
    stale_cases = [c for c in cases if c.category == BenchmarkCategory.G_STALE_EVIDENCE]
    correctly_handled = sum(
        1 for r in results
        if r.predicted_assurance_state not in _POSITIVE_ASSURANCE_STATES
        and case_map.get(r.case_id)
        and case_map[r.case_id].category == BenchmarkCategory.G_STALE_EVIDENCE
    )

    return MetricResult(
        name="Stale Evidence Detection Rate",
        value=_safe_rate(correctly_handled, len(stale_cases)),
        numerator=correctly_handled,
        denominator=len(stale_cases),
        interpretation=(
            "Proportion of stale-evidence cases where the system correctly declined "
            "to produce a positive assurance. Higher is better."
        ),
        limitation=(
            "Does not measure whether the system explicitly named the evidence as stale; "
            "only that it avoided a false positive assurance."
        ),
    )


# ---------------------------------------------------------------------------
# Metric 9: Semantic Drift Detection Rate
# ---------------------------------------------------------------------------

def semantic_drift_detection_rate(
    results: Sequence[CaseResult],
    cases: Sequence[BenchmarkCase],
) -> MetricResult:
    """
    Semantic Drift Detection Rate =
        Drift cases correctly triggering REVIEW or higher /
        Total semantic drift cases (Category Q)
    """
    from app.drift.models import SemanticCIDecision
    case_map = {c.case_id: c for c in cases}
    drift_cases = [c for c in cases if c.category == BenchmarkCategory.Q_SEMANTIC_DRIFT]
    correctly_flagged = sum(
        1 for r in results
        if r.predicted_ci_action in {SemanticCIDecision.REVIEW, SemanticCIDecision.BLOCK}
        and case_map.get(r.case_id)
        and case_map[r.case_id].category == BenchmarkCategory.Q_SEMANTIC_DRIFT
    )

    return MetricResult(
        name="Semantic Drift Detection Rate",
        value=_safe_rate(correctly_flagged, len(drift_cases)),
        numerator=correctly_flagged,
        denominator=len(drift_cases),
        interpretation=(
            "Proportion of semantic drift cases where the system triggered REVIEW or BLOCK. "
            "Higher is better."
        ),
        limitation=(
            "Requires Category Q cases to be meaningful. "
            "A system without drift analysis will score 0."
        ),
    )


# ---------------------------------------------------------------------------
# Metric 10: Counterexample Discovery Rate
# ---------------------------------------------------------------------------

def counterexample_discovery_rate(
    results: Sequence[CaseResult],
    cases: Sequence[BenchmarkCase],
) -> MetricResult:
    """
    Counterexample Discovery Rate =
        Category J cases where system produced at least one counterexample /
        Total Category J cases
    """
    case_map = {c.case_id: c for c in cases}
    ce_cases = [c for c in cases if c.category == BenchmarkCategory.J_COUNTEREXAMPLE_DISCOVERY]
    discovered = sum(
        1 for r in results
        if len(r.counterexample_refs) > 0
        and case_map.get(r.case_id)
        and case_map[r.case_id].category == BenchmarkCategory.J_COUNTEREXAMPLE_DISCOVERY
    )

    return MetricResult(
        name="Counterexample Discovery Rate",
        value=_safe_rate(discovered, len(ce_cases)),
        numerator=discovered,
        denominator=len(ce_cases),
        interpretation=(
            "Proportion of category J cases where the system proposed at least one counterexample. "
            "Higher is better. Note: proposed counterexamples are NOT confirmed violations."
        ),
        limitation=(
            "A system can produce many invalid counterexamples and still score high. "
            "Counterexample precision is a future metric."
        ),
    )


# ---------------------------------------------------------------------------
# Metric 11: Appropriate Uncertainty Rate
# ---------------------------------------------------------------------------

def appropriate_uncertainty_rate(
    results: Sequence[CaseResult],
    cases: Sequence[BenchmarkCase],
) -> MetricResult:
    """
    Appropriate Uncertainty Rate =
        Cases where system returned UNKNOWN/INCONCLUSIVE and ground truth expects it /
        Total cases where ground truth expects UNKNOWN/INCONCLUSIVE

    Measures calibration: does the system know when it doesn't know?
    """
    case_map = {c.case_id: c for c in cases}
    expected_uncertain = [
        c for c in cases
        if c.ground_truth.expected_assurance_state in _UNCERTAIN_STATES
    ]
    correctly_uncertain = sum(
        1 for r in results
        if r.predicted_assurance_state in _UNCERTAIN_STATES
        and case_map.get(r.case_id)
        and case_map[r.case_id].ground_truth.expected_assurance_state in _UNCERTAIN_STATES
    )

    return MetricResult(
        name="Appropriate Uncertainty Rate",
        value=_safe_rate(correctly_uncertain, len(expected_uncertain)),
        numerator=correctly_uncertain,
        denominator=len(expected_uncertain),
        interpretation=(
            "Proportion of cases expecting UNKNOWN/INCONCLUSIVE where the system correctly "
            "returned an uncertain verdict. Higher is better."
        ),
        limitation=(
            "A system that always returns UNKNOWN scores 1.0 here but is useless overall. "
            "Must be read with Correct Positive Assurance Rate."
        ),
    )


# ---------------------------------------------------------------------------
# Calculator: compute all metrics
# ---------------------------------------------------------------------------

class MetricsCalculator:
    """
    Computes the full metric vector for one system across its case results.

    Does NOT produce an aggregate score — outputs a MetricsReport vector.
    """

    def compute(
        self,
        system: str,
        results: Sequence[CaseResult],
        cases: Sequence[BenchmarkCase],
    ) -> MetricsReport:
        """
        Main entry point: compute all metrics and produce a MetricsReport.
        """
        # Annotate false_assurance / missed_violation / correct_assurance on results
        # (these are computed here, independent of the adapter)
        annotated = self._annotate_results(results, cases)

        per_cat: dict[str, int] = {}
        for c in cases:
            per_cat[c.category.value] = per_cat.get(c.category.value, 0) + 1

        metrics = [
            false_assurance_rate(annotated, cases),
            violation_recall(annotated, cases),
            violation_precision(annotated, cases),
            correct_positive_assurance_rate(annotated, cases),
            ambiguity_recall(annotated, cases),
            contradiction_recall(annotated, cases),
            phantom_requirement_rate(annotated, cases),
            stale_evidence_detection_rate(annotated, cases),
            semantic_drift_detection_rate(annotated, cases),
            counterexample_discovery_rate(annotated, cases),
            appropriate_uncertainty_rate(annotated, cases),
        ]

        return MetricsReport(
            system=system,
            total_cases=len(cases),
            per_category_counts=per_cat,
            metrics=metrics,
        )

    def _annotate_results(
        self,
        results: Sequence[CaseResult],
        cases: Sequence[BenchmarkCase],
    ) -> list[CaseResult]:
        """
        Compute ground-truth comparison fields on CaseResult objects.
        Returns new annotated copies.
        """
        case_map = {c.case_id: c for c in cases}
        annotated = []
        for r in results:
            bcase = case_map.get(r.case_id)
            if bcase is None:
                annotated.append(r)
                continue

            gt = bcase.ground_truth
            predicted = r.predicted_assurance_state

            is_fa = (predicted in _POSITIVE_ASSURANCE_STATES and gt.known_violation)
            missed_viol = (gt.known_violation and predicted not in _VIOLATION_STATES)
            correct = (predicted == gt.expected_assurance_state)

            annotated.append(r.model_copy(update={
                "is_false_assurance": is_fa,
                "missed_violation": missed_viol,
                "correct_assurance": correct,
            }))
        return annotated
