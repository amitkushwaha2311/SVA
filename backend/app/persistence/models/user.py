import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.persistence.database import Base


def _generate_uuid():
    return str(uuid.uuid4())


class UserRow(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="ACTIVE")
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    workspace_memberships = relationship("WorkspaceMembershipRow", back_populates="user")
    sessions = relationship("SessionRow", back_populates="user")


class SessionRow(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    user_agent = Column(String(512), nullable=True)
    ip_address = Column(String(45), nullable=True)

    user = relationship("UserRow", back_populates="sessions")


class WorkspaceRow(Base):
    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    name = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    members = relationship("WorkspaceMembershipRow", back_populates="workspace")
    repositories = relationship("RepositoryRow", back_populates="workspace")


class WorkspaceMembershipRow(Base):
    __tablename__ = "workspace_memberships"

    workspace_id = Column(String(36), ForeignKey("workspaces.id"), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    role = Column(String(50), nullable=False, default="MEMBER")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    workspace = relationship("WorkspaceRow", back_populates="members")
    user = relationship("UserRow", back_populates="workspace_memberships")
