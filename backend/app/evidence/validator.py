"""
SVA Evidence Validator
======================

Strict validation of evidence objects.
"""

from app.evidence.models import Evidence, EvidenceResult, EvidenceStatus, VerificationResult, VerificationState
from app.evidence.integrity import compute_evidence_hash, verify_evidence_hash
from app.repository.intent.models import Provenance


class EvidenceValidationError(ValueError):
    """Raised when an Evidence object violates SVA rules."""
    pass


class EvidenceValidator:
    """Validates evidence objects against strict SVA boundary rules."""

    def validate(self, evidence: Evidence) -> None:
        # 1. Identity
        if not evidence.evidence_id:
            raise EvidenceValidationError("Missing evidence_id")
        if not evidence.contract_id:
            raise EvidenceValidationError("Missing contract_id")
        if not evidence.requirement_id:
            raise EvidenceValidationError("Missing requirement_id")
        if not evidence.repository_id:
            raise EvidenceValidationError("Missing repository_id")

        # 2. Provenance must not be DEFAULT for verified evidence
        if evidence.status == EvidenceStatus.VERIFIED and evidence.provenance == Provenance.DEFAULT:
            raise EvidenceValidationError(
                f"Evidence {evidence.evidence_id} is VERIFIED but has DEFAULT provenance. "
                "Verified evidence must have explicit provenance."
            )

        # 3. Integrity hash must match if integrity is present
        if evidence.integrity is not None:
            if not verify_evidence_hash(evidence):
                raise EvidenceValidationError(
                    f"Evidence {evidence.evidence_id} integrity hash does not match computed hash."
                )

    def validate_result(self, result: VerificationResult) -> None:
        if not result.contract_id:
            raise EvidenceValidationError("VerificationResult missing contract_id")

        # PROVEN state requires actual evidence
        if result.state == VerificationState.PROVEN and not result.evidence_ids:
            raise EvidenceValidationError(
                f"VerificationResult for {result.contract_id} claims PROVEN but has no evidence_ids."
            )
