# SVA-Bench Phase 18D Research Report: 18D_final

> **Final Experimental Evaluation**

## Methodology

This evaluation utilizes explicit baselines and ablations across deterministic seed cases.
Ground truth is independently maintained and strictly isolated from the FULL_SVA pipeline.
The LLM_JUDGE baseline is deterministic offline evaluation.

- **Date**: 2026-09-17T12:04:36.717275+00:00
- **Cases**: 12

## BASELINE_TEST_ONLY

- **Total Cases**: 12
- **PROVEN**: 4
- **SUPPORTED**: 0
- **VIOLATED**: 1
- **UNKNOWN (Abstention)**: 7
- **INCONCLUSIVE**: 0
- **STALE**: 0
- **UNSUPPORTED**: 0
- **FAR (False Assurance Rate)**: 0.75 (3/4)

### Detailed Metrics
- **False Assurance Rate (FAR)**: 0.75 (3/4)
- **Violation Recall**: 0.14 (1/7)
- **Violation Precision**: 1.00 (1/1)
- **Correct Positive Assurance Rate**: 0.20 (1/5)
- **Ambiguity Recall**: 0.00 (0/1)
- **Contradiction Recall**: 0.00 (0/1)
- **Phantom Requirement Rate**: 0.00 (0/1)
- **Stale Evidence Detection Rate**: 0.00 (0/1)
- **Semantic Drift Detection Rate**: 0.00 (0/1)
- **Counterexample Discovery Rate**: N/A (0/0)
- **Appropriate Uncertainty Rate**: 0.71 (5/7)

---

## BASELINE_LLM_JUDGE

- **Total Cases**: 12
- **PROVEN**: 8
- **SUPPORTED**: 0
- **VIOLATED**: 1
- **UNKNOWN (Abstention)**: 3
- **INCONCLUSIVE**: 0
- **STALE**: 0
- **UNSUPPORTED**: 0
- **FAR (False Assurance Rate)**: 0.38 (3/8)

### Detailed Metrics
- **False Assurance Rate (FAR)**: 0.38 (3/8)
- **Violation Recall**: 0.14 (1/7)
- **Violation Precision**: 1.00 (1/1)
- **Correct Positive Assurance Rate**: 1.00 (5/5)
- **Ambiguity Recall**: 0.00 (0/1)
- **Contradiction Recall**: 0.00 (0/1)
- **Phantom Requirement Rate**: 1.00 (1/1)
- **Stale Evidence Detection Rate**: 0.00 (0/1)
- **Semantic Drift Detection Rate**: 0.00 (0/1)
- **Counterexample Discovery Rate**: N/A (0/0)
- **Appropriate Uncertainty Rate**: 0.14 (1/7)

---

## FULL_SVA

- **Total Cases**: 12
- **PROVEN**: 0
- **SUPPORTED**: 0
- **VIOLATED**: 0
- **UNKNOWN (Abstention)**: 12
- **INCONCLUSIVE**: 0
- **STALE**: 0
- **UNSUPPORTED**: 0
- **FAR (False Assurance Rate)**: N/A (0/0)

### Detailed Metrics
- **False Assurance Rate (FAR)**: N/A (0/0)
- **Violation Recall**: 0.00 (0/7)
- **Violation Precision**: N/A (0/0)
- **Correct Positive Assurance Rate**: 0.00 (0/5)
- **Ambiguity Recall**: 1.00 (1/1)
- **Contradiction Recall**: 1.00 (1/1)
- **Phantom Requirement Rate**: 0.00 (0/1)
- **Stale Evidence Detection Rate**: 1.00 (1/1)
- **Semantic Drift Detection Rate**: 0.00 (0/1)
- **Counterexample Discovery Rate**: N/A (0/0)
- **Appropriate Uncertainty Rate**: 1.00 (7/7)

---

## SVA_NO_AMBIGUITY_GATE

- **Total Cases**: 12
- **PROVEN**: 0
- **SUPPORTED**: 0
- **VIOLATED**: 0
- **UNKNOWN (Abstention)**: 12
- **INCONCLUSIVE**: 0
- **STALE**: 0
- **UNSUPPORTED**: 0
- **FAR (False Assurance Rate)**: N/A (0/0)

### Detailed Metrics
- **False Assurance Rate (FAR)**: N/A (0/0)
- **Violation Recall**: 0.00 (0/7)
- **Violation Precision**: N/A (0/0)
- **Correct Positive Assurance Rate**: 0.00 (0/5)
- **Ambiguity Recall**: 0.00 (0/1)
- **Contradiction Recall**: 0.00 (0/1)
- **Phantom Requirement Rate**: 0.00 (0/1)
- **Stale Evidence Detection Rate**: 1.00 (1/1)
- **Semantic Drift Detection Rate**: 0.00 (0/1)
- **Counterexample Discovery Rate**: N/A (0/0)
- **Appropriate Uncertainty Rate**: 1.00 (7/7)

