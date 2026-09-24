from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.persistence.database import get_db
from app.persistence.models.user import UserRow, WorkspaceMembershipRow
from app.persistence.models.repository import RepositoryRow
from app.api.dependencies import get_current_user, require_workspace_member, csrf_protect
from app.api.routers.v1.schemas import RepositoryResponse, RepositoryListResponse

router = APIRouter(prefix="/v1/repositories", tags=["repositories"])

@router.get("/", response_model=RepositoryListResponse)
async def list_repositories(
    workspace_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all repositories for a given workspace."""
    # Enforce authorization
    await require_workspace_member(workspace_id=workspace_id, current_user=current_user, db=db)
    
    stmt = select(RepositoryRow).where(RepositoryRow.workspace_id == workspace_id)
    repositories = (await db.execute(stmt)).scalars().all()
    
    return RepositoryListResponse(repositories=repositories)

@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    workspace_id: str,
    repository_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get details for a specific repository."""
    await require_workspace_member(workspace_id=workspace_id, current_user=current_user, db=db)
    
    stmt = select(RepositoryRow).where(
        RepositoryRow.id == repository_id,
        RepositoryRow.workspace_id == workspace_id
    )
    repo = (await db.execute(stmt)).scalar_one_or_none()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
        
    return repo
