"""
SVA-Bench Baseline Adapters — Base Interface
=============================================

Defines the abstract adapter interface that all baseline systems
and SVA ablation configurations must implement.

MODES:
    DETERMINISTIC - No network, no LLM calls, fully reproducible.
    EXTERNAL      - Optional real LLM evaluation. Must be explicitly configured.
                    External results must be recorded and are immutable after collection.

IMPORTANT:
    Mocked/deterministic LLM results MUST NOT be presented as empirical
    evidence about real LLM performance.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.benchmark.models import (
    BenchmarkCase,
    CaseResult,
    EvaluationMode,
    SystemConfigurationMode,
)


class BaselineAdapter(ABC):
    """
    Abstract baseline adapter. Every system evaluated in SVA-Bench
    (SVA full, SVA ablation, LLM-judge, Test-only) implements this interface.
    """

    @property
    @abstractmethod
    def system(self) -> SystemConfigurationMode:
        """Which system/configuration this adapter represents."""
        ...

    @property
    @abstractmethod
    def evaluation_mode(self) -> EvaluationMode:
        """DETERMINISTIC or EXTERNAL."""
        ...

    @abstractmethod
    def evaluate(self, case: BenchmarkCase) -> CaseResult:
        """
        Evaluate a benchmark case and return a raw CaseResult.

        The adapter must NOT compute `is_false_assurance`, `missed_violation`,
        or `correct_assurance` — those are computed by the runner comparing
        the result against independent GroundTruth.

        SECURITY: Must not execute fixture code, invoke shells, or network
        access in DETERMINISTIC mode.
        """
        ...

    def description(self) -> str:
        """Human-readable description of what this adapter does."""
        return f"{self.system.value} [{self.evaluation_mode.value}]"
