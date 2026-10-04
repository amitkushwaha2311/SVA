import asyncio
import sys
import uuid
import datetime
sys.path.append('c:\\Users\\AMIT KUSHWAHA\\OneDrive\\Desktop\\SVA\\backend')

from app.persistence.database import AsyncSessionLocal
from app.persistence.repositories.repository_repo import AnalysisRepo
from app.persistence.repositories.job_repo import AnalysisJobRepo
from app.persistence.models.repository import RepositoryRow
from app.persistence.models.analysis import AnalysisRow
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RepositoryRow).where(RepositoryRow.repository_identifier == "https://github.com/amitkushwaha2311/LIFE-OS.git"))
        repo = result.scalars().first()
        
        analysis_id = f"sva-{uuid.uuid4().hex[:16]}"
        new_analysis = AnalysisRow(
            id=analysis_id,
            repository_id=repo.id,
            status="CREATED",
            created_at=datetime.datetime.now(datetime.timezone.utc),
            commit_id="main"
        )
        session.add(new_analysis)
        await session.flush()
        
        await AnalysisJobRepo.create_job(
            session=session,
            analysis_id=analysis_id,
            workspace_id=repo.workspace_id,
            created_by="system"
        )
        await session.commit()
        print(f"Enqueued {analysis_id}")
        
        for _ in range(15):
            await asyncio.sleep(2)
            res = await session.execute(select(AnalysisRow).where(AnalysisRow.id == analysis_id))
            a = res.scalars().first()
            print(f"Status: {a.status}, Error: {a.error_message}")
            if a.status in ["COMPLETED", "FAILED"]:
                break

if __name__ == "__main__":
    asyncio.run(main())
