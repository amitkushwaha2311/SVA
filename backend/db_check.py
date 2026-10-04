import asyncio
from sqlalchemy import select
from pathlib import Path
import sys
sys.path.append('c:\\Users\\AMIT KUSHWAHA\\OneDrive\\Desktop\\SVA\\backend')

from app.persistence.database import AsyncSessionLocal
from app.persistence.models.repository import RepositoryRow
from app.persistence.models.analysis import AnalysisRow

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(RepositoryRow))
        repos = result.scalars().all()
        for r in repos:
            print(f"Repo ID: {r.id}, Identifier: {r.repository_identifier}, Type: {r.provider_type}")
        
        result = await session.execute(select(AnalysisRow))
        analyses = result.scalars().all()
        for a in analyses:
            print(f"Analysis ID: {a.id}, Repo ID: {a.repository_id}, Status: {a.status}, Error: {a.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
