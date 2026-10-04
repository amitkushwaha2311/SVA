# Phase 12: Semantic Drift & Semantic CI

## Overview
Phase 12 transforms SVA from a point-in-time verification system into a continuous semantic assurance system. Given two repository states (base and target), it determines which assurance artifacts — requirements, contracts, obligations, evidence, verification results, counterexamples — are semantically affected by the changes, and whether those changes require re-verification or human review.

## Key Principles

- **Assurance Impact, Not Git Diff**: Drift detection identifies assurance-impacting changes. It does not automatically determine that changed code is correct or incorrect.
- **Historical Immutability**: Historical assurance artifacts are immutable. New repository states require new evaluation.
- **Explicit Relationships**: Configuration changes are evaluated against explicit assurance relationships. The absence of a relationship permits `PASS`; the presence of a relationship requires `REVIEW`.
- **Unsupported Entity Comparison**: Entity body modification detection is not supported by the Phase 3 data model. Phase 12 represents this as `UNKNOWN` rather than fabricating a claim.

## Semantic CI Action States

- `PASS`: No changes detected, or changes have no explicit assurance relationships (e.g., unrelated config).
- `REVIEW`: Changes affect assurance artifacts, but it is not confirmed if they violate rules.
- `BLOCK`: Changes affect a previously confirmed `VIOLATED` requirement, or explicitly break policy.

> **Note**: `PASS` ≠ `PROVEN`, `REVIEW` ≠ `UNKNOWN`, `BLOCK` ≠ `VIOLATED`. These are CI action states, not verification truth states.

## Change Types

- `FileChangeType`: `ADDED`, `REMOVED`, `MODIFIED`, `RENAMED`, `UNCHANGED`
- `EntityChangeType`: `ADDED`, `REMOVED`, `MODIFIED`, `REIDENTIFIED`, `UNCHANGED`, `UNKNOWN`

## Drift Types
- `NONE`
- `TEXTUAL`
- `STRUCTURAL`
- `BEHAVIORAL`
- `CONTRACT`
- `API`
- `AUTHORIZATION`
- `DATA`
- `INTENT`
- `CONTRADICTION`
- `CONFIGURATION`
- `DOCUMENTATION`
- `UNKNOWN`
