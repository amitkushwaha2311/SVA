"""
SVA Execution Capture
=====================

Translates ExecutionObservation into Evidence.
"""

from datetime import datetime, timezone

from app.evidence.ids import generate_evidence_id
from app.evidence.integrity import compute_evidence_hash
from app.evidence.models import (
    EnvironmentFingerprint,
    Evidence,
    EvidenceIntegrity,
    EvidenceResult,
    EvidenceStatus,
    EvidenceType,
    VerificationMethod,
)
from app.execution.models import ExecutionObservation, ExecutionRequest, ExecutionStatus
from app.repository.intent.models import Provenance


class EvidenceCapture:
    """Translates execution outcomes into strict Evidence objects."""

    def capture(self, request: ExecutionRequest, result: ExecutionObservation) -> Evidence:
        """Translate ExecutionObservation to Evidence."""

        # Determine EvidenceResult based on status and expected outcome
        # CRITICAL SECURITY RULE: exit_code == 0 MUST NOT automatically mean PROVEN (PASS)
        # Sandbox result is evidence, not truth. Phase 10 decides verification state.
        ev_result = EvidenceResult.INCONCLUSIVE
        
        if result.status == ExecutionStatus.UNSUPPORTED:
            ev_result = EvidenceResult.NOT_RUN
        elif result.status in (ExecutionStatus.TIMEOUT, ExecutionStatus.RESOURCE_LIMIT, ExecutionStatus.ERROR):
            ev_result = EvidenceResult.ERROR
        elif result.status == ExecutionStatus.NOT_RUN:
            ev_result = EvidenceResult.NOT_RUN
        elif result.status == ExecutionStatus.POLICY_DENIED:
            ev_result = EvidenceResult.NOT_RUN

        evidence_type = EvidenceType.DETERMINISTIC_TEST
        description = f"Execution of {' '.join(request.command)}"

        e_id = generate_evidence_id(
            repository_id=request.repository_id,
            contract_id=request.contract_id,
            evidence_type=evidence_type.value,
            description=description,
        )

        # Observation is raw captured output
        observation = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n\nEXIT CODE: {result.exit_code}"

        interpretation = f"Test execution status: {result.status.value}"
        if result.status == ExecutionStatus.UNSUPPORTED:
            interpretation = "Execution blocked: Secure sandbox backend unavailable."
        elif result.status == ExecutionStatus.POLICY_DENIED:
            interpretation = "Execution blocked: Policy denied execution."

        # Reconstruct sanitized environment fingerprint
        env_vars = []
        if result.environment:
            env_vars = result.environment.env_vars_injected
            
        ev = Evidence(
            evidence_id=e_id,
            contract_id=request.contract_id,
            requirement_id="UNKNOWN",  # Will be mapped during aggregation
            repository_id=request.repository_id,
            evidence_type=evidence_type,
            verification_method=VerificationMethod.UNIT_TEST,
            description=description,
            observation=observation,
            interpretation=interpretation,
            result=ev_result,
            status=EvidenceStatus.OBSERVED,
            target_refs=[request.target_id],
            commit_id=request.commit_id,
            environment=EnvironmentFingerprint(
                tool_name=result.sandbox_identity.backend_name,
                tool_version=result.sandbox_identity.image_digest or "unknown",
            ),
            provenance=Provenance.CODE,  # Evidence generated from code execution
            collected_at=datetime.now(timezone.utc).isoformat(),
            # Execution provenance bindings — included in integrity hash
            execution_id=result.execution_id,
            job_id=request.job_id,
            analysis_id=request.analysis_id,
            snapshot_id=request.snapshot_id or result.snapshot_id,
            obligation_id=request.obligation_id,
        )

        h = compute_evidence_hash(ev)
        ev.integrity = EvidenceIntegrity(evidence_hash=h, hash_algorithm="SHA-256")

        return ev
