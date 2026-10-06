import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from app.api.main import app
from app.persistence.models.user import UserRow
from app.persistence.models.intent import IntentCandidateRow

@pytest.fixture
def authorized_user():
    return UserRow(id="user-1", email="test@example.com")

@pytest.fixture(autouse=True)
def override_dependencies(authorized_user):
    from app.api.dependencies import get_current_user
    from app.persistence.database import get_db

    async def mock_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: authorized_user
    app.dependency_overrides[get_db] = mock_get_db
    yield
    app.dependency_overrides.clear()


def make_candidate(**kwargs):
    defaults = dict(
        candidate_id="cand-123",
        analysis_id="sva-123",
        original_statement="Only project owners can delete projects.",
        normalized_statement=None,
        status="CANDIDATE",
        extraction_method="DOCUMENT",
        provenance={"type": "DOCUMENT"},
        human_confirmed=False,
        sources=[]
    )
    defaults.update(kwargs)
    return IntentCandidateRow(**defaults)


@pytest.mark.asyncio
async def test_list_intent_returns_human_confirmed():
    with patch("app.api.routers.v1.intent.require_workspace_member", return_value=None):
        async def mock_execute(stmt):
            class MockResult:
                def scalar_one_or_none(self):
                    return True # Fake analysis exists
                def scalars(self):
                    class MockScalars:
                        def all(self):
                            return [make_candidate()]
                    return MockScalars()
            return MockResult()

        from app.api.dependencies import get_db
        async def mock_get_db():
            db_mock = AsyncMock()
            db_mock.execute = mock_execute
            yield db_mock

        app.dependency_overrides[get_db] = mock_get_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/api/v1/intent/?workspace_id=ws-1&analysis_id=sva-123")

        assert resp.status_code == 200
        data = resp.json()["items"]
        assert len(data) == 1
        item = data[0]
        
        assert item["human_confirmed"] is False
        assert item["actor"] == "project owner"
        assert item["action"] == "delete"
        assert item["resource"] == "project"
        assert len(item["assumptions"]) == 1
        assert "owner = resource.owner_id" in item["assumptions"][0]


@pytest.mark.asyncio
async def test_confirm_intent_success_and_idempotency():
    with patch("app.api.routers.v1.intent.require_workspace_member", return_value=None):
        async def mock_execute(stmt):
            class MockResult:
                def scalar_one_or_none(self):
                    return True # Fake analysis exists
            return MockResult()
            
        with patch("app.persistence.repositories.intent_repo.IntentRepository.confirm_candidate") as mock_confirm:
            mock_confirm.return_value = make_candidate(human_confirmed=True)
            
            from app.api.dependencies import get_db
            async def mock_get_db():
                db_mock = AsyncMock()
                db_mock.execute = mock_execute
                yield db_mock

            app.dependency_overrides[get_db] = mock_get_db

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post("/api/v1/intent/cand-123/confirm?workspace_id=ws-1&analysis_id=sva-123")

            assert resp.status_code == 200
            data = resp.json()
            assert data["human_confirmed"] is True
            assert data["actor"] == "project owner"
            mock_confirm.assert_called_once_with(
                candidate_id="cand-123",
                analysis_id="sva-123",
                workspace_id="ws-1",
                user_id="user-1"
            )


@pytest.mark.asyncio
async def test_confirm_intent_wrong_analysis_rejected():
    with patch("app.api.routers.v1.intent.require_workspace_member", return_value=None):
        async def mock_execute(stmt):
            class MockResult:
                def scalar_one_or_none(self):
                    return None # Analysis NOT found
            return MockResult()

        from app.api.dependencies import get_db
        async def mock_get_db():
            db_mock = AsyncMock()
            db_mock.execute = mock_execute
            yield db_mock

        app.dependency_overrides[get_db] = mock_get_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/api/v1/intent/cand-123/confirm?workspace_id=ws-1&analysis_id=fake-analysis")

        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_confirm_intent_not_found():
    with patch("app.api.routers.v1.intent.require_workspace_member", return_value=None):
        async def mock_execute(stmt):
            class MockResult:
                def scalar_one_or_none(self):
                    return True # Fake analysis exists
            return MockResult()
            
        with patch("app.persistence.repositories.intent_repo.IntentRepository.confirm_candidate") as mock_confirm:
            mock_confirm.side_effect = ValueError("Candidate not found")
            
            from app.api.dependencies import get_db
            async def mock_get_db():
                db_mock = AsyncMock()
                db_mock.execute = mock_execute
                yield db_mock

            app.dependency_overrides[get_db] = mock_get_db

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post("/api/v1/intent/fake-cand/confirm?workspace_id=ws-1&analysis_id=sva-123")

            assert resp.status_code == 404
