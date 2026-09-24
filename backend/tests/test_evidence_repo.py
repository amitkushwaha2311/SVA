import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.persistence.database import Base
from app.persistence.repositories.evidence_repo import EvidenceRepository, ImmutableEvidenceError
from app.evidence.models import Evidence, EvidenceType, VerificationMethod, EvidenceResult, EvidenceStatus

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
async def test_evidence_immutability(db_session: AsyncSession):
    repo = EvidenceRepository(db_session)
    ev = Evidence(
        evidence_id="ev-123", contract_id="c-1", requirement_id="r-1", repository_id="repo-1", commit_id="commit-1",
        evidence_type=EvidenceType.DETERMINISTIC_TEST, verification_method=VerificationMethod.UNIT_TEST,
        result=EvidenceResult.PASS, status=EvidenceStatus.OBSERVED,
        description="Test pass", observation="None", collected_at=datetime.now(timezone.utc).isoformat()
    )
    
    await repo.save(ev)
    
    with pytest.raises(ImmutableEvidenceError):
        await repo.save(ev)

@pytest.mark.asyncio
async def test_evidence_get(db_session: AsyncSession):
    repo = EvidenceRepository(db_session)
    ev = Evidence(
        evidence_id="ev-123", contract_id="c-1", requirement_id="r-1", repository_id="repo-1", commit_id="commit-1",
        evidence_type=EvidenceType.DETERMINISTIC_TEST, verification_method=VerificationMethod.UNIT_TEST,
        result=EvidenceResult.PASS, status=EvidenceStatus.OBSERVED,
        description="Test pass", observation="None", collected_at=datetime.now(timezone.utc).isoformat()
    )
    await repo.save(ev)
    
    fetched = await repo.get_by_id("ev-123")
    assert fetched is not None
    assert fetched.evidence_id == "ev-123"
    assert fetched.evidence_type == EvidenceType.DETERMINISTIC_TEST
