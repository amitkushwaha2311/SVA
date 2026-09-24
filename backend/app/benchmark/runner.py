"""
SVA-Bench Evaluation Runner
============================

Orchestrates evaluation of benchmark cases against a selected system adapter.

The runner:
  1. Loads BenchmarkCases.
  2. Runs each case through the selected BaselineAdapter.
  3. Compares results against independent GroundTruth.
  4. Annotates CaseResults with is_false_assurance, missed_violation, etc.
  5. Computes the MetricsReport via MetricsCalculator.
  6. Returns an EvaluationRun with full reproducibility metadata.

SECURITY:
  - Fixture content is treated as untrusted data.
  - No subprocess, shell, exec, or network calls in DETERMINISTIC mode.
  - External mode must be explicitly configured.

REPRODUCIBILITY:
  - All run metadata is captured in ReproducibilityMetadata.
  - Timestamps are metadata only and never influence identity.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone

from app.benchmark.baselines.base import BaselineAdapter
from app.benchmark.metrics.calculator import MetricsCalculator
from app.benchmark.models import (
    BenchmarkCase,
    EvaluationMode,
    EvaluationRun,
    ReproducibilityMetadata,
    SystemConfigurationMode,
)


class BenchmarkRunner:
    """
    Runs a set of BenchmarkCases through a BaselineAdapter and computes metrics.
    """

    def __init__(
        self,
        adapter: BaselineAdapter,
        benchmark_version: str = "0.1.0",
        sva_commit: str = "unknown",
        random_seed: int | None = None,
    ):
        self._adapter = adapter
        self._benchmark_version = benchmark_version
        self._sva_commit = sva_commit
        self._random_seed = random_seed
        self._calculator = MetricsCalculator()

    def run(self, cases: list[BenchmarkCase]) -> EvaluationRun:
        """
        Evaluate all provided cases and return a complete EvaluationRun.
        """
        if not cases:
            raise ValueError("BenchmarkRunner.run() requires at least one case.")

        # Evaluate each case
        raw_results = []
        for case in cases:
            result = self._adapter.evaluate(case)
            raw_results.append(result)

        # Compute metrics (this annotates results against ground truth)
        metrics_report = self._calculator.compute(
            system=self._adapter.system.value,
            results=raw_results,
            cases=cases,
        )

        # Collect annotated results from calculator (with ground-truth fields set)
        annotated_results = self._calculator._annotate_results(raw_results, cases)

        # Build reproducibility metadata
        config_hash = self._compute_config_hash(cases)
        run_id = self._compute_run_id(config_hash)

        metadata = ReproducibilityMetadata(
            run_id=run_id,
            benchmark_version=self._benchmark_version,
            case_ids=[c.case_id for c in cases],
            sva_commit=self._sva_commit,
            configuration_hash=config_hash,
            system=self._adapter.system,
            evaluation_mode=self._adapter.evaluation_mode,
            random_seed=self._random_seed,
            tool_versions={
                "python": sys.version,
                "platform": platform.platform(),
            },
        )

        run = EvaluationRun(
            metadata=metadata,
            case_results=annotated_results,
        )

        # Record result hash (immutable after collection)
        run.metadata.result_hash = run.result_hash()

        return run

    def _compute_config_hash(self, cases: list[BenchmarkCase]) -> str:
        """Deterministic hash of case IDs + system configuration."""
        raw = json.dumps({
            "system": self._adapter.system.value,
            "benchmark_version": self._benchmark_version,
            "case_ids": sorted(c.case_id for c in cases),
        }, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _compute_run_id(self, config_hash: str) -> str:
        """Deterministic run ID based on config hash. Timestamp is metadata only."""
        return f"run_{config_hash}"
