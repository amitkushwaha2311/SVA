# Phase 13: SVA-Bench Evaluation Framework

## Research Question

> "Can a provenance-aware semantic verification architecture that explicitly
> separates human requirements, AI interpretations, assumptions, executable
> contracts, and independent behavioral evidence reduce false assurances
> compared with conventional LLM-as-judge verification?"

The benchmark measures whether SVA **actually** reduces false assurance.
It is designed to be capable of **disproving** the hypothesis.

---

## Hypothesis

SVA's architectural safeguards (provenance tracking, ambiguity detection,
negative obligation contracts, stale evidence detection, skeptic engine,
and semantic drift analysis) collectively reduce the **False Assurance Rate**
compared to simpler baselines that lack these safeguards.

This is a hypothesis. It is not yet proven. Empirical evaluation is required.

---

## Benchmark Design

### Ground Truth Independence (Critical)

All benchmark ground truths are:
- **Manually authored** by a human reviewer.
- **Version-controlled** and traceable.
- **Never derived** from SVA predictions, SVA verifiers, SVA contracts,
  SVA evidence, or any SVA output.

`GroundTruth.authored_by` must never be `"sva"`. The runtime enforces this.

### Case Categories (A–Q)

| Category | Description |
|---|---|
| A | Correct implementation — positive assurance expected |
| B | Direct semantic violation |
| C | Positive-only evidence trap |
| D | Ambiguous requirement |
| E | Contradictory requirements |
| F | Phantom requirement (AI-inferred, not human-confirmed) |
| G | Stale evidence |
| H | Configuration drift |
| I | Intent drift |
| J | Counterexample discovery |
| K | Malicious repository text (prompt injection) |
| L | Missing evidence |
| M | Scope boundary violation |
| N | Authorization boundary violation |
| O | Input boundary violation |
| P | Condition-flipping violation |
| Q | Semantic drift |

### Initial Seed Dataset

12 high-quality seed cases distributed across categories A–Q.
Case count is intentionally small. Quality and ground-truth correctness
take priority over raw count. Expand via controlled mutation.

---

## False Assurance Rate (Primary Metric)

**Definition:**
```
FAR = False Assurance Decisions / All Positive Assurance Decisions
```

**False Assurance:** System predicts PROVEN (or equivalent positive assurance)
while independent ground truth indicates `known_violation = True`.

**UNKNOWN / INCONCLUSIVE / abstentions** are NOT counted as positive assurances
and do NOT reduce FAR.

**Anti-gaming:** A system that always returns UNKNOWN achieves FAR = None
(undefined) but also achieves zero Violation Recall and zero Correct Positive
Assurance Rate. Results are reported as a **metric vector**, not a single score.

---

## Full Metric Vector

| # | Metric | What It Measures |
|---|---|---|
| 1 | False Assurance Rate (FAR) | Safety |
| 2 | Violation Recall | Usefulness: finding real violations |
| 3 | Violation Precision | Precision on violation claims |
| 4 | Correct Positive Assurance Rate | Usefulness: finding real correct implementations |
| 5 | Ambiguity Recall | Ambiguity surfacing |
| 6 | Contradiction Recall | Contradiction surfacing |
| 7 | Phantom Requirement Rate | Provenance enforcement |
| 8 | Stale Evidence Detection Rate | Temporal integrity |
| 9 | Semantic Drift Detection Rate | Drift sensitivity |
| 10 | Counterexample Discovery Rate | Skeptic engine coverage |
| 11 | Appropriate Uncertainty Rate | Calibration |

Every metric explicitly handles UNKNOWN, INCONCLUSIVE, and abstention.
There is **no aggregate score**.

---

## Baselines

### Baseline A: LLM-as-Judge (Deterministic Mode)
Simulates a naive LLM verifier. In deterministic mode it applies a fixed
rule representing known LLM failure modes (silent ambiguity resolution,
acceptance of stale evidence, etc.). This is for **benchmark framework
development only** and must NOT be presented as empirical evidence about
real LLM performance.

### Baseline B: Test-Only
Simulates a verifier that relies solely on test pass/fail signals.
Cannot detect positive-only evidence traps, stale evidence, ambiguity,
or phantom requirements.

Both baselines are adapters implementing `BaselineAdapter`. An external
LLM adapter can be configured via `EvaluationMode.EXTERNAL`.

---

## Ablation Studies

