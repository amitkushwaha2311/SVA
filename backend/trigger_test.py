import asyncio
import sys
sys.path.append('c:\\Users\\AMIT KUSHWAHA\\OneDrive\\Desktop\\SVA\\backend')

from app.persistence.database import AsyncSessionLocal
from app.persistence.repositories.repository_repo import AnalysisRepo
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        # Find LIFE-OS repo
        from app.persistence.models.repository import RepositoryRow
        result = await session.execute(select(RepositoryRow).where(RepositoryRow.repository_identifier == "https://github.com/amitkushwaha2311/LIFE-OS.git"))
        repo = result.scalars().first()
        if not repo:
            print("Repo not found")
            return
            
        print(f"Triggering analysis for {repo.repository_identifier} in workspace {repo.workspace_id}")
        
        # trigger_analysis is an endpoint, let's call it manually or just use the orchestrator directly.
        # Actually it's easier to use the orchestrator directly if trigger_analysis needs FastAPI BackgroundTasks.
        # Since it uses BackgroundTasks, if we run it here, it will block. 
        from app.orchestration.analyzer import AnalysisOrchestrator
        from app.persistence.models.analysis import AnalysisRow
        import uuid
        import datetime
        analysis_id = f"sva-{uuid.uuid4().hex[:16]}"
        new_analysis = AnalysisRow(
            id=analysis_id,
            repository_id=repo.id,
            status="CREATED",
            created_at=datetime.datetime.now(datetime.timezone.utc),
            commit_id="main"
        )
        session.add(new_analysis)
        await session.commit()
        
        orchestrator = AnalysisOrchestrator(AsyncSessionLocal)
        await orchestrator.run(
            analysis_id=analysis_id,
            repository_id=repo.id,
            provider_name=repo.provider_type,
            repository_identifier=repo.repository_identifier,
            revision="main",
            workspace_id=repo.workspace_id
        )
        
        # Fetch the result
        result = await session.execute(select(AnalysisRow).where(AnalysisRow.id == analysis_id))
        a = result.scalars().first()
        print(f"Analysis completed with status: {a.status}")
        print(f"Error message: {a.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
