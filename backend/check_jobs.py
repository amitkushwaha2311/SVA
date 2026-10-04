import asyncio
from sqlalchemy import select
from app.persistence.database import AsyncSessionLocal
from app.persistence.models.job import AnalysisJobRow
import sys

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(AnalysisJobRow).order_by(AnalysisJobRow.created_at.desc()).limit(10))
        jobs = result.scalars().all()
        for j in jobs:
            print(f"Job: {j.job_id}, Status: {j.status}, Analysis: {j.analysis_id}, Att: {j.attempt_count}")

if __name__ == "__main__":
    asyncio.run(main())
