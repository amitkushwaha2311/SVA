import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from app.api.main import app
from app.persistence.database import engine, Base
from app.auth.session import _hash_token

@pytest.fixture(autouse=True, scope="module")
async def setup_db_module():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://testserver") as c:
        yield c

@pytest.mark.asyncio
async def test_raw_token_never_in_db(client: AsyncClient):
    response = await client.post("/auth/signup", json={
        "email": "sec1@example.com",
        "password": "secure123",
        "display_name": "Sec User",
        "workspace_name": "Sec WS"
    })
    
    raw_token = response.cookies.get("session")
    token_hash = _hash_token(raw_token)
    
    async with engine.connect() as conn:
        # Raw token should not exist anywhere in the sessions table
        result_raw = await conn.execute(text("SELECT id FROM sessions WHERE token_hash = :raw"), {"raw": raw_token})
        assert result_raw.fetchone() is None
        
        # Hash should exist
        result_hash = await conn.execute(text("SELECT id FROM sessions WHERE token_hash = :hash"), {"hash": token_hash})
        assert result_hash.fetchone() is not None

@pytest.mark.asyncio
async def test_token_hash_cannot_authenticate(client: AsyncClient):
    login_resp = await client.post("/auth/login", json={
        "email": "sec1@example.com",
        "password": "secure123"
    })
    
    raw_token = login_resp.cookies.get("session")
    token_hash = _hash_token(raw_token)
    
    # Try to auth with token_hash as Bearer token
    me_resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token_hash}"})
    assert me_resp.status_code == 401

@pytest.mark.asyncio
async def test_deterministic_transport_precedence(client: AsyncClient):
    # Get token 1
    resp1 = await client.post("/auth/login", json={
        "email": "sec1@example.com",
        "password": "secure123"
    })
    token1 = resp1.cookies.get("session")
    
    # Get token 2 for another user
    await client.post("/auth/signup", json={
        "email": "sec2@example.com",
        "password": "secure123",
        "display_name": "Sec User 2",
        "workspace_name": "Sec WS 2"
    })
    resp2 = await client.post("/auth/login", json={
        "email": "sec2@example.com",
        "password": "secure123"
    })
    token2 = resp2.cookies.get("session")
    
    # Send request with both. Bearer (token1) should win over cookie (token2)
    me_resp = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token1}"},
        cookies={"session": token2}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "sec1@example.com"

@pytest.mark.asyncio
async def test_csrf_on_cookie_auth(client: AsyncClient):
    login_resp = await client.post("/auth/login", json={
        "email": "sec1@example.com",
        "password": "secure123"
    })
    
    # State changing POST with cookie but NO CSRF header
    ws_resp = await client.post(
        "/workspaces/",
        json={"name": "New WS"},
        cookies=login_resp.cookies
    )
    assert ws_resp.status_code == 403

@pytest.mark.asyncio
async def test_bearer_clients_skip_csrf(client: AsyncClient):
    login_resp = await client.post("/auth/login", json={
        "email": "sec1@example.com",
        "password": "secure123"
    })
    
    raw_token = login_resp.cookies.get("session")
    
    # State changing POST with Bearer token, NO CSRF header -> succeeds
    ws_resp = await client.post(
        "/workspaces/",
        json={"name": "New WS via API"},
        headers={"Authorization": f"Bearer {raw_token}"}
    )
    assert ws_resp.status_code == 200
