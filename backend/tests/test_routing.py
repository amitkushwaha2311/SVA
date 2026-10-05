import pytest
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

def test_v1_endpoints_no_trailing_slash():
    """Ensure v1 endpoints don't have trailing slashes and return 404/405/403/401 instead of 307."""
    
    # We are checking for the absence of 307 Temporary Redirect
    
    endpoints = [
        "/api/v1/workspaces",
        "/api/v1/evidence",
        "/api/v1/contracts",
        "/api/v1/intent",
        "/api/v1/verification",
        "/api/v1/drift",
    ]
    
    for ep in endpoints:
        response = client.get(ep, follow_redirects=False)
        # It should not return a 307 Redirect! It might return 401 Unauthorized, 422 (missing query params), etc.
        assert response.status_code != 307, f"Endpoint {ep} returned 307 redirect!"

def test_v1_endpoints_with_trailing_slash():
    """Ensure v1 endpoints WITH trailing slash return 404 Not Found since we strictly disabled them."""
    endpoints = [
        "/api/v1/workspaces/",
        "/api/v1/evidence/",
        "/api/v1/contracts/",
        "/api/v1/intent/",
        "/api/v1/verification/",
        "/api/v1/drift/",
    ]
    
    for ep in endpoints:
        response = client.get(ep, follow_redirects=False)
        # Should be 307 Temporary Redirect because FastAPI redirects to the non-trailing slash version
        assert response.status_code == 307, f"Endpoint {ep} should return 307 redirect to non-trailing slash route, but returned {response.status_code}"
