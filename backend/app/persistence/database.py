import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# Use environment variable or default to local sqlite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sva.db")

# Create engine
# Note: pool_pre_ping helps with connection drops, particularly in postgres.
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True if "postgresql" in DATABASE_URL else False,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Alias for orchestrator use (background tasks need their own session scope)
async_session_maker = AsyncSessionLocal

# Declarative Base for models
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session.
    """
    async with AsyncSessionLocal() as session:
        yield session
