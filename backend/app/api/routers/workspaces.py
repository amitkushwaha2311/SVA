from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.persistence.database import get_db
from app.persistence.models.user import UserRow, WorkspaceRow, WorkspaceMembershipRow
from app.api.dependencies import get_current_user, csrf_protect
from app.auth.schemas import WorkspaceSummary
from pydantic import BaseModel

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

class CreateWorkspaceRequest(BaseModel):
    name: str

@router.get("/", response_model=List[WorkspaceSummary])
async def list_workspaces(current_user: UserRow = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """List workspaces the current user belongs to."""
    stmt = select(WorkspaceMembershipRow).where(WorkspaceMembershipRow.user_id == current_user.id)
    memberships = (await db.execute(stmt)).scalars().all()
    
    ws_ids = [m.workspace_id for m in memberships]
    workspaces = []
    
    if ws_ids:
        ws_stmt = select(WorkspaceRow).where(WorkspaceRow.id.in_(ws_ids))
        ws_rows = (await db.execute(ws_stmt)).scalars().all()
        ws_map = {row.id: row.name for row in ws_rows}
        
        for m in memberships:
            workspaces.append(WorkspaceSummary(
                id=m.workspace_id,
                name=ws_map.get(m.workspace_id, "Unknown"),
                role=m.role
            ))
            
    return workspaces

@router.post("/", response_model=WorkspaceSummary, dependencies=[Depends(csrf_protect)])
async def create_workspace(request: CreateWorkspaceRequest, current_user: UserRow = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Create a new workspace."""
    workspace = WorkspaceRow(name=request.name)
    db.add(workspace)
    await db.flush()
    
    membership = WorkspaceMembershipRow(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role="OWNER"
    )
    db.add(membership)
    await db.commit()
    
    return WorkspaceSummary(
        id=workspace.id,
        name=workspace.name,
        role=membership.role
    )
