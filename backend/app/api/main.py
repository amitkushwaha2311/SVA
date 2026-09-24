from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.api.routers import auth, workspaces
from app.api.routers.v1 import repositories, analyses
from app.api.routers.v1.contracts import router as contracts_router
from app.api.routers.v1.evidence import router as evidence_router
from app.api.routers.v1.intent import router as intent_router
from app.api.routers.v1.domain import ambiguity_router, verification_router, drift_router
from app.api.routers.v1.workspaces import router as v1_workspaces_router
from app.api.routers.v1.orchestration import router as orchestration_router
from app.api.routers.v1.integrations import router as integrations_router
from app.api.routers.v1.webhooks import router as webhooks_router
from app.api.routers.v1.observability import router as observability_router
from app.api.routers.v1.search import router as search_router
from app.auth.errors import AuthError, SessionExpired, InvalidCredentials

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Start the embedded LocalAnalysisWorker when the server starts, and stop it
    gracefully when the server shuts down.

    This keeps the worker in-process with the API server for development and
    single-process deployments. In production, the worker can be extracted into
    a separate process (worker_main.py) and this lifespan can be a no-op.
    """
    from app.orchestration.worker import LocalAnalysisWorker
    from app.persistence.database import async_session_maker, engine, Base

    # Ensure all tables exist. This is a safe no-op if tables already exist,
    # and protects against the database being wiped (e.g., by the test suite
    # calling Base.metadata.drop_all on a shared engine).
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema verified/created.")

    worker = LocalAnalysisWorker(session_factory=async_session_maker, poll_interval_seconds=2.0)
    await worker.start()
    logger.info("Embedded analysis worker started.")
    try:
        yield
    finally:
        logger.info("Stopping embedded analysis worker...")
        await worker.stop()
        logger.info("Embedded analysis worker stopped.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(repositories.router, prefix="/api")
app.include_router(analyses.router, prefix="/api")
app.include_router(contracts_router, prefix="/api")
app.include_router(evidence_router, prefix="/api")
app.include_router(intent_router, prefix="/api")
app.include_router(ambiguity_router, prefix="/api")
app.include_router(verification_router, prefix="/api")
app.include_router(drift_router, prefix="/api")
app.include_router(v1_workspaces_router, prefix="/api")
app.include_router(orchestration_router, prefix="/api")
app.include_router(integrations_router)
app.include_router(webhooks_router)
app.include_router(observability_router)
app.include_router(search_router, prefix="/api")

@app.exception_handler(AuthError)
async def auth_exception_handler(request: Request, exc: AuthError):
    if isinstance(exc, SessionExpired):
        return JSONResponse(status_code=401, content={"detail": str(exc)})
    if isinstance(exc, InvalidCredentials):
        return JSONResponse(status_code=401, content={"detail": str(exc)})
    return JSONResponse(status_code=401, content={"detail": str(exc)})

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
