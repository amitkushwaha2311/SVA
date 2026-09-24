"""
Secure Cryptographic Utilities for Provider Credentials.
"""

from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet() -> Fernet:
    """
    Returns a configured Fernet instance using the application's master encryption key.
    The key MUST be exactly 32 URL-safe base64-encoded bytes.
    """
    # Fernet requires a 32-byte url-safe base64-encoded key.
    # Our settings.ENCRYPTION_KEY_SECRET acts as this key.
    # We strip any whitespace that might have crept into env vars.
    key = settings.ENCRYPTION_KEY_SECRET.strip().encode("utf-8")
    
    # Fernet constructor will raise ValueError if key is invalid length/format
    return Fernet(key)


def encrypt_credential(plaintext: str) -> str:
    """
    Encrypts a plaintext credential using authenticated encryption (AES-128-CBC with HMAC-SHA256).
    """
    if not plaintext:
        return ""
    fernet = _get_fernet()
    # Fernet returns bytes, we decode to string for storage
    return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_credential(ciphertext: str) -> str:
    """
    Decrypts a credential ciphertext.
    Raises cryptography.fernet.InvalidToken if decryption or authentication fails.
    """
    if not ciphertext:
        return ""
    fernet = _get_fernet()
    return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
