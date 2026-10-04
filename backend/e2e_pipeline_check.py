"""
E2E Pipeline Check
==================
Triggers a real local-provider analysis, runs the worker, and reports results.
Creates a minimal workspace+repo if one does not already exist.
"""
import asyncio
import logging
import os
import uuid
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.persistence.database import engine, Base, async_session_maker
from app.persistence.models.repository import RepositoryRow
from app.persistence.models.analysis import AnalysisRow
from app.persistence.models.job import AnalysisJobRow
from app.persistence.repositories.job_repo import AnalysisJobRepo

# Import all models so metadata is fully populated
import app.persistence.models  # noqa

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("e2e_pipeline_check")


async def ensure_workspace_and_repo(session) -> RepositoryRow:
    """Return an existing local-provider repo, or create workspace+repo."""
    # Check existing local repo
    result = await session.execute(
        select(RepositoryRow).where(RepositoryRow.provider_type == "local").limit(1)
    )
    repo = result.scalar_one_or_none()
    if repo:
        return repo

    # Check any repo
    result = await session.execute(select(RepositoryRow).limit(1))
    repo = result.scalar_one_or_none()
    if repo:
        return repo

    # Need a workspace first
    ws_result = await session.execute(text("SELECT id FROM workspaces LIMIT 1"))
    ws_row = ws_result.fetchone()

    if not ws_row:
        # Create workspace
        ws_id = f"ws-e2e-{uuid.uuid4().hex[:8]}"
        await session.execute(
            text("INSERT INTO workspaces (id, name, created_at) VALUES (:id, :name, CURRENT_TIMESTAMP)"),
            {"id": ws_id, "name": "E2E-Workspace"}
        )
        await session.flush()
        ws_id_used = ws_id
        logger.info("Created workspace: %s", ws_id_used)
    else:
        ws_id_used = ws_row[0]

    # Create local repository
    repo = RepositoryRow(
        id=f"repo-e2e-{uuid.uuid4().hex[:8]}",
        workspace_id=ws_id_used,
        name="E2E-Local-Repo",
        source_type="local",
        provider_type="local",
        repository_identifier=os.path.abspath("."),
    )
    session.add(repo)
    await session.flush()
    logger.info("Created repository: %s -> %s", repo.id, repo.repository_identifier)
    return repo


async def run_e2e():
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    analysis_id = None
    job_id = None

    async with async_session_maker() as session:
        async with session.begin():
            repo = await ensure_workspace_and_repo(session)

            # Create analysis
            analysis_id = f"e2e-check-{uuid.uuid4().hex[:8]}"
            analysis = AnalysisRow(
                id=analysis_id,
                repository_id=repo.id,
                status="CREATED",
                commit_id="HEAD",  # placeholder; worker/orchestrator will resolve it
            )
            session.add(analysis)
            await session.flush()

            # Create job
            job_id = await AnalysisJobRepo.create_job(session, analysis_id, repo.workspace_id)
            logger.info("Created analysis: %s", analysis_id)
            logger.info("Created job: %s", job_id)
            logger.info("Repository: %s (provider=%s)", repo.repository_identifier, repo.provider_type)

    # Run the worker
    from app.orchestration.worker import LocalAnalysisWorker
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    worker = LocalAnalysisWorker(session_factory=SessionLocal, poll_interval_seconds=1.0)
    await worker.start()
    logger.info("Worker started, waiting up to 90s for analysis to complete...")

    # Poll for completion
    for _ in range(90):
        await asyncio.sleep(1)
        async with async_session_maker() as session:
            result = await session.execute(
                select(AnalysisRow).where(AnalysisRow.id == analysis_id)
            )
            a = result.scalar_one_or_none()
            if a and a.status in ("COMPLETED", "FAILED", "CANCELLED"):
                logger.info("Analysis reached terminal state: %s", a.status)
                break

    await worker.stop()

    # Final report
    async with async_session_maker() as session:
        result = await session.execute(select(AnalysisRow).where(AnalysisRow.id == analysis_id))
        a = result.scalar_one_or_none()
        result2 = await session.execute(
            select(AnalysisJobRow).where(AnalysisJobRow.analysis_id == analysis_id)
        )
        j = result2.scalar_one_or_none()

    print("\n" + "=" * 60)
    print("E2E ANALYSIS RESULT")
    print("=" * 60)
    print(f"  Analysis ID:     {analysis_id}")
    print(f"  Analysis status: {a.status if a else 'NOT FOUND'}")
    print(f"  Analysis error:  {a.error_message if a else 'N/A'}")
    print(f"  Job status:      {j.status if j else 'NOT FOUND'}")
    print(f"  Job attempts:    {j.attempt_count if j else 'N/A'}")
    if j and j.last_error:
        print(f"  Job last error:  {j.last_error[:500]}")
    print("=" * 60)

    if a and a.status == "COMPLETED" and j and j.status == "SUCCEEDED":
        print("✅ E2E PASSED: Analysis COMPLETED, Job SUCCEEDED")
        return True
    elif a and a.status == "FAILED":
        print(f"❌ E2E FAILED: Analysis FAILED — {a.error_message}")
        return False
    else:
        status_a = a.status if a else "N/A"
        status_j = j.status if j else "N/A"
        print(f"⚠️  E2E STATUS: Analysis={status_a}, Job={status_j}")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_e2e())
    import sys
    sys.exit(0 if success else 1)
