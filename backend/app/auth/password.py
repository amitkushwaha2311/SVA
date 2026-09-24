from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from app.core.config import settings

_ph = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM
)

def hash_password(plaintext: str) -> str:
    """Hash a password using Argon2id."""
    return _ph.hash(plaintext)

def verify_password(plaintext: str, hashed: str) -> bool:
    """Verify a password against its Argon2id hash."""
    try:
        return _ph.verify(hashed, plaintext)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
