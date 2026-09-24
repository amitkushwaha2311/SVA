"""
SVA Test Configuration
======================

Shared pytest fixtures for all SVA tests.

FIXTURE DESIGN PRINCIPLES:
- All file access uses real temporary directories (not mocks)
- Security tests create actual adversarial filesystem layouts
- No test executes repository code
- Tests verify BEHAVIOR, not just function execution
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.repository.scanner.path_guard import PathGuard


# ---------------------------------------------------------------------------
# Path to fixture repositories
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "repos"


@pytest.fixture
def simple_python_repo() -> Path:
    """Path to the simple Python test repository fixture."""
    p = FIXTURES_DIR / "simple_python"
    assert p.exists(), f"Fixture missing: {p}"
    return p


@pytest.fixture
def injection_repo() -> Path:
    """Path to the fixture repository containing prompt injection text."""
    p = FIXTURES_DIR / "with_injection"
    assert p.exists(), f"Fixture missing: {p}"
    return p


@pytest.fixture
def simple_guard(simple_python_repo: Path) -> PathGuard:
    """PathGuard locked to the simple Python fixture repository."""
    return PathGuard(root=simple_python_repo)


# ---------------------------------------------------------------------------
# Temporary directory helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """
    An empty temporary directory that acts as a repository root.

    Unlike simple_python_repo, tests can write arbitrary content here.
    Uses pytest's built-in tmp_path fixture for automatic cleanup.
    """
    return tmp_path


@pytest.fixture
def tmp_guard(tmp_path: Path) -> PathGuard:
    """PathGuard locked to an empty temporary directory."""
    return PathGuard(root=tmp_path)


# ---------------------------------------------------------------------------
# Symlink capability detection
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------
import uuid as _uuid
import tempfile as _tempfile
import os as _os
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.persistence.database import Base


@pytest_asyncio.fixture
async def engine(tmp_path):
    # Use a real file-based SQLite DB so background worker tasks (in thread-pool)
    # can open the same database file. Named in-memory DBs are not reliably
    # shared across aiosqlite's thread-worker boundaries.
    db_file = tmp_path / f"sva_test_{_uuid.uuid4().hex}.db"
    url = f"sqlite+aiosqlite:///{db_file}"
    eng = create_async_engine(url, echo=False, connect_args={"check_same_thread": False})
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()
    # db_file cleaned up by tmp_path fixture automatically


@pytest_asyncio.fixture
async def db(engine):
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session


def _can_create_symlinks() -> bool:
    """
    Check whether the current environment supports symlink creation.

    On Windows, creating symlinks requires either:
    - Administrator privileges, or
    - Developer Mode enabled (Windows 10+)
    """
    import tempfile

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            link = Path(tmpdir) / "test_link"
            target = Path(tmpdir) / "target.txt"
            target.write_text("test")
            link.symlink_to(target)
            return True
    except (OSError, NotImplementedError):
        return False


requires_symlinks = pytest.mark.skipif(
    not _can_create_symlinks(),
    reason="Symlink creation requires admin or Developer Mode on Windows",
)
