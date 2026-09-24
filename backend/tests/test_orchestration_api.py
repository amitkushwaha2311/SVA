import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException

from app.api.main import app
from app.persistence.models.user import UserRow
from app.persistence.models.repository import RepositoryRow
from app.persistence.models.analysis import AnalysisRow


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def authorized_user():
    return UserRow(id="user-1", email="test@example.com")


@pytest.fixture(autouse=True)
def override_dependencies(authorized_user):
    """Override auth + DB dependencies to avoid real I/O in API tests."""
    from app.api.dependencies import get_current_user
    from app.persistence.database import get_db

    async def mock_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_current_user] = lambda: authorized_user
    app.dependency_overrides[get_db] = mock_get_db
    yield
    app.dependency_overrides.clear()


def make_repo(**kwargs) -> RepositoryRow:
    defaults = dict(
        id="repo-1",
        workspace_id="ws-1",
        name="test-repo",
        source_type="git",
        provider_type="git",
        repository_identifier="https://github.com/a/b",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return RepositoryRow(**defaults)


def make_analysis(**kwargs) -> AnalysisRow:
    defaults = dict(
        id="sva-123",
        repository_id="repo-1",
        status="CREATED",
        commit_id="main",
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return AnalysisRow(**defaults)


# ─── Tests ────────────────────────────────────────────────────────────────────

async def test_register_repository_success():
    """POST /repositories returns 201 for valid workspace member."""
    with patch("app.api.routers.v1.orchestration.require_workspace_member", return_value=None), \
         patch("app.api.routers.v1.orchestration.RepositoryRepo") as MockRepo:

        instance = MockRepo.return_value
        instance.create = AsyncMock(return_value=make_repo())

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/v1/orchestration/repositories", json={
                "workspace_id": "ws-1",
                "name": "test-repo",
                "provider": "git",
                "identifier": "https://github.com/a/b"
            })

        assert response.status_code == 201
        assert response.json()["id"] == "repo-1"


async def test_trigger_analysis_accepted():
    """POST /repositories/{id}/analyses returns 202 Accepted immediately."""
    with patch("app.api.routers.v1.orchestration.require_workspace_member", return_value=None), \
         patch("app.api.routers.v1.orchestration.RepositoryRepo") as MockRepo, \
         patch("app.api.routers.v1.orchestration.AnalysisRepo") as MockAnalysisRepo, \
         patch("app.api.routers.v1.orchestration.AnalysisJobRepo") as MockJobRepo, \
         patch("app.api.routers.v1.orchestration.AnalysisOrchestrator"):

        MockRepo.return_value.get_by_id = AsyncMock(return_value=make_repo())
        MockAnalysisRepo.return_value.create = AsyncMock(return_value=make_analysis())
        MockJobRepo.create_job = AsyncMock(return_value="job-1")

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/v1/orchestration/repositories/repo-1/analyses", json={
                "revision": "main"
            })

        # Must be 202 Accepted — not 200, not 201
        assert response.status_code == 202
        body = response.json()
        assert body["id"] == "sva-123"
        assert body["status"] == "CREATED"


async def test_register_repository_unauthorized():
    """POST /repositories returns 403 when user is not in workspace."""
    async def mock_reject(*args, **kwargs):
        raise HTTPException(status_code=403, detail="Not authorized")

    with patch("app.api.routers.v1.orchestration.require_workspace_member", side_effect=mock_reject):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/v1/orchestration/repositories", json={
                "workspace_id": "ws-other",
                "name": "test",
                "provider": "git",
                "identifier": "https://github.com/a/b"
            })

        assert response.status_code == 403


async def test_trigger_analysis_unauthorized():
    """POST /repositories/{id}/analyses returns 403 when user is not in owning workspace."""
    async def mock_reject(*args, **kwargs):
        raise HTTPException(status_code=403, detail="Not authorized")

    with patch("app.api.routers.v1.orchestration.RepositoryRepo") as MockRepo, \
         patch("app.api.routers.v1.orchestration.require_workspace_member", side_effect=mock_reject):

        MockRepo.return_value.get_by_id = AsyncMock(return_value=make_repo(workspace_id="ws-other"))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/v1/orchestration/repositories/repo-1/analyses", json={
                "revision": "main"
            })

        assert response.status_code == 403


async def test_get_analysis_status_unauthorized():
    """GET /analyses/{id}/status returns 403 when user is not in owning workspace."""
    async def mock_reject(*args, **kwargs):
        raise HTTPException(status_code=403, detail="Not authorized")

    with patch("app.api.routers.v1.orchestration.AnalysisRepo") as MockAnalysisRepo, \
         patch("app.api.routers.v1.orchestration.RepositoryRepo") as MockRepo, \
         patch("app.api.routers.v1.orchestration.require_workspace_member", side_effect=mock_reject):

        MockAnalysisRepo.return_value.get_by_id = AsyncMock(return_value=make_analysis())
        MockRepo.return_value.get_by_id = AsyncMock(return_value=make_repo(workspace_id="ws-other"))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v1/orchestration/analyses/sva-123/status")

        assert response.status_code == 403


async def test_register_repository_invalid_provider():
    """POST /repositories returns 422 for disallowed provider types."""
    with patch("app.api.routers.v1.orchestration.require_workspace_member", return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/v1/orchestration/repositories", json={
                "workspace_id": "ws-1",
                "name": "test",
                "provider": "ssh",  # Not allowed — only 'git' or 'local'
                "identifier": "ssh://git@github.com/org/repo"
            })

        assert response.status_code == 422


async def test_register_repository_empty_identifier():
    """POST /repositories returns 422 for blank identifier."""
    with patch("app.api.routers.v1.orchestration.require_workspace_member", return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/v1/orchestration/repositories", json={
                "workspace_id": "ws-1",
                "name": "test",
                "provider": "git",
                "identifier": "   "  # Whitespace-only — rejected by field_validator
            })

        assert response.status_code == 422


async def test_unauthenticated_requests_rejected():
    """All endpoints must return 401 when there is no authenticated session."""
    app.dependency_overrides.clear()  # Remove the autouse fixture overrides
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r1 = await ac.post("/api/v1/orchestration/repositories", json={
                "workspace_id": "ws-1", "name": "x", "provider": "git", "identifier": "https://a.b/c"
            })
            r2 = await ac.post("/api/v1/orchestration/repositories/x/analyses", json={"revision": "main"})
            r3 = await ac.get("/api/v1/orchestration/analyses/x/status")

        assert r1.status_code == 401, f"Expected 401, got {r1.status_code}"
        assert r2.status_code == 401, f"Expected 401, got {r2.status_code}"
        assert r3.status_code == 401, f"Expected 401, got {r3.status_code}"
    finally:
        # Re-apply overrides for subsequent tests (autouse fixture resets after each test)
        from app.api.dependencies import get_current_user
        from app.persistence.database import get_db
        from tests.test_orchestration_api import authorized_user  # re-use fixture value
