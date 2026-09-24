import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.persistence.database import Base


def _generate_uuid():
    return str(uuid.uuid4())


class RepositorySnapshotRow(Base):
    __tablename__ = "repository_snapshots"

    snapshot_id = Column(String(36), primary_key=True, default=_generate_uuid)
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    canonical_source = Column(String(255), nullable=False)
    requested_revision = Column(String(255), nullable=False)
    resolved_commit = Column(String(255), nullable=False, index=True)
    content_hash = Column(String(255), nullable=False)
    manifest_hash = Column(String(255), nullable=False)
    analyzer_version = Column(String(50), nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    repository = relationship("RepositoryRow", back_populates="snapshots")
    analyses = relationship("AnalysisRow", back_populates="snapshot")
