"""
Regression test: frontend registration route
============================================

The frontend signup page calls:
  POST /api/auth/signup          (Next.js)
  → proxied to →
  POST /auth/signup              (FastAPI backend, prefix="/auth" router)

This test calls the backend directly at /auth/signup and proves end-to-end
that registration → login → /auth/me → /api/v1/workspaces/ all work.

Preserves Phase 15 security architecture:
  - Argon2id passwords
  - opaque DB-backed sessions
  - hashed session tokens
  - CSRF protection
  - no JWT
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.api.main import app
from app.persistence.database import engine, Base
from app.core.config import settings


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


# -- 1. Registration endpoint discovery --------------------------------------

@pytest.mark.asyncio
async def test_registration_endpoint_is_auth_signup(client: AsyncClient):
    """
    POST /auth/signup must return 200 with a valid user + workspace + session cookie.
    This is the exact backend route reached when the frontend calls
    POST /api/auth/signup (via Next.js rewrite /api/auth/:path* -> /auth/:path*).
    """
    res = await client.post("/auth/signup", json={
        "email": "reg_test@example.com",
        "password": "secure_pass_1",
        "display_name": "Reg Tester",
        "workspace_name": "Reg WS",
    })
    assert res.status_code == 200, f"Expected 200 from /auth/signup, got {res.status_code}: {res.text}"

    body = res.json()
    assert body["email"] == "reg_test@example.com"
    assert "user_id" in body
    assert "workspace_ids" in body
    assert len(body["workspace_ids"]) == 1

    # Session cookie must be present (opaque DB-backed token)
    assert "session" in res.cookies, "Missing session cookie after registration"

    # CSRF cookie must be present (double-submit pattern)
    expected_csrf = "__Host-csrf" if settings.SECURE_COOKIES else "csrf_token"
    assert expected_csrf in res.cookies, f"Missing {expected_csrf} cookie after registration"


# -- 2. /auth/register does NOT exist (confirms the bug was real) -------------

@pytest.mark.asyncio
async def test_register_path_returns_404(client: AsyncClient):
    """
    /auth/register must NOT exist -- confirming the old frontend call was wrong.
    The correct endpoint is /auth/signup.
    """
    res = await client.post("/auth/register", json={
        "email": "ghost@example.com",
        "password": "secure_pass_1",
        "display_name": "Ghost",
        "workspace_name": "Ghost WS",
    })
    assert res.status_code == 404, (
        f"Expected 404 for non-existent /auth/register, got {res.status_code}"
    )


# -- 3. Full flow: signup -> login -> /auth/me -> /api/v1/workspaces/ ---------

@pytest.mark.asyncio
async def test_full_auth_flow_after_registration(client: AsyncClient):
    """
    Full browser flow regression:
      POST /auth/signup  -> 200
      POST /auth/login   -> 200 (JSON body, email + password)
      GET  /auth/me      -> 200
      GET  /api/v1/workspaces/ -> 200
    """
    # Step 1: Register
    signup_res = await client.post("/auth/signup", json={
        "email": "flow_test@example.com",
        "password": "secure_pass_2",
        "display_name": "Flow Tester",
        "workspace_name": "Flow WS",
    })
    assert signup_res.status_code == 200, f"Signup failed: {signup_res.text}"

    # Step 2: Login (JSON body matching LoginRequest schema)
    login_res = await client.post("/auth/login", json={
        "email": "flow_test@example.com",
        "password": "secure_pass_2",
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    assert "session" in login_res.cookies

    session_cookies = login_res.cookies

    # Step 3: GET /auth/me
    me_res = await client.get("/auth/me", cookies=session_cookies)
    assert me_res.status_code == 200, f"/auth/me failed: {me_res.text}"
    me_body = me_res.json()
    assert me_body["email"] == "flow_test@example.com"
    assert len(me_body["workspaces"]) == 1
    assert me_body["workspaces"][0]["name"] == "Flow WS"

    # Step 4: GET /api/v1/workspaces/
    ws_res = await client.get("/api/v1/workspaces/", cookies=session_cookies)
    assert ws_res.status_code == 200, f"/api/v1/workspaces/ failed: {ws_res.text}"
    ws_body = ws_res.json()
    assert "items" in ws_body
    assert len(ws_body["items"]) >= 1


# -- 4. Duplicate registration returns 409 ------------------------------------

@pytest.mark.asyncio
async def test_duplicate_registration_returns_409(client: AsyncClient):
    """Registering the same email twice returns 409 Conflict."""
    payload = {
        "email": "dup_reg@example.com",
        "password": "secure_pass_3",
        "display_name": "Dup User",
        "workspace_name": "Dup WS",
    }
    res1 = await client.post("/auth/signup", json=payload)
    assert res1.status_code == 200

    res2 = await client.post("/auth/signup", json=payload)
    assert res2.status_code == 409, f"Expected 409 for duplicate email, got {res2.status_code}"


# -- 5. Weak password rejected at registration --------------------------------

@pytest.mark.asyncio
async def test_registration_rejects_weak_password(client: AsyncClient):
    """SignupRequest schema enforces min_length=8 on password."""
    res = await client.post("/auth/signup", json={
        "email": "weak@example.com",
        "password": "short",
        "display_name": "Weak User",
        "workspace_name": "Weak WS",
    })
    assert res.status_code == 422, f"Expected 422 for weak password, got {res.status_code}"
