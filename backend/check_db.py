import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.persistence.database import Base
from sqlalchemy import text

async def check():
    engine = create_async_engine("sqlite+aiosqlite:///./sva.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        tables = [row[0] for row in result.fetchall()]
        print("Tables:", tables)
    await engine.dispose()

asyncio.run(check())
