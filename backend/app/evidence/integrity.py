"""
SVA Evidence Integrity
======================

Canonical serialization and deterministic hashing of evidence.
"""

import hashlib
import json

from app.evidence.models import Evidence


def _canonical_evidence_dict(evidence: Evidence) -> dict:
    """
    Build a canonical, deterministic dictionary of evidence identity fields.

    Deliberately excludes volatile metadata (collected_at timestamp) to
    ensure the hash represents identity, not time of collection.
    """
    return {
        "evidence_id": evidence.evidence_id,
        "contract_id": evidence.contract_id,
        "requirement_id": evidence.requirement_id,
        "repository_id": evidence.repository_id,
        "evidence_type": evidence.evidence_type.value,
        "verification_method": evidence.verification_method.value,
        "description": evidence.description,
        "observation": evidence.observation,
        "result": evidence.result.value,
        "commit_id": evidence.commit_id,
        "target_refs": sorted(evidence.target_refs),
        "source_refs": sorted(
            [f"{s.path}:{s.start_line}" for s in evidence.source_refs]
        ),
        "parent_evidence_ids": sorted(evidence.parent_evidence_ids),
        # Execution provenance bindings — must be in hash so any tampering invalidates integrity
        "execution_id": evidence.execution_id,
        "job_id": evidence.job_id,
        "analysis_id": evidence.analysis_id,
        "snapshot_id": evidence.snapshot_id,
        "obligation_id": evidence.obligation_id,
        "environment": evidence.environment.model_dump(),
    }


def compute_evidence_hash(evidence: Evidence) -> str:
    """
    Compute a deterministic SHA-256 hash over canonical evidence identity fields.

    Does NOT include timestamp. Identical evidence produced at different times
    yields the same hash.
    """
    canonical = _canonical_evidence_dict(evidence)
    serialized = json.dumps(canonical, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def verify_evidence_hash(evidence: Evidence) -> bool:
    """Returns True if the stored integrity hash matches a freshly computed hash."""
    if evidence.integrity is None:
        return False
    expected = compute_evidence_hash(evidence)
    return evidence.integrity.evidence_hash == expected
