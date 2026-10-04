import asyncio
from app.persistence.database import async_session_maker
from app.persistence.models.analysis import AnalysisRow
from app.persistence.models.job import AnalysisJobRow
from app.orchestration.worker import LocalAnalysisWorker
from app.orchestration.analyzer import AnalysisOrchestrator
import logging

logging.basicConfig(level=logging.DEBUG)

async def main():
    async with async_session_maker() as session:
        # Create a mock job
        job = AnalysisJobRow(
            repository_url="https://github.com/amitkushwaha2311/LIFE-OS.git",
            revision="main",
            provider="git",
            state="QUEUED",
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        
        analysis = AnalysisRow(
            job_id=job.id,
            state="CREATED",
            repository_identifier=job.repository_url,
            revision=job.revision,
            provider_name=job.provider
        )
        session.add(analysis)
        await session.commit()
        
        print(f"Created job {job.id} and analysis {analysis.id}")
        
    worker = LocalAnalysisWorker(poll_interval_seconds=1.0)
    await worker.start()
    await asyncio.sleep(10)
    await worker.stop()

if __name__ == "__main__":
    asyncio.run(main())
