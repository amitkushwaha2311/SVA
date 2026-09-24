import pytest
import asyncio
import uuid
from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.persistence.models.job import AnalysisJobRow
from app.persistence.models.analysis import AnalysisRow
from app.persistence.repositories.repository_repo import RepositoryRepo, AnalysisRepo
from app.persistence.repositories.workspace_repo import WorkspaceRepository
from app.persistence.repositories.job_repo import AnalysisJobRepo
from app.orchestration.worker import LocalAnalysisWorker


async def setup_analysis(db: AsyncSession):
    ws_repo = WorkspaceRepository(db)
    repo_repo = RepositoryRepo(db)
    analysis_repo = AnalysisRepo(db)

    ws = await ws_repo.create("WS")
    repo = await repo_repo.create(ws.id, "my-repo", "git", "https://github.com/x/y")
    analysis_id = f"test-analysis-{uuid.uuid4()}"
    analysis = await analysis_repo.create(
        analysis_id, repo.id, "commit-abc", "CREATED"
    )
    await db.commit()
    return ws, analysis


async def read_job(SessionLocal, job_id: str):
    """Read job from a fresh session to avoid stale cache."""
    async with SessionLocal() as session:
        result = await session.execute(
            select(AnalysisJobRow).where(AnalysisJobRow.job_id == job_id)
        )
        return result.scalar_one_or_none()


@pytest.mark.asyncio
async def test_worker_cancellation(db: AsyncSession, engine):
    ws, analysis = await setup_analysis(db)
    job_id = await AnalysisJobRepo.create_job(db, analysis.id, ws.id)
    await db.commit()

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    worker = LocalAnalysisWorker(session_factory=SessionLocal, poll_interval_seconds=0.1)

    # Patch the orchestrator run method so it takes a while
    async def slow_run(*args, **kwargs):
        # Cancel the job from DB while it's running (cooperative cancellation)
        async with SessionLocal() as session:
            async with session.begin():
                await AnalysisJobRepo.cancel_job(session, job_id)
        # Sleep long enough that the heartbeat (accelerated to 0.1s) will fire
        await asyncio.sleep(10)

    original_sleep = asyncio.sleep

    async def fast_sleep(delay):
        if delay == 60:
            await original_sleep(0.05)
        else:
            await original_sleep(delay)

    with patch("app.orchestration.analyzer.AnalysisOrchestrator.run", side_effect=slow_run):
        with patch("app.orchestration.worker.asyncio.sleep", side_effect=fast_sleep):
            await worker.start()
            await asyncio.sleep(1.0)  # Give heartbeat time to fire and cancel the task
            await worker.stop()

    job = await read_job(SessionLocal, job_id)
    assert job.status == "CANCELLED"


@pytest.mark.asyncio
async def test_worker_semantic_separation(db: AsyncSession, engine):
    """A verification VIOLATED/UNKNOWN is NOT a job failure. Normal orchestrator
    completion (no exception) → job SUCCEEDED regardless of semantic outcome."""
    ws, analysis = await setup_analysis(db)
    job_id = await AnalysisJobRepo.create_job(db, analysis.id, ws.id)
    await db.commit()

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    worker = LocalAnalysisWorker(session_factory=SessionLocal, poll_interval_seconds=0.1)

    async def fast_run(*args, **kwargs):
        pass  # Orchestrator returns normally — semantic outcome irrelevant to job status

    with patch("app.orchestration.analyzer.AnalysisOrchestrator.run", side_effect=fast_run):
        await worker.start()
        await asyncio.sleep(0.5)
        await worker.stop()

    job = await read_job(SessionLocal, job_id)
    assert job.status == "SUCCEEDED"
    assert job.last_error is None


@pytest.mark.asyncio
async def test_worker_infrastructure_failure(db: AsyncSession, engine):
    """Infrastructure crash (exception from orchestrator) → job FAILED with last_error."""
    ws, analysis = await setup_analysis(db)
    job_id = await AnalysisJobRepo.create_job(db, analysis.id, ws.id)
    await db.commit()

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    worker = LocalAnalysisWorker(session_factory=SessionLocal, poll_interval_seconds=0.1)

    async def fail_run(*args, **kwargs):
        raise ValueError("Database connection lost")

    with patch("app.orchestration.analyzer.AnalysisOrchestrator.run", side_effect=fail_run):
        await worker.start()
        await asyncio.sleep(0.5)
        await worker.stop()

    job = await read_job(SessionLocal, job_id)
    assert job.status == "FAILED"
    assert "Database connection lost" in job.last_error


@pytest.mark.asyncio
async def test_worker_retry_idempotency(db: AsyncSession, engine):
    """Failed jobs can be re-queued and retried; second attempt succeeds independently."""
    ws, analysis = await setup_analysis(db)
    job_id = await AnalysisJobRepo.create_job(db, analysis.id, ws.id)
    await db.commit()

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    fail_count = {"val": 0}

    async def flaky_run(*args, **kwargs):
        if fail_count["val"] == 0:
            fail_count["val"] += 1
            raise ValueError("First run fails")
        # Second run: succeeds

    # --- Run 1: fails ---
    worker1 = LocalAnalysisWorker(session_factory=SessionLocal, poll_interval_seconds=0.1)
    with patch("app.orchestration.analyzer.AnalysisOrchestrator.run", side_effect=flaky_run):
        await worker1.start()
        await asyncio.sleep(0.5)
        await worker1.stop()

    job = await read_job(SessionLocal, job_id)
    assert job.status == "FAILED"
    assert job.attempt_count == 1

    # Re-queue for retry
    async with SessionLocal() as session:
        async with session.begin():
            result = await session.execute(
                select(AnalysisJobRow).where(AnalysisJobRow.job_id == job_id)
            )
            j = result.scalar_one()
            j.status = "QUEUED"

    # --- Run 2: succeeds ---
    worker2 = LocalAnalysisWorker(session_factory=SessionLocal, poll_interval_seconds=0.1)
    with patch("app.orchestration.analyzer.AnalysisOrchestrator.run", side_effect=flaky_run):
        await worker2.start()
        await asyncio.sleep(0.5)
        await worker2.stop()

    job = await read_job(SessionLocal, job_id)
    assert job.status == "SUCCEEDED"
    assert job.attempt_count == 2
