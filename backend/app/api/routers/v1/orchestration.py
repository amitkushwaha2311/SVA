"""
Phase 17: Repository and Analysis Orchestration API
=====================================================

Endpoints:
  POST /api/v1/repositories                     — register a repository
  POST /api/v1/repositories/{id}/analyses       — trigger an analysis (202 Accepted)
  GET  /api/v1/repositories                     — list workspace repositories
  GET  /api/v1/analyses/{id}/status             — poll analysis lifecycle status
  GET  /api/v1/analyses/{id}/summary            — full analysis summary

Authorization chain:
  authenticated user → workspace membership → repository ownership

SECURITY: workspace_id is NEVER trusted from the frontend for authorization.
It is only used as a UX hint; actual scoping is enforced via session user.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.persistence.database import get_db, async_session_maker
from app.persistence.models.user import UserRow, WorkspaceMembershipRow
from app.persistence.models.repository import RepositoryRow
from app.persistence.models.analysis import AnalysisRow
from app.persistence.repositories.repository_repo import RepositoryRepo, AnalysisRepo
from app.persistence.repositories.job_repo import AnalysisJobRepo
from app.api.dependencies import get_current_user, require_workspace_member
from app.orchestration.analyzer import AnalysisOrchestrator, ANALYZER_VERSION

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/orchestration", tags=["orchestration"])


# ─── Request / Response Schemas ───────────────────────────────────────────────

class RegisterRepositoryRequest(BaseModel):
    workspace_id: str
    name: str
    provider: str  # "git" | "local"
    identifier: str  # Git HTTPS URL or local absolute path

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        allowed = {"git", "local"}
        if v not in allowed:
            raise ValueError(f"provider must be one of {allowed}")
        return v

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("identifier cannot be empty")
        return v.strip()


class RepositoryResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    provider_type: Optional[str]
    repository_identifier: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateAnalysisRequest(BaseModel):
    revision: str = "main"  # branch, tag, or commit SHA

    @field_validator("revision")
    @classmethod
    def validate_revision(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("revision cannot be empty")
        return v.strip()


class AnalysisStatusResponse(BaseModel):
    id: str
    repository_id: str
    status: str
    commit_id: str
    snapshot_id: Optional[str]
    analyzer_version: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class RepositoryListResponse(BaseModel):
    items: List[RepositoryResponse]


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/repositories", response_model=RepositoryResponse, status_code=201)
async def register_repository(
    body: RegisterRepositoryRequest,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RepositoryResponse:
    """Register a repository in a workspace. Validates workspace membership."""
    await require_workspace_member(workspace_id=body.workspace_id, current_user=current_user, db=db)

    repo_repo = RepositoryRepo(db)
    repo = await repo_repo.create(
        workspace_id=body.workspace_id,
        name=body.name,
        source_type=body.provider,
        identifier=body.identifier,
        provider_type=body.provider,
        provider_metadata={},
    )
    await db.commit()
    await db.refresh(repo)
    return RepositoryResponse.model_validate(repo)


@router.get("/repositories", response_model=RepositoryListResponse)
async def list_repositories(
    workspace_id: str = Query(...),
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RepositoryListResponse:
    """List all repositories in a workspace the current user is a member of."""
    await require_workspace_member(workspace_id=workspace_id, current_user=current_user, db=db)

    repo_repo = RepositoryRepo(db)
    repos = await repo_repo.get_by_workspace(workspace_id)
    return RepositoryListResponse(items=[RepositoryResponse.model_validate(r) for r in repos])


@router.post("/repositories/{repository_id}/analyses", response_model=AnalysisStatusResponse, status_code=202)
async def create_analysis(
    repository_id: str,
    body: CreateAnalysisRequest,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalysisStatusResponse:
    """
    Trigger an analysis for a repository revision.
    
    Returns 202 Accepted immediately. The analysis runs in the background.
    Poll /analyses/{id}/status for lifecycle updates.
    
    NOTE: BackgroundTasks is not durable. A process restart will interrupt
    an in-progress analysis, leaving it in an intermediate state.
    """
    # Verify the repository belongs to a workspace the user is a member of
    repo_repo = RepositoryRepo(db)
    repo = await repo_repo.get_by_id(repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    await require_workspace_member(workspace_id=repo.workspace_id, current_user=current_user, db=db)

    # Generate a deterministic analysis ID
    # Using repository_id + revision + timestamp to ensure uniqueness while being traceable
    analysis_id = f"sva-{uuid.uuid4().hex[:16]}"

    # Create the analysis row in CREATED state
    analysis_repo = AnalysisRepo(db)
    analysis = await analysis_repo.create(
        analysis_id=analysis_id,
        repository_id=repository_id,
        commit_id=body.revision,  # Will be resolved to actual SHA during ingestion
        status="CREATED",
        analyzer_version=ANALYZER_VERSION,
    )
    
    # Enqueue a durable job
    await AnalysisJobRepo.create_job(
        session=db,
        analysis_id=analysis_id,
        workspace_id=repo.workspace_id,
        created_by=current_user.id
    )
    await db.commit()

    await db.refresh(analysis)
    return AnalysisStatusResponse.model_validate(analysis)


@router.get("/analyses/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalysisStatusResponse:
    """Poll the lifecycle state of an analysis. Enforces ownership through repository workspace."""
    analysis = await _get_authorized_analysis(analysis_id, current_user, db)
    return AnalysisStatusResponse.model_validate(analysis)


@router.delete("/analyses/{analysis_id}", status_code=204)
async def cancel_analysis(
    analysis_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Request cancellation of a queued or running analysis.
    
    LIMITATION: With BackgroundTasks, cancellation marks the DB state CANCELLED
    but cannot interrupt the running background coroutine. A durable queue
    would be required for true preemption.
    """
    analysis = await _get_authorized_analysis(analysis_id, current_user, db)

    cancellable = {"CREATED", "QUEUED", "INGESTING", "ANALYZING", "VERIFYING"}
    if analysis.status not in cancellable:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel analysis in state: {analysis.status}"
        )

    analysis_repo = AnalysisRepo(db)
    await analysis_repo.update_status(analysis_id, "CANCELLED", completed_at=datetime.now(timezone.utc))
    
    # Also cancel the durable job if one exists and is not terminal
    from app.persistence.models.job import AnalysisJobRow
    result = await db.execute(select(AnalysisJobRow).where(AnalysisJobRow.analysis_id == analysis_id))
    job = result.scalar_one_or_none()
    if job:
        await AnalysisJobRepo.cancel_job(db, job.job_id)

    await db.commit()


# ─── Helper ───────────────────────────────────────────────────────────────────

async def _get_authorized_analysis(
    analysis_id: str,
    current_user: UserRow,
    db: AsyncSession,
) -> AnalysisRow:
    """Fetch analysis and verify user has workspace access to its repository."""
    analysis_repo = AnalysisRepo(db)
    analysis = await analysis_repo.get_by_id(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    repo_repo = RepositoryRepo(db)
    repo = await repo_repo.get_by_id(analysis.repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    await require_workspace_member(workspace_id=repo.workspace_id, current_user=current_user, db=db)
    return analysis
