import secrets
from fastapi import Request, HTTPException

def generate_csrf_token() -> str:
    """Generate a random CSRF token for the double-submit cookie pattern."""
    return secrets.token_hex(16)

def _is_bearer_auth(request: Request) -> bool:
    """Check if the request uses Bearer token authentication."""
    auth_header = request.headers.get("Authorization")
    return bool(auth_header and auth_header.lower().startswith("bearer "))

def validate_csrf_token(request: Request) -> None:
    """
    Validate CSRF token for state-changing requests.
    Skips validation for Bearer-authenticated API clients.
    """
    if request.method not in ["POST", "PUT", "DELETE", "PATCH"]:
        return
        
    if _is_bearer_auth(request):
        return
        
    from app.core.config import settings
    cookie_name = "__Host-csrf" if settings.SECURE_COOKIES else "csrf_token"
    cookie_csrf = request.cookies.get(cookie_name)
    header_csrf = request.headers.get("X-CSRF-Token")
    
    if not cookie_csrf or not header_csrf:
        raise HTTPException(status_code=403, detail="CSRF validation failed: Missing token")
        
    if not secrets.compare_digest(cookie_csrf, header_csrf):
        raise HTTPException(status_code=403, detail="CSRF validation failed: Token mismatch")
