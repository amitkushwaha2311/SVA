import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.persistence.models.job import AnalysisJobRow
from app.persistence.models.analysis import AnalysisRow

logger = logging.getLogger(__name__)

# Configurable limits for job retries and recovery
MAX_ATTEMPTS = 3
STALE_HEARTBEAT_SECONDS = 300  # 5 minutes


class JobRepoError(Exception):
    pass


class JobOwnershipError(JobRepoError):
    """Raised when a worker tries to update a job it no longer owns."""
    pass


class JobStateError(JobRepoError):
    """Raised on illegal job transitions (e.g., cancelling a completed job)."""
    pass


class AnalysisJobRepo:
    
    @staticmethod
    async def create_job(
        session: AsyncSession,
        analysis_id: str,
        workspace_id: str,
        created_by: Optional[str] = None
    ) -> str:
        """
        Enqueue a new analysis job for the given analysis ID.
        """
        # Ensure analysis exists
        result = await session.execute(select(AnalysisRow).where(AnalysisRow.id == analysis_id))
        analysis = result.scalar_one_or_none()
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        job_id = str(uuid.uuid4())
        job = AnalysisJobRow(
            job_id=job_id,
            analysis_id=analysis_id,
            workspace_id=workspace_id,
            status="QUEUED",
            attempt_count=0,
            created_by=created_by,
        )
        session.add(job)
        await session.flush()
        return job_id

    @staticmethod
    async def claim_job(session: AsyncSession, worker_id: str) -> Optional[AnalysisJobRow]:
        """
        Atomically claim a single QUEUED job for the current worker.
        Increments attempt_count securely and sets status to RUNNING.
        """
        # We need an atomic UPDATE ... WHERE status='QUEUED' returning the job.
        # SQLAlchemy supports returning() for SQLite (and Postgres).
        now = datetime.now(timezone.utc)
        
        # Subquery to find one QUEUED job
        subq = (
            select(AnalysisJobRow.job_id)
            .where(AnalysisJobRow.status == "QUEUED")
            .limit(1)
            .scalar_subquery()
        )
        
        stmt = (
            update(AnalysisJobRow)
            .where(AnalysisJobRow.job_id == subq)
            .where(AnalysisJobRow.status == "QUEUED")  # Double-check
            .values(
                status="RUNNING",
                worker_id=worker_id,
                started_at=now,
                last_heartbeat=now,
                attempt_count=AnalysisJobRow.attempt_count + 1
            )
            .returning(AnalysisJobRow)
        )
        
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()
        await session.flush()
        return job

    @staticmethod
    async def heartbeat(session: AsyncSession, job_id: str, worker_id: str) -> None:
        """
        Record a heartbeat. Enforces ownership (must be RUNNING and owned by worker_id).
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(AnalysisJobRow)
            .where(AnalysisJobRow.job_id == job_id)
            .where(AnalysisJobRow.status == "RUNNING")
            .where(AnalysisJobRow.worker_id == worker_id)
            .values(last_heartbeat=now)
        )
        
        result = await session.execute(stmt)
        if result.rowcount == 0:
            # Check why it failed
            check_res = await session.execute(select(AnalysisJobRow).where(AnalysisJobRow.job_id == job_id))
            job = check_res.scalar_one_or_none()
            if not job:
                raise JobRepoError(f"Job {job_id} not found")
            if job.status != "RUNNING":
                raise JobStateError(f"Cannot heartbeat job {job_id} in state {job.status}")
            if job.worker_id != worker_id:
                raise JobOwnershipError(f"Worker {worker_id} does not own job {job_id} (owned by {job.worker_id})")

        await session.flush()

    @staticmethod
    async def complete_job(session: AsyncSession, job_id: str, worker_id: str, success: bool, error: Optional[str] = None) -> None:
        """
        Mark a job as SUCCEEDED or FAILED. Enforces ownership.
        """
        now = datetime.now(timezone.utc)
        target_status = "SUCCEEDED" if success else "FAILED"
        
        stmt = (
            update(AnalysisJobRow)
            .where(AnalysisJobRow.job_id == job_id)
            .where(AnalysisJobRow.status == "RUNNING")
            .where(AnalysisJobRow.worker_id == worker_id)
            .values(
                status=target_status,
                completed_at=now,
                last_error=error
            )
        )
        
        result = await session.execute(stmt)
        if result.rowcount == 0:
            check_res = await session.execute(select(AnalysisJobRow).where(AnalysisJobRow.job_id == job_id))
            job = check_res.scalar_one_or_none()
            if not job:
                raise JobRepoError(f"Job {job_id} not found")
            if job.status != "RUNNING":
                raise JobStateError(f"Cannot complete job {job_id} from state {job.status}")
            if job.worker_id != worker_id:
                raise JobOwnershipError(f"Worker {worker_id} does not own job {job_id}")

        await session.flush()

    @staticmethod
    async def cancel_job(session: AsyncSession, job_id: str) -> bool:
        """
        Mark a job as CANCELLED. If it's already running, it's cooperative 
        (the worker will see the state change and halt if supported).
        Returns True if cancelled, False if it was already terminal.
        """
        now = datetime.now(timezone.utc)
        
        # Check current state first
        result = await session.execute(select(AnalysisJobRow).where(AnalysisJobRow.job_id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise JobRepoError(f"Job {job_id} not found")
            
        if job.status in ("SUCCEEDED", "FAILED", "CANCELLED"):
            return False
            
        stmt = (
            update(AnalysisJobRow)
            .where(AnalysisJobRow.job_id == job_id)
            .where(AnalysisJobRow.status.in_(["CREATED", "QUEUED", "RUNNING"]))
            .values(
                status="CANCELLED",
                completed_at=now
            )
        )
        
        await session.execute(stmt)
        await session.flush()
        return True

    @staticmethod
    async def recover_stale_jobs(session: AsyncSession) -> int:
        """
        Find RUNNING jobs whose heartbeat is older than STALE_HEARTBEAT_SECONDS.
        If attempt_count < MAX_ATTEMPTS, revert to QUEUED for retry.
        If attempt_count >= MAX_ATTEMPTS, mark FAILED.
        Returns the number of recovered jobs.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=STALE_HEARTBEAT_SECONDS)
        
        # Re-queue eligible stale jobs
        requeue_stmt = (
            update(AnalysisJobRow)
            .where(AnalysisJobRow.status == "RUNNING")
            .where(AnalysisJobRow.last_heartbeat < cutoff)
            .where(AnalysisJobRow.attempt_count < MAX_ATTEMPTS)
            .values(
                status="QUEUED",
                worker_id=None,
                # Note: we do not decrement attempt_count. 
                # The next claim will bump it.
            )
        )
        requeue_res = await session.execute(requeue_stmt)
        recovered_count = requeue_res.rowcount
        
        # Fail hopelessly stale jobs
        fail_stmt = (
            update(AnalysisJobRow)
            .where(AnalysisJobRow.status == "RUNNING")
            .where(AnalysisJobRow.last_heartbeat < cutoff)
            .where(AnalysisJobRow.attempt_count >= MAX_ATTEMPTS)
            .values(
                status="FAILED",
                completed_at=datetime.now(timezone.utc),
                last_error="Job abandoned and exceeded max retries"
            )
        )
        fail_res = await session.execute(fail_stmt)
        
        await session.flush()
        return recovered_count + fail_res.rowcount
