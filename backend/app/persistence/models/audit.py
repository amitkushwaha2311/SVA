import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from app.persistence.database import Base


def _generate_uuid():
    return str(uuid.uuid4())


class ExecutionAuditRow(Base):
    """
    ExecutionAudit from Phase 9. Included as nullable table for future use.
    """
    __tablename__ = "execution_audits"

    id = Column(String(36), primary_key=True, default=_generate_uuid)
    execution_id = Column(String(255), nullable=False, index=True)
    contract_id = Column(String(255), nullable=False, index=True)
    obligation_id = Column(String(255), nullable=True, index=True)
    target_id = Column(String(255), nullable=True, index=True)
    repository_id = Column(String(255), nullable=False, index=True)
    commit_id = Column(String(255), nullable=False, index=True)
    
    requested_permissions = Column(JSON, nullable=False, default=list)
    granted_permissions = Column(JSON, nullable=False, default=list)
    
    sandbox_backend = Column(String(50), nullable=False)
    command_identity = Column(String, nullable=False)
    
    start_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime(timezone=True), nullable=True)


class ExecutionResultRow(Base):
    """
    ExecutionResult from Phase 9. Included as nullable table for future use.
    """
    __tablename__ = "execution_results"

    execution_id = Column(String(255), primary_key=True)
    status = Column(String(50), nullable=False)
    exit_code = Column(String(50), nullable=True) # string to support things like 'SIGKILL'
    
    stdout = Column(String, nullable=True)
    stderr = Column(String, nullable=True)
    
    duration_seconds = Column(String, nullable=True) # Using string to preserve exact float text if needed, or Float
    timed_out = Column(String(50), nullable=True)
    resource_limit_exceeded = Column(String(50), nullable=True)
    
    sandbox_backend = Column(String(50), nullable=False)
    policy_id = Column(String(255), nullable=False)
    repository_id = Column(String(255), nullable=False, index=True)
    commit_id = Column(String(255), nullable=False, index=True)