| Ablation | Component Removed | Primary Hypothesis |
|---|---|---|
| SVA_NO_PROVENANCE | Phase 4 | Higher Phantom Requirement Rate |
| SVA_NO_AMBIGUITY_GATE | Phase 6 | Ambiguity Recall = 0, higher FAR on cat D |
| SVA_NO_NEGATIVE_OBLIGATIONS | Phase 7 | High FAR on cat C |
| SVA_NO_EVIDENCE_INTEGRITY | Phase 8 | Higher FAR via corrupted evidence |
| SVA_NO_STALE_DETECTION | Phase 12 | Stale Detection Rate = 0, high FAR on cat G |
| SVA_NO_SKEPTIC | Phase 11 | Counterexample Discovery Rate = 0 |
| SVA_NO_DRIFT | Phase 12 | Semantic Drift Detection Rate = 0 |
| SVA_NO_HUMAN_CONFIRMATION | Phase 5/6 | Higher Phantom Requirement Rate |

Ablations do **not** assume worse performance. The benchmark measures the result.

---

## Mutation Framework

Mutations apply declarative string-level transformations to fixture content.
They **never** execute repository code, invoke shells, or install dependencies.

Each mutation specifies:
- `mutation_id`, `parent_case_id`, `mutation_type`
- `affected_requirement`, `expected_behavioral_effect`
- An independent `ground_truth_result` (manually authored)

---

## Statistical Methodology

- **Paired comparison**: all systems evaluate identical cases.
- **Per-category results**: reported separately.
- **Aggregate**: reported with explicit caveats.
- **Confidence intervals**: only when sample size permits.
- **Small-sample limitation**: initial seed (~12–30 cases) is insufficient
  for statistical significance claims. This is a framework; claims require expansion.
- **UNKNOWN treatment**: abstentions are excluded from FAR denominator,
  counted against usefulness metrics.
- **No gaming protection**: metric vector prevents single-dimension optimization.

---

## Security Model

Benchmark fixtures are **UNTRUSTED DATA**. The framework:
- Never executes fixture code.
- Never invokes subprocess or shell.
- Never installs fixture dependencies.
- Never makes network calls in DETERMINISTIC mode.
- Treats injected text as inert strings.

Phase 9's hardened execution boundary must be used if future execution evidence is required.

---

## Reproducibility

Every evaluation run records:
`run_id`, `benchmark_version`, `case_ids`, `sva_commit`,
`configuration_hash`, `system`, `evaluation_mode`,
`model_provider`, `model_name`, `model_version`, `prompt_version`,
`random_seed`, `tool_versions`, `environment_fingerprint`, `result_hash`.

Timestamps are metadata only and do not influence run identity.

---

## Research Integrity Rules

1. Ground truth is never derived from SVA.
2. Difficult cases are never removed because SVA performs poorly.
3. Only all required metrics are reported, not a favorable subset.
4. Results are never fabricated.
5. UNKNOWN is not treated as automatically correct.
6. Proposed counterexamples are not treated as confirmed violations.
7. Test passing is not treated as universal behavioral proof.
8. Statistical significance is never claimed without sufficient sample size.
9. Benchmark cases are never tuned against observed results without versioning.

---

## Implementation Capability vs. Empirical Evidence

SVA's architecture provides **implementation capabilities** (ambiguity detection,
provenance tracking, negative obligations, etc.). Whether these capabilities
**empirically reduce false assurance** compared to baselines is a research
question that requires benchmark evaluation with sufficient sample size.

> **Do NOT claim SVA reduces false assurance until actual benchmark evaluation
> with a statistically meaningful dataset has been performed.**

---

## Known Limitations

1. Initial seed has 12 cases — insufficient for statistical significance.
2. Fixtures are simplified mock repositories, not real codebases.
3. Deterministic baselines simulate failure modes, not real LLM behavior.
4. External LLM evaluation is not wired by default.
5. Full SVA pipeline wiring to the evaluation runner is a future extension.

---

## Threats to Validity

1. **Construct validity**: simplified fixtures may not capture complexity of real repositories.
2. **Internal validity**: researcher choices in ground truth authoring may introduce bias.
3. **External validity**: results may not generalize beyond the fixture set.
4. **Temporal validity**: SVA behavior may change between evaluated commits.
5. **Baseline validity**: deterministic baselines are models, not real systems.
