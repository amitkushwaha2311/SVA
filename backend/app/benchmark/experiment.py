"""
SVA-Bench Phase 18D Experiment Orchestrator
===========================================
Runs Phase 18D Final Experimental Evaluation.
Generates structured JSON, CSV, Markdown, and Experiment Manifest.
Maintains absolute baseline integrity and strict metric calculations.
"""

import csv
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from app.benchmark.baselines.llm_judge import LLMJudgeAdapter
from app.benchmark.baselines.test_only import TestOnlyAdapter
from app.benchmark.baselines.sva import FullSVAAdapter
from app.benchmark.models import (
    EvaluationMode,
    SystemConfigurationMode,
    CaseResult,
    BenchmarkCase,
)
from app.benchmark.runner import BenchmarkRunner
from app.benchmark.seed_cases import SEED_CASES
from app.evidence.models import VerificationState
from app.benchmark.metrics.calculator import MetricsCalculator


REPORT_DIR = Path("C:/Users/AMIT KUSHWAHA/OneDrive/Desktop/SVA/benchmark/reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

SVA_VERSION = "18.0.0-final"
SVA_COMMIT = "phase18d"


def determine_failure_category(result: CaseResult, case: BenchmarkCase) -> str:
    """Deterministic failure classification without forcing matches."""
    gt = case.ground_truth

    # False Assurances
    if result.is_false_assurance:
        if case.category.value == "C_POSITIVE_ONLY_EVIDENCE_TRAP":
            return "POSITIVE_EVIDENCE_OVERGENERALIZATION"
        if case.category.value == "F_PHANTOM_REQUIREMENT":
            return "PHANTOM_REQUIREMENT"
        if case.category.value == "G_STALE_EVIDENCE":
            return "STALE_EVIDENCE_ACCEPTED"
        if case.category.value == "N_AUTHORIZATION_BOUNDARY_VIOLATION":
            return "NEGATIVE_BEHAVIOR_MISSED"
        if case.category.value == "D_AMBIGUOUS_REQUIREMENT":
            return "AMBIGUITY_MISSED"
        if case.category.value == "E_CONTRADICTORY_REQUIREMENTS":
            return "CONTRADICTORY_REQUIREMENTS_MISSED"
        return "INTENT_MISINTERPRETATION"

    # Missed Violations
    if result.missed_violation:
        if result.predicted_assurance_state == VerificationState.UNKNOWN:
            return "INSUFFICIENT_EVIDENCE"
        return "VERIFICATION_ERROR"

    return "OTHER"

def _hash_config(config_dict: dict) -> str:
    s = json.dumps(config_dict, sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()

def run_experiment(experiment_id: str, seed: int = 42):
    random.seed(seed)
    
    systems = [
        TestOnlyAdapter(),
        LLMJudgeAdapter(mode=EvaluationMode.DETERMINISTIC),
        FullSVAAdapter(mode=SystemConfigurationMode.FULL_SVA),
        # Ablations
        FullSVAAdapter(mode=SystemConfigurationMode.SVA_NO_AMBIGUITY_GATE),
        FullSVAAdapter(mode=SystemConfigurationMode.SVA_NO_NEGATIVE_OBLIGATIONS),
        FullSVAAdapter(mode=SystemConfigurationMode.SVA_NO_EVIDENCE_INTEGRITY),
        FullSVAAdapter(mode=SystemConfigurationMode.SVA_NO_STALE_DETECTION),
        FullSVAAdapter(mode=SystemConfigurationMode.SVA_NO_SKEPTIC),
    ]

    timestamp = datetime.now(timezone.utc).isoformat()
    
    # 1. Manifest
    manifest = {
        "experiment_id": experiment_id,
        "dataset_id": "sva-bench-seed",
        "dataset_version": "0.1.0",
        "SVA_commit": SVA_COMMIT,
        "SVA_version": SVA_VERSION,
        "timestamp": timestamp,
        "random_seed": seed,
        "baselines_run": [],
        "ablations_run": [],
        "configuration_hash": "",
        "environment_fingerprint": "local-test-runner",
    }
    
    # We will accumulate all results across all systems
    all_raw_results = {}
    
    markdown_report = [
        f"# SVA-Bench Phase 18D Research Report: {experiment_id}",
        "\n> **Final Experimental Evaluation**",
        "\n## Methodology\n",
        "This evaluation utilizes explicit baselines and ablations across deterministic seed cases.",
        "Ground truth is independently maintained and strictly isolated from the FULL_SVA pipeline.",
        "The LLM_JUDGE baseline is deterministic offline evaluation.\n",
        f"- **Date**: {timestamp}",
        f"- **Cases**: {len(SEED_CASES)}\n",
    ]

    for adapter in systems:
        system_name = adapter.system.value
        if "NO_" in system_name:
            manifest["ablations_run"].append(system_name)
        else:
            manifest["baselines_run"].append(system_name)
            
        runner = BenchmarkRunner(
            adapter=adapter,
            benchmark_version="0.1.0",
            sva_commit=SVA_COMMIT,
            random_seed=seed,
        )
        
        # Execute the benchmark
        run_data = runner.run(SEED_CASES)
        
        calc = MetricsCalculator()
        report = calc.compute(system_name, run_data.case_results, SEED_CASES)
        
        # Aggregate stats
        proven = sum(1 for r in run_data.case_results if r.predicted_assurance_state == VerificationState.PROVEN)
        supported = sum(1 for r in run_data.case_results if r.predicted_assurance_state == VerificationState.SUPPORTED)
        violated = sum(1 for r in run_data.case_results if r.predicted_assurance_state == VerificationState.VIOLATED)
        unknown = sum(1 for r in run_data.case_results if r.predicted_assurance_state == VerificationState.UNKNOWN)
        inconclusive = sum(1 for r in run_data.case_results if r.predicted_assurance_state == VerificationState.INCONCLUSIVE)
        stale = sum(1 for r in run_data.case_results if r.predicted_assurance_state == VerificationState.STALE)
        unsupported = sum(1 for r in run_data.case_results if r.predicted_assurance_state == VerificationState.UNSUPPORTED)

        # FAR calculation
        # False Assurance Decisions / All Positive Assurance Decisions
        pos_decisions = proven + supported
        false_assurances = sum(1 for r in run_data.case_results if r.is_false_assurance)
        
        if pos_decisions == 0:
            far_str = "N/A"
        else:
            far_str = f"{(false_assurances / pos_decisions):.2f}"

        all_raw_results[system_name] = {
            "metadata": run_data.metadata.model_dump(),
            "metrics": report.as_dict()["metrics"],
            "aggregated": {
                "PROVEN": proven,
                "SUPPORTED": supported,
                "VIOLATED": violated,
                "UNKNOWN": unknown,
                "INCONCLUSIVE": inconclusive,
                "STALE": stale,
                "UNSUPPORTED": unsupported,
                "FalseAssuranceCount": false_assurances,
                "PositiveAssuranceCount": pos_decisions,
                "FAR": far_str
            },
            "cases": [r.model_dump() for r in run_data.case_results]
        }
        
        # Update Markdown
        markdown_report.append(f"## {system_name}\n")
        markdown_report.append(f"- **Total Cases**: {len(SEED_CASES)}")
        markdown_report.append(f"- **PROVEN**: {proven}")
        markdown_report.append(f"- **SUPPORTED**: {supported}")
        markdown_report.append(f"- **VIOLATED**: {violated}")
        markdown_report.append(f"- **UNKNOWN (Abstention)**: {unknown}")
        markdown_report.append(f"- **INCONCLUSIVE**: {inconclusive}")
        markdown_report.append(f"- **STALE**: {stale}")
        markdown_report.append(f"- **UNSUPPORTED**: {unsupported}")
        markdown_report.append(f"- **FAR (False Assurance Rate)**: {far_str} ({false_assurances}/{pos_decisions})")
        markdown_report.append("\n### Detailed Metrics")
        for m in report.metrics:
            val = f"{m.value:.2f}" if m.value is not None else "N/A"
            markdown_report.append(f"- **{m.name}**: {val} ({m.numerator}/{m.denominator})")
        markdown_report.append("\n---\n")

    markdown_report.append("## Known Limitations")
    markdown_report.append("- Small sample size prevents broad statistical significance claims.")
    markdown_report.append("- LLM_JUDGE is an offline proxy deterministic implementation for safety in CI environments.")
    markdown_report.append("- Execution Sandbox is constrained to isolated test fixtures without network bounds.")
    
    manifest["configuration_hash"] = _hash_config(all_raw_results)
    
    # 1. Write Manifest JSON
    manifest_path = REPORT_DIR / f"manifest_{experiment_id}.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    # 2. Write Markdown
    md_path = REPORT_DIR / f"report_{experiment_id}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_report))
        
    # 3. Write Full Results JSON (Machine readable)
    json_path = REPORT_DIR / f"results_{experiment_id}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_raw_results, f, indent=2)
        
    # 4. Write CSV (Flat case-level)
    csv_path = REPORT_DIR / f"results_{experiment_id}.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "System", "CaseID", "Category", "PredictedState", 
            "IsFalseAssurance", "MissedViolation", "CorrectAssurance"
        ])
        for system_name, data in all_raw_results.items():
            for case in data["cases"]:
                # Lookup category
                cat = next((c.category.value for c in SEED_CASES if c.case_id == case["case_id"]), "UNKNOWN")
                writer.writerow([
                    system_name,
                    case["case_id"],
                    cat,
                    case["predicted_assurance_state"],
                    case["is_false_assurance"],
                    case["missed_violation"],
                    case.get("is_correct_assurance", False)
                ])

    print(f"Generated Phase 18D Benchmark Artifacts in {REPORT_DIR}")


if __name__ == "__main__":
    run_experiment("18D_final")
