from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.persistence.database import Base


class AnalysisRow(Base):
    __tablename__ = "analyses"

    id = Column(String(255), primary_key=True)  # SVA analysis_id is a deterministic string
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=False, index=True)
    commit_id = Column(String(255), nullable=False, index=True)
    snapshot_id = Column(String(36), ForeignKey("repository_snapshots.snapshot_id"), nullable=True, index=True)
    status = Column(String(50), nullable=False)
    analyzer_version = Column(String(50), nullable=True)
    error_message = Column(String, nullable=True)
    
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    repository = relationship("RepositoryRow", back_populates="analyses")
    snapshot = relationship("RepositorySnapshotRow", back_populates="analyses")
