"""
Tests: SVA-Bench Runner (E2E)
==============================
End-to-end tests of the BenchmarkRunner against seed cases.
Verifies that:
  - Baselines produce CaseResults for all seed cases.
  - is_false_assurance is correctly annotated from ground truth.
  - missed_violation is correctly annotated.
  - Deterministic runs are reproducible.
  - Metrics are computed without error.
  - The runner never fabricates benchmark performance numbers.
"""

import pytest

from app.benchmark.baselines.llm_judge import LLMJudgeAdapter
from app.benchmark.baselines.test_only import TestOnlyAdapter
from app.benchmark.metrics.calculator import MetricsCalculator
from app.benchmark.models import EvaluationMode
from app.benchmark.runner import BenchmarkRunner
from app.benchmark.seed_cases import (
    CASE_A1, CASE_B1, CASE_C1, CASE_K1, SEED_CASES
)
from app.evidence.models import VerificationState


# ---------------------------------------------------------------------------
# Runner: basic functionality
# ---------------------------------------------------------------------------

class TestRunnerBasic:

    def _runner(self, adapter=None):
        if adapter is None:
            adapter = TestOnlyAdapter()
        return BenchmarkRunner(
            adapter=adapter,
            benchmark_version="0.1.0",
            sva_commit="abc123",
        )

    def test_runner_produces_results_for_all_cases(self):
        runner = self._runner()
        run = runner.run(SEED_CASES)
        assert len(run.case_results) == len(SEED_CASES)

    def test_runner_assigns_case_ids(self):
        runner = self._runner()
        run = runner.run(SEED_CASES[:3])
        result_ids = {r.case_id for r in run.case_results}
        case_ids = {c.case_id for c in SEED_CASES[:3]}
        assert result_ids == case_ids

    def test_runner_metadata_complete(self):
        runner = self._runner()
        run = runner.run(SEED_CASES[:3])
        meta = run.metadata
        assert meta.benchmark_version == "0.1.0"
        assert meta.sva_commit == "abc123"
        assert meta.result_hash is not None
        assert len(meta.case_ids) == 3


# ---------------------------------------------------------------------------
# Ground-truth annotation
# ---------------------------------------------------------------------------

class TestGroundTruthAnnotation:

    def _run_single(self, case, adapter=None):
        if adapter is None:
            adapter = TestOnlyAdapter()
        runner = BenchmarkRunner(adapter=adapter, sva_commit="test")
        run = runner.run([case])
        return run.case_results[0]

    def test_false_assurance_annotated_correctly(self):
        """
        CASE_C1: Positive-only evidence trap.
        TestOnlyAdapter sees 'test_pass' → predicts PROVEN.
        Ground truth: known_violation=True.
        → is_false_assurance must be True.
        """
        result = self._run_single(CASE_C1)
        assert result.predicted_assurance_state == VerificationState.PROVEN
        assert result.is_false_assurance is True

    def test_correct_assurance_not_false_assurance(self):
        """
        CASE_A1: Correct implementation with both positive and negative tests.
        TestOnlyAdapter sees 'test_pass' → PROVEN.
        Ground truth: known_violation=False.
        → is_false_assurance must be False.
        """
        result = self._run_single(CASE_A1)
        assert result.is_false_assurance is False

    def test_missed_violation_when_violated_not_found(self):
        """
        CASE_B1: Direct violation. TestOnlyAdapter sees 'test_fail' → VIOLATED.
        → missed_violation must be False (violation was found).
        """
        result = self._run_single(CASE_B1)
        assert result.predicted_assurance_state == VerificationState.VIOLATED
        assert result.missed_violation is False

    def test_malicious_case_not_proven(self):
        """
        CASE_K1: Adversarial. TestOnlyAdapter must not produce PROVEN.
        """
        result = self._run_single(CASE_K1)
        assert result.predicted_assurance_state != VerificationState.PROVEN


# ---------------------------------------------------------------------------
# LLM-judge baseline
# ---------------------------------------------------------------------------

class TestLLMJudgeBaseline:

    def _run_single(self, case):
        adapter = LLMJudgeAdapter(mode=EvaluationMode.DETERMINISTIC)
        runner = BenchmarkRunner(adapter=adapter, sva_commit="test")
        return runner.run([case]).case_results[0]

    def test_llm_judge_produces_false_assurance_on_phantom(self):
        """
        CASE_F1 (phantom requirement): naive LLM produces PROVEN.
        Ground truth: known_violation=False, but expected_state=UNKNOWN.
        → correct_assurance should be False (predicted PROVEN ≠ UNKNOWN).
        """
        from app.benchmark.seed_cases import CASE_F1
        result = self._run_single(CASE_F1)
        assert result.predicted_assurance_state == VerificationState.PROVEN
        assert result.correct_assurance is False

    def test_llm_judge_evaluates_all_seed_cases(self):
        adapter = LLMJudgeAdapter(mode=EvaluationMode.DETERMINISTIC)
        runner = BenchmarkRunner(adapter=adapter, sva_commit="test")
        run = runner.run(SEED_CASES)
        assert len(run.case_results) == len(SEED_CASES)


# ---------------------------------------------------------------------------
# Metrics: not fabricated
# ---------------------------------------------------------------------------

class TestMetricsNotFabricated:

    def test_far_is_computed_from_actual_results(self):
        """
        FAR must be computed from actual adapter output vs ground truth.
        It must NOT be a hardcoded value.
        """
        adapter = TestOnlyAdapter()
        runner = BenchmarkRunner(adapter=adapter, sva_commit="test")
        run = runner.run(SEED_CASES)

        calc = MetricsCalculator()
        report = calc.compute("TEST_ONLY", run.case_results, SEED_CASES)

        far_metrics = [m for m in report.metrics if "False Assurance Rate" in m.name]
        assert far_metrics, "FAR metric must be present."
        far = far_metrics[0]

        # FAR value is computed from data, not hardcoded
        if far.denominator > 0:
            expected = far.numerator / far.denominator
            assert abs((far.value or 0) - expected) < 1e-10

    def test_metrics_report_has_no_aggregate_score(self):
        calc = MetricsCalculator()
        cases = SEED_CASES[:3]
        adapter = TestOnlyAdapter()
        runner = BenchmarkRunner(adapter=adapter, sva_commit="test")
        run = runner.run(cases)
        report = calc.compute("TEST_ONLY", run.case_results, cases)
        assert not hasattr(report, "aggregate_score"), (
            "MetricsReport must not have an aggregate_score. "
            "Results are a metric vector, not a single number."
        )

    def test_no_empirical_claim_about_real_llm(self):
        """
        Deterministic LLM results carry the correct disclaimer in notes.
        """
        adapter = LLMJudgeAdapter(mode=EvaluationMode.DETERMINISTIC)
        runner = BenchmarkRunner(adapter=adapter, sva_commit="test")
        run = runner.run([CASE_A1])
        result = run.case_results[0]
        assert "DETERMINISTIC" in result.evaluator_notes.upper(), (
            "Deterministic LLM results must be labeled as DETERMINISTIC, "
            "not presented as empirical evidence about real LLM performance."
        )