---

## SVA_NO_NEGATIVE_OBLIGATIONS

- **Total Cases**: 12
- **PROVEN**: 0
- **SUPPORTED**: 0
- **VIOLATED**: 0
- **UNKNOWN (Abstention)**: 12
- **INCONCLUSIVE**: 0
- **STALE**: 0
- **UNSUPPORTED**: 0
- **FAR (False Assurance Rate)**: N/A (0/0)

### Detailed Metrics
- **False Assurance Rate (FAR)**: N/A (0/0)
- **Violation Recall**: 0.00 (0/7)
- **Violation Precision**: N/A (0/0)
- **Correct Positive Assurance Rate**: 0.00 (0/5)
- **Ambiguity Recall**: 1.00 (1/1)
- **Contradiction Recall**: 1.00 (1/1)
- **Phantom Requirement Rate**: 0.00 (0/1)
- **Stale Evidence Detection Rate**: 1.00 (1/1)
- **Semantic Drift Detection Rate**: 0.00 (0/1)
- **Counterexample Discovery Rate**: N/A (0/0)
- **Appropriate Uncertainty Rate**: 1.00 (7/7)

---

## SVA_NO_EVIDENCE_INTEGRITY

- **Total Cases**: 12
- **PROVEN**: 0
- **SUPPORTED**: 0
- **VIOLATED**: 0
- **UNKNOWN (Abstention)**: 12
- **INCONCLUSIVE**: 0
- **STALE**: 0
- **UNSUPPORTED**: 0
- **FAR (False Assurance Rate)**: N/A (0/0)

### Detailed Metrics
- **False Assurance Rate (FAR)**: N/A (0/0)
- **Violation Recall**: 0.00 (0/7)
- **Violation Precision**: N/A (0/0)
- **Correct Positive Assurance Rate**: 0.00 (0/5)
- **Ambiguity Recall**: 1.00 (1/1)
- **Contradiction Recall**: 1.00 (1/1)
- **Phantom Requirement Rate**: 0.00 (0/1)
- **Stale Evidence Detection Rate**: 1.00 (1/1)
- **Semantic Drift Detection Rate**: 0.00 (0/1)
- **Counterexample Discovery Rate**: N/A (0/0)
- **Appropriate Uncertainty Rate**: 1.00 (7/7)

---

## SVA_NO_STALE_DETECTION

- **Total Cases**: 12
- **PROVEN**: 0
- **SUPPORTED**: 0
- **VIOLATED**: 0
- **UNKNOWN (Abstention)**: 12
- **INCONCLUSIVE**: 0
- **STALE**: 0
- **UNSUPPORTED**: 0
- **FAR (False Assurance Rate)**: N/A (0/0)

### Detailed Metrics
- **False Assurance Rate (FAR)**: N/A (0/0)
- **Violation Recall**: 0.00 (0/7)
- **Violation Precision**: N/A (0/0)
- **Correct Positive Assurance Rate**: 0.00 (0/5)
- **Ambiguity Recall**: 1.00 (1/1)
- **Contradiction Recall**: 1.00 (1/1)
- **Phantom Requirement Rate**: 0.00 (0/1)
- **Stale Evidence Detection Rate**: 1.00 (1/1)
- **Semantic Drift Detection Rate**: 0.00 (0/1)
- **Counterexample Discovery Rate**: N/A (0/0)
- **Appropriate Uncertainty Rate**: 1.00 (7/7)

---

## SVA_NO_SKEPTIC

- **Total Cases**: 12
- **PROVEN**: 0
- **SUPPORTED**: 0
- **VIOLATED**: 0
- **UNKNOWN (Abstention)**: 12
- **INCONCLUSIVE**: 0
- **STALE**: 0
- **UNSUPPORTED**: 0
- **FAR (False Assurance Rate)**: N/A (0/0)

### Detailed Metrics
- **False Assurance Rate (FAR)**: N/A (0/0)
- **Violation Recall**: 0.00 (0/7)
- **Violation Precision**: N/A (0/0)
- **Correct Positive Assurance Rate**: 0.00 (0/5)
- **Ambiguity Recall**: 1.00 (1/1)
- **Contradiction Recall**: 1.00 (1/1)
- **Phantom Requirement Rate**: 0.00 (0/1)
- **Stale Evidence Detection Rate**: 1.00 (1/1)
- **Semantic Drift Detection Rate**: 0.00 (0/1)
- **Counterexample Discovery Rate**: N/A (0/0)
- **Appropriate Uncertainty Rate**: 1.00 (7/7)

---

## Known Limitations
- Small sample size prevents broad statistical significance claims.
- LLM_JUDGE is an offline proxy deterministic implementation for safety in CI environments.
- Execution Sandbox is constrained to isolated test fixtures without network bounds.