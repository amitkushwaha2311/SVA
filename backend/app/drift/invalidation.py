"""
SVA Semantic Drift Invalidation
===============================

Handles staleness detection and invalidation of evidence and verification results.
Historical artifacts are never mutated or deleted.
"""

from __future__ import annotations

from app.drift.models import InvalidationRecord, SemanticImpact, generate_invalidation_id
from app.evidence.models import Evidence
from app.verification.models import RequirementVerification


class EvidenceInvalidator:
    """Invalidates stale evidence and verifications based on semantic impacts."""

    def invalidate(
        self,
        impacts: list[SemanticImpact],
        evidence_items: list[Evidence],
        verifications: list[RequirementVerification],
        target_commit: str,
    ) -> list[InvalidationRecord]:
        """
        Generate InvalidationRecords for stale evidence and affected verifications.
        """
        invalidations: list[InvalidationRecord] = []
        
        # Build sets of affected artifacts from impacts
        affected_evidence_ids = set()
        affected_target_ids = set()
        affected_req_ids = set()
        
        for imp in impacts:
            affected_evidence_ids.update(imp.affected_evidence)
            affected_target_ids.update(imp.affected_targets)
            affected_req_ids.update(imp.affected_requirements)

        # 1. Evidence Invalidation
        for ev in evidence_items:
            is_stale = ev.commit_id != target_commit
            is_affected = False
            
            # Check if evidence is directly affected by impact
            if ev.evidence_id in affected_evidence_ids:
                is_affected = True
                
            # Check if evidence targets an affected VerificationTarget
            if not is_affected and any(t_id in affected_target_ids for t_id in ev.target_refs):
                is_affected = True
                
            if is_stale or is_affected:
                status = "AFFECTED" if is_affected else "STALE"
                reason = (
                    f"Evidence {ev.evidence_id} was generated for commit {ev.commit_id} "
                    f"but the target is commit {target_commit}."
                )
                if is_affected:
                    reason += " It is materially affected by semantic changes."
                    
                iid = generate_invalidation_id("EVIDENCE", ev.evidence_id, ev.commit_id, target_commit)
                invalidations.append(InvalidationRecord(
                    invalidation_id=iid,
                    artifact_type="EVIDENCE",
                    artifact_id=ev.evidence_id,
                    previous_commit=ev.commit_id,
                    target_commit=target_commit,
                    reason=reason,
                    status=status,
                    provenance=ev.provenance,
                ))

        # 2. Verification Invalidation
        # For simplicity in this implementation, we assume verifications share the
        # commit_id of their underlying evidence or are passed a known "base_commit".
        # We will use the target_commit to invalidate if the req is affected.
        for vr in verifications:
            if vr.requirement_id in affected_req_ids:
                # The underlying assurance basis changed
                iid = generate_invalidation_id("VERIFICATION", vr.requirement_id, "unknown_base", target_commit)
                invalidations.append(InvalidationRecord(
                    invalidation_id=iid,
                    artifact_type="VERIFICATION",
                    artifact_id=vr.requirement_id,
                    previous_commit="unknown_base",  # Verifications should ideally store their commit
                    target_commit=target_commit,
                    reason=f"Verification result for requirement {vr.requirement_id} is affected by semantic changes. Re-verification required.",
                    status="REQUIRES_REVIEW",
                ))

        return invalidations
