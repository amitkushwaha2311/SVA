import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.persistence.database import Base


def _generate_uuid():
    return str(uuid.uuid4())


class RepositoryRow(Base):
    __tablename__ = "repositories"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)
    repository_identifier = Column(String(255), nullable=False)
    provider_type = Column(String(50), nullable=True) # e.g. "git", "local"
    provider_metadata = Column(JSON, nullable=True, default=dict)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    workspace = relationship("WorkspaceRow", back_populates="repositories")
    analyses = relationship("AnalysisRow", back_populates="repository")
    snapshots = relationship("RepositorySnapshotRow", back_populates="repository")
