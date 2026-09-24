import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.persistence.models.user import UserRow, WorkspaceRow, WorkspaceMembershipRow


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, email: str, password_hash: str, display_name: str) -> UserRow:
        user = UserRow(
            id=str(uuid.uuid4()),
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            status="ACTIVE"
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_email(self, email: str) -> Optional[UserRow]:
        stmt = select(UserRow).where(UserRow.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> Optional[UserRow]:
        stmt = select(UserRow).where(UserRow.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
