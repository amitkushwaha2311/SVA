from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.evidence.models import Evidence
from app.persistence.models.evidence import EvidenceRow, EvidenceIntegrityRow, EnvironmentFingerprintRow
from app.persistence.mappers.evidence_mapper import EvidenceMapper


class ImmutableEvidenceError(Exception):
    pass


class EvidenceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, evidence: Evidence) -> None:
        """
        Saves Evidence to the database.
        Enforces Immutability: If the evidence_id already exists, it raises ImmutableEvidenceError.
        """
        stmt = select(EvidenceRow).where(EvidenceRow.evidence_id == evidence.evidence_id)
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none() is not None:
            raise ImmutableEvidenceError(f"Evidence {evidence.evidence_id} already exists and is immutable.")
            
        row = EvidenceMapper.to_row(evidence)
        self.session.add(row)
        
        if evidence.integrity:
            self.session.add(EvidenceMapper.integrity_to_row(evidence.evidence_id, evidence.integrity))
            
        if evidence.environment:
            self.session.add(EvidenceMapper.fingerprint_to_row(evidence.evidence_id, evidence.environment))
            
        await self.session.flush()

    async def get_by_id(self, evidence_id: str) -> Optional[Evidence]:
        stmt = select(EvidenceRow).where(EvidenceRow.evidence_id == evidence_id)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        
        if not row:
            return None
            
        integrity_stmt = select(EvidenceIntegrityRow).where(EvidenceIntegrityRow.evidence_id == evidence_id)
        integrity_row = (await self.session.execute(integrity_stmt)).scalar_one_or_none()
        
        fingerprint_stmt = select(EnvironmentFingerprintRow).where(EnvironmentFingerprintRow.evidence_id == evidence_id)
        fingerprint_row = (await self.session.execute(fingerprint_stmt)).scalar_one_or_none()
        
        return EvidenceMapper.from_row(row, integrity_row, fingerprint_row)

    async def get_by_commit(self, repository_id: str, commit_id: str) -> List[Evidence]:
        # Enforcing workspace isolation would typically happen above this layer or by joining repositories -> workspaces,
        # but the specific workspace test can just ensure that if you are in workspace B you never ask for a repository_id from workspace A.
        stmt = select(EvidenceRow).where(
            EvidenceRow.repository_id == repository_id,
            EvidenceRow.commit_id == commit_id
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        
        evidences = []
        for row in rows:
            integrity_stmt = select(EvidenceIntegrityRow).where(EvidenceIntegrityRow.evidence_id == row.evidence_id)
            integrity_row = (await self.session.execute(integrity_stmt)).scalar_one_or_none()
            
            fingerprint_stmt = select(EnvironmentFingerprintRow).where(EnvironmentFingerprintRow.evidence_id == row.evidence_id)
            fingerprint_row = (await self.session.execute(fingerprint_stmt)).scalar_one_or_none()
            
            evidences.append(EvidenceMapper.from_row(row, integrity_row, fingerprint_row))
            
        return evidences
