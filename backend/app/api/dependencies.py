from enum import Enum
from fastapi import Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.persistence.database import get_db
from app.persistence.models.user import UserRow, WorkspaceMembershipRow
from app.auth.session import validate_session
from app.auth.errors import SessionExpired
from app.auth.csrf import validate_csrf_token


class WorkspaceRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"

# Hierarchy of permissions: OWNER > ADMIN > MEMBER > VIEWER
_ROLE_WEIGHTS = {
    WorkspaceRole.OWNER: 40,
    WorkspaceRole.ADMIN: 30,
    WorkspaceRole.MEMBER: 20,
    WorkspaceRole.VIEWER: 10,
}


def _extract_bearer(request: Request) -> str | None:
    """Extract token from Authorization: Bearer <token> header."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return None

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> UserRow:
    """
    Dependency that extracts the token (Bearer wins over cookie) and validates it.
    Returns the associated UserRow if valid.
    Raises 401 on missing or invalid token.
    """
    bearer_token = _extract_bearer(request)
    
    # Precedence: Bearer token wins if present
    token_to_validate = bearer_token if bearer_token else request.cookies.get("session")
    
    if not token_to_validate:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    try:
        user = await validate_session(token_to_validate, db)
        return user
    except SessionExpired as e:
        raise HTTPException(status_code=401, detail=str(e))

async def require_workspace_member(
    workspace_id: str,
    current_user: UserRow = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> WorkspaceMembershipRow:
    """
    Dependency that enforces workspace isolation.
    Fails with 403 if the user is not a member of the workspace_id.
    """
    stmt = select(WorkspaceMembershipRow).where(
        WorkspaceMembershipRow.workspace_id == workspace_id,
        WorkspaceMembershipRow.user_id == current_user.id
    )
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Forbidden: You are not a member of this workspace")
        
    return membership

def require_workspace_role(required_role: WorkspaceRole):
    """
    Returns a dependency that verifies the user has AT LEAST the required role.
    """
    async def role_checker(
        membership: WorkspaceMembershipRow = Depends(require_workspace_member)
    ) -> WorkspaceMembershipRow:
        # Default to VIEWER (10) if role not found, requiring elevated access to fail safe
        user_weight = _ROLE_WEIGHTS.get(WorkspaceRole(membership.role), 0)
        req_weight = _ROLE_WEIGHTS.get(required_role, 999)
        if user_weight < req_weight:
            raise HTTPException(
                status_code=403, 
                detail=f"Forbidden: Action requires {required_role.value} role"
            )
        return membership
    return role_checker

def csrf_protect(request: Request) -> None:
    """
    Dependency for state-changing routes to enforce CSRF.
    It calls the validate_csrf_token from auth module.
    """
    validate_csrf_token(request)
