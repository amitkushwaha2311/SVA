import asyncio
import uuid
import sys
from sqlalchemy import select
from app.persistence.database import async_session_maker
from app.persistence.models.workspace import WorkspaceRow, RepositoryRow
from app.persistence.models.analysis import AnalysisRow
from app.persistence.repositories.job_repo import AnalysisJobRepo

async def trigger_analysis():
    async with async_session_maker() as session:
        async with session.begin():
            # Get a repository
            result = await session.execute(select(RepositoryRow).limit(1))
            repo = result.scalar_one_or_none()
            if not repo:
                print("No repository found")
                return
            
            analysis_id = f"sva-e2e-{uuid.uuid4().hex[:8]}"
            analysis = AnalysisRow(
                id=analysis_id,
                repository_id=repo.id,
                revision="HEAD",
                status="CREATED"
            )
            session.add(analysis)
            
            # create job
            job_id = await AnalysisJobRepo.create_job(session, analysis_id, repo.workspace_id)
            print(f"Triggered analysis {analysis_id} with job {job_id}")

if __name__ == "__main__":
    asyncio.run(trigger_analysis())
