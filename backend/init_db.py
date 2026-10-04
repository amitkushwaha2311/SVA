import asyncio
from app.persistence.database import engine, Base
from sqlalchemy import text

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")
    
    # Verify
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        tables = [row[0] for row in result.fetchall()]
        print("Tables in DB:", tables)

asyncio.run(init_db())
