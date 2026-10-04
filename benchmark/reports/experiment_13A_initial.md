# SVA-Bench Experiment Report: 13A_initial

> **Initial exploratory evaluation.**
> **Insufficient sample size for broad statistical inference.**

- **Date**: 2026-09-16T18:16:27.318324+00:00
- **Cases Evaluated**: 12

## Coverage Matrix

| Case ID | Category | Ambiguity | Contradiction | Violation |
|---|---|---|---|---|
| BENCH-A-001 | A_CORRECT_IMPLEMENTATION | False | False | False |
| BENCH-B-001 | B_DIRECT_SEMANTIC_VIOLATION | False | False | True |
| BENCH-C-001 | C_POSITIVE_ONLY_EVIDENCE_TRAP | False | False | True |
| BENCH-D-001 | D_AMBIGUOUS_REQUIREMENT | True | False | False |
| BENCH-E-001 | E_CONTRADICTORY_REQUIREMENTS | False | True | False |
| BENCH-F-001 | F_PHANTOM_REQUIREMENT | False | False | False |
| BENCH-G-001 | G_STALE_EVIDENCE | False | False | True |
| BENCH-H-001 | H_CONFIGURATION_DRIFT | False | False | True |
| BENCH-K-001 | K_MALICIOUS_REPOSITORY_TEXT | False | False | True |
| BENCH-L-001 | L_MISSING_EVIDENCE | False | False | False |
| BENCH-N-001 | N_AUTHORIZATION_BOUNDARY_VIOLATION | False | False | True |
| BENCH-Q-001 | Q_SEMANTIC_DRIFT | False | False | True |


## System: BASELINE_TEST_ONLY

### Metrics

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
- **Positive Assurance Count**: 4
- **False Assurance Count**: 3
- **Appropriate Uncertainty Count**: 5
- **PROVEN count**: 4
- **VIOLATED count**: 1
- **UNKNOWN count**: 7
- **INCONCLUSIVE count**: 0

### Failure Analysis

**False Assurances (3)**:

- BENCH-C-001 (Predicted: PROVEN) -> Reason: POSITIVE_EVIDENCE_OVERGENERALIZATION
- BENCH-G-001 (Predicted: PROVEN) -> Reason: STALE_EVIDENCE_ACCEPTED
- BENCH-N-001 (Predicted: PROVEN) -> Reason: NEGATIVE_BEHAVIOR_MISSED

**Missed Violations (3)**:

- BENCH-H-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-K-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-Q-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE

---

## System: BASELINE_LLM_JUDGE

### Metrics

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
- **Positive Assurance Count**: 8
- **False Assurance Count**: 3
- **Appropriate Uncertainty Count**: 1
- **PROVEN count**: 8
- **VIOLATED count**: 1
- **UNKNOWN count**: 3
- **INCONCLUSIVE count**: 0

### Failure Analysis

**False Assurances (3)**:

- BENCH-C-001 (Predicted: PROVEN) -> Reason: POSITIVE_EVIDENCE_OVERGENERALIZATION
- BENCH-G-001 (Predicted: PROVEN) -> Reason: STALE_EVIDENCE_ACCEPTED
- BENCH-K-001 (Predicted: PROVEN) -> Reason: INTENT_MISINTERPRETATION

**Missed Violations (3)**:

- BENCH-H-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-N-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-Q-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE

---

## System: FULL_SVA

### Metrics

- **False Assurance Rate (FAR)**: N/A
  > No positive assurance decisions were produced, so FAR is not estimable.
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
- **Positive Assurance Count**: 0
- **False Assurance Count**: 0
- **Appropriate Uncertainty Count**: 7
- **PROVEN count**: 0
- **VIOLATED count**: 0
- **UNKNOWN count**: 12
- **INCONCLUSIVE count**: 0

### Failure Analysis

**False Assurances (0)**:


**Missed Violations (7)**:

- BENCH-B-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-C-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-G-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-H-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-K-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-N-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-Q-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE

---

## System: SVA_NO_AMBIGUITY_GATE

### Metrics

- **False Assurance Rate (FAR)**: N/A
  > No positive assurance decisions were produced, so FAR is not estimable.
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
- **Positive Assurance Count**: 0
- **False Assurance Count**: 0
- **Appropriate Uncertainty Count**: 7
- **PROVEN count**: 0
- **VIOLATED count**: 0
- **UNKNOWN count**: 12
- **INCONCLUSIVE count**: 0

### Failure Analysis

**False Assurances (0)**:


**Missed Violations (7)**:

- BENCH-B-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-C-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-G-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-H-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-K-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-N-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-Q-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE

---

## System: SVA_NO_NEGATIVE_OBLIGATIONS

### Metrics

- **False Assurance Rate (FAR)**: N/A
  > No positive assurance decisions were produced, so FAR is not estimable.
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
- **Positive Assurance Count**: 0
- **False Assurance Count**: 0
- **Appropriate Uncertainty Count**: 7
- **PROVEN count**: 0
- **VIOLATED count**: 0
- **UNKNOWN count**: 12
- **INCONCLUSIVE count**: 0

### Failure Analysis

**False Assurances (0)**:


**Missed Violations (7)**:

- BENCH-B-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-C-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-G-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-H-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-K-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-N-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-Q-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE

---

## System: SVA_NO_EVIDENCE_INTEGRITY

### Metrics

- **False Assurance Rate (FAR)**: N/A
  > No positive assurance decisions were produced, so FAR is not estimable.
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
- **Positive Assurance Count**: 0
- **False Assurance Count**: 0
- **Appropriate Uncertainty Count**: 7
- **PROVEN count**: 0
- **VIOLATED count**: 0
- **UNKNOWN count**: 12
- **INCONCLUSIVE count**: 0

### Failure Analysis

**False Assurances (0)**:


**Missed Violations (7)**:

- BENCH-B-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-C-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-G-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-H-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-K-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-N-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-Q-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE

---

## System: SVA_NO_STALE_DETECTION

### Metrics

- **False Assurance Rate (FAR)**: N/A
  > No positive assurance decisions were produced, so FAR is not estimable.
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
- **Positive Assurance Count**: 0
- **False Assurance Count**: 0
- **Appropriate Uncertainty Count**: 7
- **PROVEN count**: 0
- **VIOLATED count**: 0
- **UNKNOWN count**: 12
- **INCONCLUSIVE count**: 0

### Failure Analysis

**False Assurances (0)**:


**Missed Violations (7)**:

- BENCH-B-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-C-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-G-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-H-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-K-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-N-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-Q-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE

---

## System: SVA_NO_SKEPTIC

### Metrics

- **False Assurance Rate (FAR)**: N/A
  > No positive assurance decisions were produced, so FAR is not estimable.
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
- **Positive Assurance Count**: 0
- **False Assurance Count**: 0
- **Appropriate Uncertainty Count**: 7
- **PROVEN count**: 0
- **VIOLATED count**: 0
- **UNKNOWN count**: 12
- **INCONCLUSIVE count**: 0

### Failure Analysis

**False Assurances (0)**:


**Missed Violations (7)**:

- BENCH-B-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-C-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-G-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-H-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-K-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-N-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE
- BENCH-Q-001 (Predicted: UNKNOWN) -> Reason: INSUFFICIENT_EVIDENCE

---
