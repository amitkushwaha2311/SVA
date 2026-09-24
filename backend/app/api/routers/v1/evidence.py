"""
Phase 16 v1 API: Evidence endpoints.
Forensic read-only evidence access scoped strictly by workspace.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.persistence.database import get_db
from app.persistence.models.user import UserRow
from app.persistence.models.repository import RepositoryRow
from app.persistence.models.evidence import EvidenceRow, EvidenceIntegrityRow, EnvironmentFingerprintRow
from app.api.dependencies import get_current_user, require_workspace_member
from app.api.routers.v1.schemas import (
    EvidenceResponse,
    EvidenceListResponse,
    EvidenceIntegrityResponse,
    EnvironmentFingerprintResponse,
)

router = APIRouter(prefix="/v1/evidence", tags=["evidence"])


async def _build_evidence_response(ev: EvidenceRow, db: AsyncSession) -> EvidenceResponse:
    integrity = (
        await db.execute(
            select(EvidenceIntegrityRow).where(EvidenceIntegrityRow.evidence_id == ev.evidence_id)
        )
    ).scalar_one_or_none()

    env = (
        await db.execute(
            select(EnvironmentFingerprintRow).where(EnvironmentFingerprintRow.evidence_id == ev.evidence_id)
        )
    ).scalar_one_or_none()

    return EvidenceResponse(
        evidence_id=ev.evidence_id,
        contract_id=ev.contract_id,
        requirement_id=ev.requirement_id,
        repository_id=ev.repository_id,
        commit_id=ev.commit_id,
        evidence_type=ev.evidence_type,
        verification_method=ev.verification_method,
        result=ev.result,
        status=ev.status,
        description=ev.description,
        observation=ev.observation,
        collected_at=ev.collected_at,
        integrity=EvidenceIntegrityResponse.model_validate(integrity) if integrity else None,
        environment=EnvironmentFingerprintResponse.model_validate(env) if env else None,
    )


@router.get("/", response_model=EvidenceListResponse)
async def list_evidence(
    workspace_id: str,
    repository_id: Optional[str] = None,
    contract_id: Optional[str] = None,
    requirement_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List evidence records. Scoped to workspace via repository ownership.
    Never fabricates evidence — returns only what exists in the database.
    """
    await require_workspace_member(workspace_id=workspace_id, current_user=current_user, db=db)

    # Get all repo IDs in this workspace
    repos = (
        await db.execute(
            select(RepositoryRow.id).where(RepositoryRow.workspace_id == workspace_id)
        )
    ).scalars().all()

    if not repos:
        return EvidenceListResponse(items=[], total=0)

    stmt = select(EvidenceRow).where(EvidenceRow.repository_id.in_(repos))

    if repository_id:
        if repository_id not in repos:
            raise HTTPException(status_code=403, detail="Forbidden: Repository not in this workspace")
        stmt = stmt.where(EvidenceRow.repository_id == repository_id)
    if contract_id:
        stmt = stmt.where(EvidenceRow.contract_id == contract_id)
    if requirement_id:
        stmt = stmt.where(EvidenceRow.requirement_id == requirement_id)
    if status:
        stmt = stmt.where(EvidenceRow.status == status)

    total_stmt = stmt
    total = len((await db.execute(total_stmt)).scalars().all())

    stmt = stmt.offset(offset).limit(limit)
    evidence_rows = (await db.execute(stmt)).scalars().all()

    items = [await _build_evidence_response(ev, db) for ev in evidence_rows]
    return EvidenceListResponse(items=items, total=total)


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    workspace_id: str,
    evidence_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await require_workspace_member(workspace_id=workspace_id, current_user=current_user, db=db)

    repos = (
        await db.execute(
            select(RepositoryRow.id).where(RepositoryRow.workspace_id == workspace_id)
        )
    ).scalars().all()

    ev = (
        await db.execute(
            select(EvidenceRow).where(
                EvidenceRow.evidence_id == evidence_id,
                EvidenceRow.repository_id.in_(repos),
            )
        )
    ).scalar_one_or_none()

    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")

    return await _build_evidence_response(ev, db)
