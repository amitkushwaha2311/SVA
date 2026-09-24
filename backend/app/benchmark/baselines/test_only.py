"""
SVA-Bench — Baseline B: Test-Only Adapter
==========================================

Represents a verifier that relies solely on available test outcomes.
If any test evidence in the fixture declares "pass", the requirement
is considered satisfied. It does not reason about:
  - What the tests actually cover
  - Whether negative behaviors are tested
  - Whether evidence is stale
  - Whether requirements are ambiguous or contradictory

DISCLAIMER:
    This is a benchmark baseline model, NOT a universal representation
    of all test-only verification systems. It models a naive test-pass
    verifier specifically to enable false-assurance measurement.
"""

from __future__ import annotations

from app.benchmark.baselines.base import BaselineAdapter
from app.benchmark.models import (
    BenchmarkCase,
    BenchmarkCategory,
    CaseResult,
    EvaluationMode,
    SystemConfigurationMode,
)
from app.evidence.models import VerificationState


_POSITIVE_TEST_SIGNAL = "test_pass"
_VIOLATION_SIGNAL = "test_fail"


class TestOnlyAdapter(BaselineAdapter):
    """
    Baseline B: Test-only verifier.

    Searches fixture file content for test signal markers:
    - "test_pass" → PROVEN
    - "test_fail" → VIOLATED
    - Neither → UNKNOWN

    Known simulated limitations:
    - Cannot detect positive-only traps (missing negative coverage)
    - Cannot detect stale evidence
    - Cannot detect ambiguity or contradiction
    - Cannot detect phantom requirements
    """

    @property
    def system(self) -> SystemConfigurationMode:
        return SystemConfigurationMode.BASELINE_TEST_ONLY

    @property
    def evaluation_mode(self) -> EvaluationMode:
        return EvaluationMode.DETERMINISTIC

    def evaluate(self, case: BenchmarkCase) -> CaseResult:
        all_content = "\n".join(
            f.content for f in case.repository_fixture.files
        )

        has_pass = _POSITIVE_TEST_SIGNAL in all_content
        has_fail = _VIOLATION_SIGNAL in all_content

        if has_fail:
            predicted = VerificationState.VIOLATED
        elif has_pass:
            predicted = VerificationState.PROVEN
        else:
            predicted = VerificationState.UNKNOWN

        return CaseResult(
            case_id=case.case_id,
            system=self.system,
            predicted_assurance_state=predicted,
            abstained=(predicted == VerificationState.UNKNOWN),
            ambiguity_detected=False,
            contradiction_detected=False,
            evaluator_notes=(
                "DETERMINISTIC test-only baseline: looks for 'test_pass' / "
                "'test_fail' signals only. Does not reason about coverage, "
                "staleness, ambiguity, or contradictions."
            ),
        )
