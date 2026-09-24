import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.persistence.database import Base
from app.persistence.repositories.verification_repo import VerificationRepository
from app.verification.models import VerificationReport

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_verification_report_save(db_session: AsyncSession):
    repo = VerificationRepository(db_session)
    report = VerificationReport(
        verification_id="v-1",
        repository_id="repo-1",
        commit_id="commit-1",
        generated_at=datetime.now(timezone.utc).isoformat(),
        engine_version="1.0",
        requirement_results=[]
    )
    
    await repo.save_report(report)
    fetched = await repo.get_report("v-1")
    assert fetched is not None
    assert fetched.verification_id == "v-1"
