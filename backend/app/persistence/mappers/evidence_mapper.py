from datetime import datetime
from typing import Optional

from app.evidence.models import Evidence, EvidenceIntegrity, EnvironmentFingerprint, EvidenceType, VerificationMethod, EvidenceResult, EvidenceStatus
from app.persistence.models.evidence import EvidenceRow, EvidenceIntegrityRow, EnvironmentFingerprintRow


class EvidenceMapper:
    @staticmethod
    def to_row(domain: Evidence) -> EvidenceRow:
        row = EvidenceRow(
            evidence_id=domain.evidence_id,
            contract_id=domain.contract_id,
            requirement_id=domain.requirement_id,
            repository_id=domain.repository_id,
            commit_id=domain.commit_id,
            evidence_type=domain.evidence_type.value,
            verification_method=domain.verification_method.value,
            result=domain.result.value,
            status=domain.status.value,
            description=domain.description,
            observation=domain.observation,
            collected_at=domain.collected_at
        )
        return row

    @staticmethod
    def from_row(row: EvidenceRow, integrity_row: Optional[EvidenceIntegrityRow] = None, fingerprint_row: Optional[EnvironmentFingerprintRow] = None) -> Evidence:
        integrity = None
        if integrity_row:
            integrity = EvidenceIntegrity(
                evidence_hash=integrity_row.evidence_hash,
                hash_algorithm=integrity_row.hash_algorithm,
                input_hashes=integrity_row.input_hashes,
                parent_evidence_ids=integrity_row.parent_evidence_ids
            )
            
        environment = None
        if fingerprint_row:
            environment = EnvironmentFingerprint(
                os_name=fingerprint_row.os_name,
                python_version=fingerprint_row.python_version,
                tool_name=fingerprint_row.tool_name,
                tool_version=fingerprint_row.tool_version,
                dependency_lock_hash=fingerprint_row.dependency_lock_hash
            )

        return Evidence(
            evidence_id=row.evidence_id,
            contract_id=row.contract_id,
            requirement_id=row.requirement_id,
            repository_id=row.repository_id,
            commit_id=row.commit_id,
            evidence_type=EvidenceType(row.evidence_type),
            verification_method=VerificationMethod(row.verification_method),
            result=EvidenceResult(row.result),
            status=EvidenceStatus(row.status),
            description=row.description,
            observation=row.observation,
            collected_at=row.collected_at,
            integrity=integrity,
            environment=environment,
            # We skip some fields that weren't tracked tightly in early phases but must satisfy pydantic
            source_refs=[],
            target_refs=[],
            provenance="DEFAULT"
        )

    @staticmethod
    def integrity_to_row(evidence_id: str, domain: EvidenceIntegrity) -> EvidenceIntegrityRow:
        return EvidenceIntegrityRow(
            evidence_id=evidence_id,
            evidence_hash=domain.evidence_hash,
            hash_algorithm=domain.hash_algorithm,
            input_hashes=domain.input_hashes,
            parent_evidence_ids=domain.parent_evidence_ids
        )

    @staticmethod
    def fingerprint_to_row(evidence_id: str, domain: EnvironmentFingerprint) -> EnvironmentFingerprintRow:
        return EnvironmentFingerprintRow(
            evidence_id=evidence_id,
            os_name=domain.os_name,
            python_version=domain.python_version,
            tool_name=domain.tool_name,
            tool_version=domain.tool_version,
            dependency_lock_hash=domain.dependency_lock_hash
        )
