class AuthError(Exception):
    """Base authentication error."""
    pass

class InvalidCredentials(AuthError):
    """Raised when email or password is incorrect."""
    pass

class SessionExpired(AuthError):
    """Raised when the session is expired, revoked, or not found."""
    pass
