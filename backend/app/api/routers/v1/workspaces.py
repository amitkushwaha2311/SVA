"""
Phase 16 v1 API: Workspace listing for authenticated user.
Returns workspaces the current user is a member of.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.persistence.database import get_db
from app.persistence.models.user import UserRow, WorkspaceRow, WorkspaceMembershipRow
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/v1/workspaces", tags=["workspaces"])


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkspaceListResponse(BaseModel):
    items: List[WorkspaceResponse]


@router.get("/", response_model=WorkspaceListResponse)
async def list_my_workspaces(
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all workspaces the authenticated user is a member of."""
    memberships = (
        await db.execute(
            select(WorkspaceMembershipRow, WorkspaceRow)
            .join(WorkspaceRow, WorkspaceMembershipRow.workspace_id == WorkspaceRow.id)
            .where(WorkspaceMembershipRow.user_id == current_user.id)
        )
    ).all()

    items = []
    for membership, workspace in memberships:
        items.append(WorkspaceResponse(
            id=workspace.id,
            name=workspace.name,
            role=membership.role,
            created_at=workspace.created_at,
        ))

    return WorkspaceListResponse(items=items)
