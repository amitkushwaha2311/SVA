import uuid
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.persistence.models.repository import RepositoryRow
from app.persistence.models.analysis import AnalysisRow
from app.persistence.models.snapshot import RepositorySnapshotRow


class RepositoryRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        workspace_id: str,
        name: str,
        source_type: str,
        identifier: str,
        provider_type: Optional[str] = None,
        provider_metadata: Optional[dict] = None,
    ) -> RepositoryRow:
        repo = RepositoryRow(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            name=name,
            source_type=source_type,
            repository_identifier=identifier,
            provider_type=provider_type,
            provider_metadata=provider_metadata or {},
        )
        self.session.add(repo)
        await self.session.flush()
        return repo

    async def get_by_workspace(self, workspace_id: str) -> List[RepositoryRow]:
        stmt = select(RepositoryRow).where(RepositoryRow.workspace_id == workspace_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, repository_id: str) -> Optional[RepositoryRow]:
        stmt = select(RepositoryRow).where(RepositoryRow.id == repository_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class RepositorySnapshotRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        repository_id: str,
        provider: str,
        canonical_source: str,
        requested_revision: str,
        resolved_commit: str,
        content_hash: str,
        manifest_hash: str,
        analyzer_version: str,
    ) -> RepositorySnapshotRow:
        snapshot = RepositorySnapshotRow(
            snapshot_id=str(uuid.uuid4()),
            repository_id=repository_id,
            provider=provider,
            canonical_source=canonical_source,
            requested_revision=requested_revision,
            resolved_commit=resolved_commit,
            content_hash=content_hash,
            manifest_hash=manifest_hash,
            analyzer_version=analyzer_version,
        )
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def get_by_id(self, snapshot_id: str) -> Optional[RepositorySnapshotRow]:
        stmt = select(RepositorySnapshotRow).where(RepositorySnapshotRow.snapshot_id == snapshot_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class AnalysisRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        analysis_id: str,
        repository_id: str,
        commit_id: str,
        status: str,
        snapshot_id: Optional[str] = None,
        analyzer_version: Optional[str] = None,
    ) -> AnalysisRow:
        row = AnalysisRow(
            id=analysis_id,
            repository_id=repository_id,
            commit_id=commit_id,
            status=status,
            snapshot_id=snapshot_id,
            analyzer_version=analyzer_version,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def update_status(
        self,
        analysis_id: str,
        status: str,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[AnalysisRow]:
        row = await self.get_by_id(analysis_id)
        if row:
            row.status = status
            if error_message is not None:
                row.error_message = error_message
            if completed_at is not None:
                row.completed_at = completed_at
            await self.session.flush()
        return row

    async def get_by_id(self, analysis_id: str) -> Optional[AnalysisRow]:
        stmt = select(AnalysisRow).where(AnalysisRow.id == analysis_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_repository(self, repository_id: str) -> List[AnalysisRow]:
        stmt = select(AnalysisRow).where(AnalysisRow.repository_id == repository_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
