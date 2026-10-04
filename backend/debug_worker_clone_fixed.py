import asyncio
from app.persistence.database import async_session_maker
from app.persistence.models.job import AnalysisJobRow
from app.persistence.models.analysis import AnalysisRow
from app.persistence.models.workspace import WorkspaceRow
from app.orchestration.worker import LocalAnalysisWorker
import uuid

async def main():
    async with async_session_maker() as session:
        ws = WorkspaceRow(name='test_worker_ws')
        session.add(ws)
        await session.commit()
        await session.refresh(ws)
        
        analysis_id = str(uuid.uuid4())
        
        job = AnalysisJobRow(
            job_id=str(uuid.uuid4()),
            analysis_id=analysis_id,
            workspace_id=ws.id,
            status="QUEUED"
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        
        analysis = AnalysisRow(
            id=analysis_id,
            repository_id=str(uuid.uuid4()), # Fake
            commit_id="main",
            status="CREATED"
        )
        session.add(analysis)
        
        # We need a repository for the analysis
        from app.persistence.models.repository import RepositoryRow
        repo = RepositoryRow(
            id=analysis.repository_id,
            workspace_id=ws.id,
            provider_type="git",
            repository_identifier="https://github.com/amitkushwaha2311/LIFE-OS.git",
            name="testrepo"
        )
        session.add(repo)
        await session.commit()
        
    worker = LocalAnalysisWorker(poll_interval_seconds=1.0)
    await worker.start()
    await asyncio.sleep(5)
    await worker.stop()
    
    async with async_session_maker() as session:
        from sqlalchemy import select
        job_result = await session.execute(select(AnalysisJobRow).where(AnalysisJobRow.job_id == job.job_id))
        j = job_result.scalar_one()
        print("Job status:", j.status, "Error:", j.last_error)

asyncio.run(main())
