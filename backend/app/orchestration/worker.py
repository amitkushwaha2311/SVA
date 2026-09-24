import asyncio
import logging
import traceback
import uuid
from typing import Protocol, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.database import async_session_maker
from app.persistence.models.analysis import AnalysisRow
from app.persistence.repositories.job_repo import (
    AnalysisJobRepo,
    JobOwnershipError,
    JobStateError,
    JobRepoError
)
from app.orchestration.analyzer import AnalysisOrchestrator

logger = logging.getLogger(__name__)


class AnalysisWorker(Protocol):
    async def start(self) -> None:
        """Start accepting and processing jobs."""
        pass
        
    async def stop(self) -> None:
        """Stop accepting new jobs and gracefully shutdown."""
        pass


class LocalAnalysisWorker(AnalysisWorker):
    """
    A local worker that polls the database for QUEUED jobs.
    Uses AnalysisJobRepo for atomic claiming and heartbeating.
    """
    def __init__(self, session_factory=async_session_maker, poll_interval_seconds: float = 2.0):
        self.session_factory = session_factory
        self.poll_interval = poll_interval_seconds
        self.worker_id = f"local-worker-{uuid.uuid4()}"
        self._running = False
        self._loop_task: Optional[asyncio.Task] = None
        self._active_jobs: set[asyncio.Task] = set()

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._loop_task = asyncio.create_task(self._poll_loop())
        logger.info("LocalAnalysisWorker %s started", self.worker_id)

    async def stop(self) -> None:
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        
        # Wait for active jobs to finish or cancel them
        if self._active_jobs:
            logger.info("Waiting for %d active jobs to finish", len(self._active_jobs))
            await asyncio.gather(*self._active_jobs, return_exceptions=True)

    async def _poll_loop(self) -> None:
        while self._running:
            try:
                await self._try_claim_and_run()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in worker poll loop: %s", e)
            
            await asyncio.sleep(self.poll_interval)

    async def _try_claim_and_run(self) -> None:
        # 1. Recover stale jobs first
        async with self.session_factory() as session:
            async with session.begin():
                try:
                    recovered = await AnalysisJobRepo.recover_stale_jobs(session)
                    if recovered > 0:
                        logger.info("Recovered %d stale jobs", recovered)
                except Exception as e:
                    logger.error("Error recovering stale jobs: %s", e)

        # 2. Try to claim a job
        job = None
        async with self.session_factory() as session:
            async with session.begin():
                job = await AnalysisJobRepo.claim_job(session, self.worker_id)

        if not job:
            return

        logger.info("Worker %s claimed job %s (analysis %s, attempt %d)", 
                    self.worker_id, job.job_id, job.analysis_id, job.attempt_count)
        
        # Run in background
        task = asyncio.create_task(self._run_job(job.job_id, job.analysis_id))
        self._active_jobs.add(task)
        task.add_done_callback(self._active_jobs.discard)

    async def _run_job(self, job_id: str, analysis_id: str) -> None:
        main_task = asyncio.current_task()
        heartbeat_task = asyncio.create_task(self._heartbeat_loop(job_id, main_task))
        success = False
        error_msg = None
        
        try:
            # We must fetch the analysis row to get the repository identifier/provider/etc
            async with self.session_factory() as session:
                from sqlalchemy import select
                result = await session.execute(select(AnalysisRow).where(AnalysisRow.id == analysis_id))
                analysis = result.scalar_one_or_none()
                if not analysis:
                    raise ValueError(f"Analysis {analysis_id} not found")
                
                # We need the repository details
                # (assuming orchestrator uses the repository relation)
                await session.refresh(analysis, ["repository"])
                repo_id = analysis.repository_id
                provider_name = analysis.repository.provider_type
                identifier = analysis.repository.repository_identifier
                revision = analysis.commit_id
                workspace_id = analysis.repository.workspace_id

            orchestrator = AnalysisOrchestrator(session_factory=self.session_factory)
            await orchestrator.run(
                analysis_id=analysis_id,
                repository_id=repo_id,
                provider_name=provider_name,
                repository_identifier=identifier,
                revision=revision,
                workspace_id=workspace_id
            )
            success = True
        except asyncio.CancelledError:
            error_msg = "Job was cooperatively cancelled"
            success = False
        except Exception as e:
            logger.error("Job %s failed with error: %s", job_id, e)
            error_msg = traceback.format_exc()
            success = False
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
            
            # Complete the job (marks SUCCEEDED or FAILED)
            # A semantic VIOLATED or UNKNOWN is a job SUCCEEDED.
            async with self.session_factory() as session:
                async with session.begin():
                    try:
                        await AnalysisJobRepo.complete_job(
                            session, 
                            job_id, 
                            self.worker_id, 
                            success=success, 
                            error=error_msg
                        )
                    except JobOwnershipError:
                        logger.warning("Lost ownership of job %s before completion", job_id)
                    except JobStateError as e:
                        logger.warning("Job state error on completion for %s: %s", job_id, e)
                    except Exception as e:
                        logger.error("Failed to complete job %s: %s", job_id, e)

    async def _heartbeat_loop(self, job_id: str, main_task: asyncio.Task) -> None:
        """Periodically heartbeat. If we lose ownership or it's cancelled, cancel the main task."""
        while True:
            await asyncio.sleep(60)  # Heartbeat every 60s
            
            async with self.session_factory() as session:
                async with session.begin():
                    try:
                        await AnalysisJobRepo.heartbeat(session, job_id, self.worker_id)
                    except (JobOwnershipError, JobStateError) as e:
                        logger.warning("Heartbeat failed for job %s: %s. Cancelling job execution.", job_id, e)
                        main_task.cancel()
                        break
                    except Exception as e:
                        logger.error("Unexpected error in heartbeat for %s: %s", job_id, e)
