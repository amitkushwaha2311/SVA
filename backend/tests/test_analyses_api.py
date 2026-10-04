import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

from app.api.main import app
from app.persistence.models.user import UserRow
from app.persistence.models.repository import RepositoryRow
from app.persistence.models.analysis import AnalysisRow

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


def make_analysis(**kwargs) -> AnalysisRow:
    defaults = dict(
        id="sva-123",
        repository_id="repo-1",
        status="COMPLETED",
        commit_id="main",
        created_at=datetime.now(timezone.utc),
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return AnalysisRow(**defaults)


async def test_list_analyses_success():
    """POST /analyses returns analyses for a repository."""
    with patch("app.api.routers.v1.analyses.require_workspace_member", return_value=None):
        async def mock_execute(stmt):
            class MockResult:
                def scalars(self):
                    class MockScalars:
                        def all(self):
                            # Ensure the where clause uses repository_id
                            # But we just return a mocked list for testing the endpoint serialization
                            return [make_analysis(id="sva-completed")]
                    return MockScalars()
            return MockResult()

        from app.api.dependencies import get_db
        async def mock_get_db():
            db_mock = AsyncMock()
            db_mock.execute = mock_execute
            yield db_mock

        app.dependency_overrides[get_db] = mock_get_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v1/analyses/?workspace_id=ws-1&repository_id=repo-1")

        assert response.status_code == 200
        data = response.json()
        assert "analyses" in data
        assert len(data["analyses"]) == 1
        assert data["analyses"][0]["id"] == "sva-completed"
        assert data["analyses"][0]["status"] == "COMPLETED"


async def test_list_analyses_empty():
    """POST /analyses returns empty list when no analyses exist."""
    with patch("app.api.routers.v1.analyses.require_workspace_member", return_value=None):
        async def mock_execute(stmt):
            class MockResult:
                def scalars(self):
                    class MockScalars:
                        def all(self):
                            return []
                    return MockScalars()
            return MockResult()

        from app.api.dependencies import get_db
        async def mock_get_db():
            db_mock = AsyncMock()
            db_mock.execute = mock_execute
            yield db_mock

        app.dependency_overrides[get_db] = mock_get_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v1/analyses/?workspace_id=ws-1&repository_id=repo-empty")

        assert response.status_code == 200
        data = response.json()
        assert "analyses" in data
        assert len(data["analyses"]) == 0

