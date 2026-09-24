"""SVA core configuration — settings loaded from environment."""

from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    SVA application settings.

    Values are read from environment variables (case-insensitive).
    For local development, place overrides in backend/.env (never committed).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------------------------------------------------------------------------
    # Application
    # ---------------------------------------------------------------------------
    APP_NAME: str = "SVA — Semantic Verification & Assurance"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ---------------------------------------------------------------------------
    # Database
    # ---------------------------------------------------------------------------
    # Default: SQLite for local dev. Override with a PostgreSQL URL for production.
    # Example: postgresql+asyncpg://user:password@localhost/sva
    DATABASE_URL: str = "sqlite+aiosqlite:///./sva_dev.db"

    # ---------------------------------------------------------------------------
    # Repository scanner security limits
    # ---------------------------------------------------------------------------
    # Maximum size of any single file that SVA will read (bytes)
    SCANNER_MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB

    # Maximum directory depth traversal
    SCANNER_MAX_DEPTH: int = 50

    # Maximum total files per analysis run
    SCANNER_MAX_FILES: int = 100_000

    @field_validator("SCANNER_MAX_FILE_SIZE_BYTES")
    @classmethod
    def validate_max_file_size(cls, v: int) -> int:
        if v < 1:
            raise ValueError("SCANNER_MAX_FILE_SIZE_BYTES must be positive")
        if v > 500 * 1024 * 1024:  # 500 MB hard ceiling
            raise ValueError("SCANNER_MAX_FILE_SIZE_BYTES cannot exceed 500 MB")
        return v

    @field_validator("SCANNER_MAX_DEPTH")
    @classmethod
    def validate_max_depth(cls, v: int) -> int:
        if v < 1 or v > 200:
            raise ValueError("SCANNER_MAX_DEPTH must be between 1 and 200")
        return v

    # ---------------------------------------------------------------------------
    # Authentication & Authorization
    # ---------------------------------------------------------------------------
    SESSION_TTL_SECONDS: int = 604800   # 7 days
    ARGON2_TIME_COST: int = 2
    ARGON2_MEMORY_COST: int = 65536     # 64 MB
    ARGON2_PARALLELISM: int = 2
    CORS_ORIGINS: list[str] = []
    SECURE_COOKIES: bool = True         # Set False for local HTTP dev

    # ---------------------------------------------------------------------------
    # Integrations & Encryption
    # ---------------------------------------------------------------------------
    # Master key for encrypting provider credentials (must be 32 URL-safe base64-encoded bytes for Fernet)
    # Default is a dummy key for dev. Override in production.
    ENCRYPTION_KEY_SECRET: str = "da9jErI3N9ZXj4KGrzfmgF_X3gSDEqlP2oVz-LpHqYQ="  # Dev dummy key — override in production
    ENCRYPTION_KEY_VERSION: int = 1


# Module-level singleton — import this everywhere
settings = Settings()
