"""
SVA-Bench — Baseline A: LLM-as-Judge Adapter
=============================================

This adapter represents a verifier that provides requirement + code/evidence
context to a language model and accepts its verdict as the assurance result.

DETERMINISTIC MODE (default):
    Returns a controlled, deterministic result based on case category.
    Does NOT make external network calls.
    Does NOT reflect the performance of any real LLM.

EXTERNAL MODE (optional, explicitly configured):
    Calls an external LLM provider. Requires explicit configuration.
    Records provider/model/prompt metadata.
    Results are immutable after collection.

WARNING:
    Deterministic results from this adapter MUST NOT be presented as
    empirical evidence about real LLM performance. The DETERMINISTIC
    mode is for benchmark framework development and regression testing only.
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


class LLMJudgeAdapter(BaselineAdapter):
    """
    Baseline A: LLM-as-judge.

    In DETERMINISTIC mode: applies a fixed rule — categories that an LLM would
    typically fail on (e.g. phantom requirements, stale evidence) return PROVEN
    without proper scrutiny. This simulates known LLM failure modes and is used
    to exercise the benchmark's false-assurance detection.

    In EXTERNAL mode: calls the configured provider. Not implemented in the
    deterministic benchmark build.
    """

    def __init__(self, mode: EvaluationMode = EvaluationMode.DETERMINISTIC):
        self._mode = mode

    @property
    def system(self) -> SystemConfigurationMode:
        return SystemConfigurationMode.BASELINE_LLM_JUDGE

    @property
    def evaluation_mode(self) -> EvaluationMode:
        return self._mode

    def evaluate(self, case: BenchmarkCase) -> CaseResult:
        if self._mode == EvaluationMode.EXTERNAL:
            raise NotImplementedError(
                "External LLM evaluation must be explicitly configured with a "
                "provider, model, and prompt. See EXTERNAL mode documentation."
            )
        return self._deterministic_evaluate(case)

    def _deterministic_evaluate(self, case: BenchmarkCase) -> CaseResult:
        """
        Deterministic simulation of LLM-as-judge failure modes.

        IMPORTANT: This does NOT reflect real LLM behavior.
        It represents a *model* of a naive LLM-based verifier for
        benchmark framework testing only.

        Known simulated failure modes:
        - Phantom requirements are silently accepted as PROVEN
        - Stale evidence is not detected
        - Positive-only evidence traps produce PROVEN
        - Ambiguous requirements are silently resolved
        - Contradictions are not surfaced
        - Malicious text is treated as content (may produce wrong verdict)
        """
        # Categories where naive LLM-judge is expected to produce false assurances
        false_assurance_categories = {
            BenchmarkCategory.C_POSITIVE_ONLY_EVIDENCE_TRAP,
            BenchmarkCategory.F_PHANTOM_REQUIREMENT,
            BenchmarkCategory.G_STALE_EVIDENCE,
            BenchmarkCategory.K_MALICIOUS_REPOSITORY_TEXT,
            BenchmarkCategory.L_MISSING_EVIDENCE,
        }
        # Categories where naive LLM-judge silently resolves ambiguity
        silent_resolution_categories = {
            BenchmarkCategory.D_AMBIGUOUS_REQUIREMENT,
            BenchmarkCategory.E_CONTRADICTORY_REQUIREMENTS,
        }
        # Categories where it correctly finds violations
        violation_categories = {
            BenchmarkCategory.B_DIRECT_SEMANTIC_VIOLATION,
        }

        if case.category in violation_categories:
            predicted = VerificationState.VIOLATED
            ambiguity_detected = False
            contradiction_detected = False
        elif case.category in silent_resolution_categories:
            # LLM picks one interpretation silently — simulate PROVEN
            predicted = VerificationState.PROVEN
            ambiguity_detected = False
            contradiction_detected = False
        elif case.category in false_assurance_categories:
            # Naive LLM is fooled into PROVEN
            predicted = VerificationState.PROVEN
            ambiguity_detected = False
            contradiction_detected = False
        elif case.category == BenchmarkCategory.A_CORRECT_IMPLEMENTATION:
            predicted = VerificationState.PROVEN
            ambiguity_detected = False
            contradiction_detected = False
        else:
            # Conservative: unknown
            predicted = VerificationState.UNKNOWN
            ambiguity_detected = False
            contradiction_detected = False

        return CaseResult(
            case_id=case.case_id,
            system=self.system,
            predicted_assurance_state=predicted,
            abstained=(predicted == VerificationState.UNKNOWN),
            ambiguity_detected=ambiguity_detected,
            contradiction_detected=contradiction_detected,
            evaluator_notes=(
                "DETERMINISTIC mode: simulated LLM-as-judge failure pattern. "
                "Does NOT reflect real LLM performance."
            ),
        )
