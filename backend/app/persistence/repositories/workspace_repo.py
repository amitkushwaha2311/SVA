import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.persistence.models.user import WorkspaceRow, WorkspaceMembershipRow


class WorkspaceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str) -> WorkspaceRow:
        ws = WorkspaceRow(id=str(uuid.uuid4()), name=name)
        self.session.add(ws)
        await self.session.flush()
        return ws

    async def get_by_id(self, workspace_id: str) -> Optional[WorkspaceRow]:
        stmt = select(WorkspaceRow).where(WorkspaceRow.id == workspace_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_member(self, workspace_id: str, user_id: str, role: str = "MEMBER") -> WorkspaceMembershipRow:
        member = WorkspaceMembershipRow(workspace_id=workspace_id, user_id=user_id, role=role)
        self.session.add(member)
        await self.session.flush()
        return member

    async def get_members(self, workspace_id: str) -> List[WorkspaceMembershipRow]:
        stmt = select(WorkspaceMembershipRow).where(WorkspaceMembershipRow.workspace_id == workspace_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
