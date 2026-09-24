from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.persistence.database import Base


class AnalysisJobRow(Base):
    """
    Durable analysis job. Used by the worker to track background execution.
    Separate from AnalysisRow, which is the semantic outcome of analysis.
    """
    __tablename__ = "analysis_jobs"

    job_id = Column(String(36), primary_key=True)
    analysis_id = Column(String(255), ForeignKey("analyses.id"), nullable=False, index=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False, index=True)
    
    # CREATED, QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELLED
    status = Column(String(50), nullable=False, index=True)
    
    attempt_count = Column(Integer, nullable=False, default=0)
    worker_id = Column(String(255), nullable=True, index=True)
    last_error = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    
    created_by = Column(String(255), nullable=True)

    analysis = relationship("AnalysisRow", backref="jobs")
    workspace = relationship("WorkspaceRow")
