import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.persistence.database import async_session_maker
from app.persistence.models.analysis import AnalysisRow
from app.persistence.models.job import AnalysisJobRow
from app.persistence.repositories.repository_repo import RepositoryRepo, AnalysisRepo
from app.persistence.repositories.workspace_repo import WorkspaceRepository
from app.persistence.repositories.job_repo import (
    AnalysisJobRepo,
    JobOwnershipError,
    JobStateError,
    JobRepoError,
    MAX_ATTEMPTS,
    STALE_HEARTBEAT_SECONDS
)

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


@pytest.mark.asyncio
async def test_job_repo_atomic_claim(db: AsyncSession):
    ws, analysis = await setup_analysis(db)
    
    job_id = await AnalysisJobRepo.create_job(db, analysis.id, ws.id, created_by="u1")
    await db.commit()
    
    # 1. Claim
    job = await AnalysisJobRepo.claim_job(db, "worker-1")
    await db.commit()
    
    assert job is not None
    assert job.job_id == job_id
    assert job.status == "RUNNING"
    assert job.worker_id == "worker-1"
    assert job.attempt_count == 1
    assert job.started_at is not None
    assert job.last_heartbeat is not None

    # 2. Try to claim again (should be None)
    job2 = await AnalysisJobRepo.claim_job(db, "worker-2")
    await db.commit()
    assert job2 is None


@pytest.mark.asyncio
async def test_concurrent_claim(db: AsyncSession, engine):
    ws, analysis = await setup_analysis(db)
    
    job_id = await AnalysisJobRepo.create_job(db, analysis.id, ws.id)
    await db.commit()

    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def claim_task(worker_id):
        # We need independent sessions for concurrency test to avoid locking
        async with SessionLocal() as session:
            async with session.begin():
                job = await AnalysisJobRepo.claim_job(session, worker_id)
                # Keep it mapped to local session by returning ID or True
                return job.job_id if job else None

    # 10 workers try to claim the single job
    results = await asyncio.gather(*(claim_task(f"w-{i}") for i in range(10)))
    
    claimed = [r for r in results if r is not None]
    assert len(claimed) == 1


@pytest.mark.asyncio
async def test_heartbeat_ownership(db: AsyncSession):
    ws, analysis = await setup_analysis(db)
    
    job_id = await AnalysisJobRepo.create_job(db, analysis.id, ws.id)
    await db.commit()
    
    await AnalysisJobRepo.claim_job(db, "worker-1")
    await db.commit()

    # Valid heartbeat
    await AnalysisJobRepo.heartbeat(db, job_id, "worker-1")
    await db.commit()
            
    # Invalid worker
    with pytest.raises(JobOwnershipError):
        await AnalysisJobRepo.heartbeat(db, job_id, "worker-2")
        await db.commit()


@pytest.mark.asyncio
async def test_complete_job_ownership(db: AsyncSession):
    ws, analysis = await setup_analysis(db)
    
    job_id = await AnalysisJobRepo.create_job(db, analysis.id, ws.id)
    await db.commit()
    
    await AnalysisJobRepo.claim_job(db, "worker-1")
    await db.commit()

    # Attempt to complete with wrong worker
    with pytest.raises(JobOwnershipError):
        await AnalysisJobRepo.complete_job(db, job_id, "worker-2", success=True)
                
    # Complete with correct worker
    await AnalysisJobRepo.complete_job(db, job_id, "worker-1", success=True)
    await db.commit()
            
    # Attempt to heartbeat a completed job
    with pytest.raises(JobStateError):
        await AnalysisJobRepo.heartbeat(db, job_id, "worker-1")


@pytest.mark.asyncio
async def test_stale_job_recovery(db: AsyncSession):
    ws, analysis = await setup_analysis(db)
    
    job_id = await AnalysisJobRepo.create_job(db, analysis.id, ws.id)
    await db.commit()
    
    job = await AnalysisJobRepo.claim_job(db, "worker-1")
    # Manually make it stale
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=STALE_HEARTBEAT_SECONDS + 10)
    job.last_heartbeat = stale_time
    await db.commit()

    # Recover
    recovered = await AnalysisJobRepo.recover_stale_jobs(db)
    await db.commit()
    assert recovered == 1

    # Attempt to claim by another worker
    job2 = await AnalysisJobRepo.claim_job(db, "worker-2")
    await db.commit()
    
    assert job2 is not None
    assert job2.worker_id == "worker-2"
    assert job2.attempt_count == 2
            
    # Original worker cannot complete it now
    with pytest.raises(JobOwnershipError):
        await AnalysisJobRepo.complete_job(db, job_id, "worker-1", success=True)


@pytest.mark.asyncio
async def test_max_attempts(db: AsyncSession):
    ws, analysis = await setup_analysis(db)
    
    job_id = await AnalysisJobRepo.create_job(db, analysis.id, ws.id)
    await db.commit()
            
    job = await AnalysisJobRepo.claim_job(db, "worker-1")
    job.attempt_count = MAX_ATTEMPTS
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=STALE_HEARTBEAT_SECONDS + 10)
    job.last_heartbeat = stale_time
    await db.commit()

    # Recover
    await AnalysisJobRepo.recover_stale_jobs(db)
    await db.commit()

    from sqlalchemy import select
    result = await db.execute(select(AnalysisJobRow).where(AnalysisJobRow.job_id == job_id))
    job = result.scalar_one_or_none()
    assert job.status == "FAILED"
    assert job.worker_id == "worker-1" # remains worker-1 or None
            
    # Cannot be claimed again
    job2 = await AnalysisJobRepo.claim_job(db, "worker-2")
    assert job2 is None
