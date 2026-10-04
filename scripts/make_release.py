#!/usr/bin/env python3
"""
Phase 18D Final Release Check and Generation Script
===================================================

Validates full system regression, checks for secrets in telemetry/logs,
runs benchmarks, and outputs the final release artifacts.
"""

import subprocess
import sys
import json
import os
import re
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
REPORT_DIR = ROOT_DIR / "benchmark" / "reports"

# Secret regex patterns
SECRET_PATTERNS = [
    re.compile(r"ghp_[a-zA-Z0-9_]{36}"),
    re.compile(r"glpat-[a-zA-Z0-9_\-]{20}"),
    re.compile(r"xox[baprs]-[a-zA-Z0-9]{10,48}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN PRIVATE KEY-----")
]

def run_tests() -> bool:
    print("Running Security & Core Regression Tests (Phase 1-18D)...")
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(BACKEND_DIR)
        
        # We run the specific test files to guarantee they pass.
        # Running all tests in `backend/tests`
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-v"],
            cwd=str(BACKEND_DIR),
            env=env,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("[FAIL] Regression Tests FAILED!")
            print(result.stdout)
            print(result.stderr)
            return False
        
        print("[OK] Regression Tests Passed.")
        return True
    except Exception as e:
        print(f"[FAIL] Test execution failed: {e}")
        return False

def check_for_secrets(content: str) -> bool:
    """Returns True if a secret is found, False otherwise."""
    for pattern in SECRET_PATTERNS:
        if pattern.search(content):
            return True
    return False

def validate_artifacts() -> bool:
    print("Validating Benchmark Artifacts for Secrets...")
    if not REPORT_DIR.exists():
        print("[FAIL] Artifact directory does not exist.")
        return False
        
    found_secrets = False
    for path in REPORT_DIR.rglob("*"):
        if path.is_file() and path.suffix in [".json", ".md", ".csv", ".txt", ".log"]:
            try:
                content = path.read_text(encoding="utf-8")
                if check_for_secrets(content):
                    print(f"[FAIL] SECRET DETECTED in artifact: {path.name}")
                    found_secrets = True
            except UnicodeDecodeError:
                pass

    if found_secrets:
        return False
    print("[OK] No secrets detected in artifacts.")
    return True

def generate_benchmark_artifacts():
    print("Generating Benchmark Reports...")
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(BACKEND_DIR)
        
        result = subprocess.run(
            ["python", "app/benchmark/experiment.py"],
            cwd=str(BACKEND_DIR),
            env=env,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("[FAIL] Benchmark generation failed!")
            print(result.stdout)
            print(result.stderr)
            return False
            
        print("[OK] Benchmark Artifacts Generated.")
        return True
    except Exception as e:
        print(f"[FAIL] Benchmark execution failed: {e}")
        return False

def main():
    print("=== Phase 18D Release Validation ===")
    
    # 1. Run all regression tests
    if not run_tests():
        sys.exit(1)
        
    # 2. Generate final benchmark outputs
    if not generate_benchmark_artifacts():
        sys.exit(1)
        
    # 3. Validate artifacts for secrets
    if not validate_artifacts():
        sys.exit(1)
        
    print("=== RELEASE VALIDATION SUCCESSFUL ===")
    print("System is ready for Phase 18D final release.")
    sys.exit(0)

if __name__ == "__main__":
    main()
