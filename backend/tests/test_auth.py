import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from app.api.main import app
from app.persistence.database import engine, Base
from app.core.config import settings

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.persistence.database import get_db

# Use an isolated in-memory database for auth tests
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

@pytest.fixture(autouse=True, scope="module")
async def setup_db_module():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as c:
        yield c
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_auth_signup(client: AsyncClient):
    response = await client.post("/auth/signup", json={
        "email": "test1@example.com",
        "password": "secure123",
        "display_name": "Test User",
        "workspace_name": "Test WS"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test1@example.com"
    assert "user_id" in data
    assert "workspace_ids" in data
    assert len(data["workspace_ids"]) == 1
    
    # Check cookies
    cookies = response.cookies
    assert "session" in cookies
    expected_csrf = "__Host-csrf" if settings.SECURE_COOKIES else "csrf_token"
    assert expected_csrf in cookies

@pytest.mark.asyncio
async def test_auth_signup_duplicate(client: AsyncClient):
    response = await client.post("/auth/signup", json={
        "email": "test1@example.com",
        "password": "secure123",
        "display_name": "Test User 2",
        "workspace_name": "Test WS 2"
    })
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_auth_signup_weak_password(client: AsyncClient):
    response = await client.post("/auth/signup", json={
        "email": "test2@example.com",
        "password": "weak",
        "display_name": "Test User",
        "workspace_name": "Test WS"
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_auth_login_success(client: AsyncClient):
    response = await client.post("/auth/login", json={
        "email": "test1@example.com",
        "password": "secure123"
    })
    assert response.status_code == 200
    assert "session" in response.cookies
    expected_csrf = "__Host-csrf" if settings.SECURE_COOKIES else "csrf_token"
    assert expected_csrf in response.cookies

@pytest.mark.asyncio
async def test_auth_login_wrong_password(client: AsyncClient):
    response = await client.post("/auth/login", json={
        "email": "test1@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_auth_login_unknown_email(client: AsyncClient):
    response = await client.post("/auth/login", json={
        "email": "unknown@example.com",
        "password": "secure123"
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_auth_me_valid_session(client: AsyncClient):
    # Login first
    login_resp = await client.post("/auth/login", json={
        "email": "test1@example.com",
        "password": "secure123"
    })
    
    # Use cookie
    me_resp = await client.get("/auth/me", cookies=login_resp.cookies)
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["email"] == "test1@example.com"
    assert len(data["workspaces"]) == 1

@pytest.mark.asyncio
async def test_auth_me_no_session(client: AsyncClient):
    me_resp = await client.get("/auth/me")
    assert me_resp.status_code == 401

@pytest.mark.asyncio
async def test_auth_logout(client: AsyncClient):
    login_resp = await client.post("/auth/login", json={
        "email": "test1@example.com",
        "password": "secure123"
    })
    
    # Need CSRF header for logout because we are using cookies
    expected_csrf = "__Host-csrf" if settings.SECURE_COOKIES else "csrf_token"
    csrf_token = login_resp.cookies.get(expected_csrf)
    
    # Ensure csrf_token is a string for httpx headers
    assert csrf_token is not None, f"Missing {expected_csrf} cookie"
    
    client.cookies = login_resp.cookies
    logout_resp = await client.post(
        "/auth/logout",
        headers={"X-CSRF-Token": csrf_token}
    )
    assert logout_resp.status_code == 204
    
    # Verify session is revoked
    me_resp = await client.get("/auth/me", cookies=login_resp.cookies)
    assert me_resp.status_code == 401
    
@pytest.mark.asyncio
async def test_workspaces_list(client: AsyncClient):
    login_resp = await client.post("/auth/login", json={
        "email": "test1@example.com",
        "password": "secure123"
    })
    
    ws_resp = await client.get("/workspaces/", cookies=login_resp.cookies)
    assert ws_resp.status_code == 200
    data = ws_resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test WS"
