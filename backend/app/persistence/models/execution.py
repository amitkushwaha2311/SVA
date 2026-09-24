from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.persistence.database import Base


class ExecutionRecordRow(Base):
    __tablename__ = "executions"

    execution_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("analysis_jobs.job_id", ondelete="CASCADE"), index=True)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), index=True)
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False)
    commit_id: Mapped[str] = mapped_column(String(40), nullable=False)
    verification_target_id: Mapped[str] = mapped_column(String(36), nullable=False)
    obligation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    contract_id: Mapped[str] = mapped_column(String(36), nullable=False)

    policy_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sandbox_backend: Mapped[str] = mapped_column(String(64), nullable=False)
    
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    start_time: Mapped[str] = mapped_column(String(64), nullable=False)
    end_time: Mapped[str] = mapped_column(String(64), nullable=False)
    
    stdout_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stderr_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    resource_observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    environment_fingerprint: Mapped[str | None] = mapped_column(Text, nullable=True)
