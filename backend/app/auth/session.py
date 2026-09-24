import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.persistence.models.user import SessionRow, UserRow
from app.auth.errors import SessionExpired

RAW_TOKEN_BYTES = 32  # 256-bit token

def _hash_token(raw_token: str) -> str:
    """Hash the raw session token so it is not stored in plaintext."""
    return hashlib.sha256(raw_token.encode()).hexdigest()

async def create_session(user_id: str, db: AsyncSession, user_agent: Optional[str] = None, ip_address: Optional[str] = None) -> str:
    """Create a new session, returning the raw unhashed token."""
    raw_token = secrets.token_hex(RAW_TOKEN_BYTES)
    token_hash = _hash_token(raw_token)
    
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.SESSION_TTL_SECONDS)
    
    session_row = SessionRow(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address
    )
    
    db.add(session_row)
    await db.flush()
    return raw_token

async def validate_session(raw_token: str, db: AsyncSession) -> UserRow:
    """Validate a raw token and return the associated UserRow."""
    token_hash = _hash_token(raw_token)
    
    stmt = select(SessionRow).options(selectinload(SessionRow.user)).where(
        SessionRow.token_hash == token_hash,
        SessionRow.revoked_at.is_(None),
        SessionRow.expires_at > datetime.now(timezone.utc)
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if not session:
        raise SessionExpired("Session is invalid, expired, or revoked.")
        
    return session.user

async def revoke_session(raw_token: str, db: AsyncSession) -> None:
    """Revoke a session by raw token."""
    token_hash = _hash_token(raw_token)
    
    stmt = select(SessionRow).where(SessionRow.token_hash == token_hash)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if session:
        session.revoked_at = datetime.now(timezone.utc)
        await db.flush()
