"""
Tests: Reproducibility
========================
Verifies that evaluation runs are deterministic and reproducible.
Timestamps must not influence run identity.
Result hashes must be stable.
"""

import pytest

from app.benchmark.baselines.llm_judge import LLMJudgeAdapter
from app.benchmark.baselines.test_only import TestOnlyAdapter
from app.benchmark.models import EvaluationMode
from app.benchmark.runner import BenchmarkRunner
from app.benchmark.seed_cases import SEED_CASES


class TestReproducibility:

    def _run(self, cases=None):
        if cases is None:
            cases = SEED_CASES[:3]
        adapter = TestOnlyAdapter()
        runner = BenchmarkRunner(
            adapter=adapter,
            benchmark_version="0.1.0",
            sva_commit="test-commit-abc",
        )
        return runner.run(cases)

    def test_same_cases_produce_same_run_id(self):
        run1 = self._run()
        run2 = self._run()
        assert run1.metadata.run_id == run2.metadata.run_id

    def test_same_cases_produce_same_config_hash(self):
        run1 = self._run()
        run2 = self._run()
        assert run1.metadata.configuration_hash == run2.metadata.configuration_hash

    def test_same_cases_produce_same_result_hash(self):
        run1 = self._run()
        run2 = self._run()
        assert run1.result_hash() == run2.result_hash()

    def test_different_cases_produce_different_run_id(self):
        run1 = self._run(SEED_CASES[:2])
        run2 = self._run(SEED_CASES[2:4])
        assert run1.metadata.run_id != run2.metadata.run_id

    def test_case_ids_recorded(self):
        cases = SEED_CASES[:3]
        run = self._run(cases)
        recorded_ids = set(run.metadata.case_ids)
        expected_ids = {c.case_id for c in cases}
        assert recorded_ids == expected_ids

    def test_benchmark_version_recorded(self):
        run = self._run()
        assert run.metadata.benchmark_version == "0.1.0"

    def test_sva_commit_recorded(self):
        run = self._run()
        assert run.metadata.sva_commit == "test-commit-abc"

    def test_system_recorded(self):
        run = self._run()
        from app.benchmark.models import SystemConfigurationMode
        assert run.metadata.system == SystemConfigurationMode.BASELINE_TEST_ONLY

    def test_evaluation_mode_recorded(self):
        run = self._run()
        assert run.metadata.evaluation_mode == EvaluationMode.DETERMINISTIC

    def test_tool_versions_recorded(self):
        run = self._run()
        assert "python" in run.metadata.tool_versions
        assert "platform" in run.metadata.tool_versions

    def test_result_has_correct_case_count(self):
        cases = SEED_CASES[:5]
        run = self._run(cases)
        assert len(run.case_results) == 5

    def test_empty_cases_raises(self):
        adapter = TestOnlyAdapter()
        runner = BenchmarkRunner(adapter=adapter)
        with pytest.raises(ValueError, match="at least one case"):
            runner.run([])


class TestAblationRegistry:

    def test_all_ablation_modes_registered(self):
        from app.benchmark.ablation.configurations import ABLATION_REGISTRY, list_ablation_modes
        from app.benchmark.models import SystemConfigurationMode
        modes = list_ablation_modes()
        assert SystemConfigurationMode.FULL_SVA in modes
        assert SystemConfigurationMode.SVA_NO_AMBIGUITY_GATE in modes
        assert SystemConfigurationMode.SVA_NO_SKEPTIC in modes

    def test_each_ablation_has_hypothesis(self):
        from app.benchmark.ablation.configurations import ABLATION_REGISTRY
        for mode, config in ABLATION_REGISTRY.items():
            assert config.research_hypothesis, (
                f"Ablation {mode.value} must have a non-empty research_hypothesis."
            )

    def test_each_ablation_has_expected_failure_mode(self):
        from app.benchmark.ablation.configurations import ABLATION_REGISTRY
        for mode, config in ABLATION_REGISTRY.items():
            assert config.expected_failure_mode, (
                f"Ablation {mode.value} must have a non-empty expected_failure_mode."
            )
