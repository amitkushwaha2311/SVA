import asyncio
from sqlalchemy import select, desc
import sys
sys.path.append('c:\\Users\\AMIT KUSHWAHA\\OneDrive\\Desktop\\SVA\\backend')

from app.persistence.database import AsyncSessionLocal
from app.persistence.models.analysis import AnalysisRow

async def main():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AnalysisRow).order_by(desc(AnalysisRow.created_at)).limit(5)
        )
        analyses = result.scalars().all()
        for a in analyses:
            print(f"Analysis ID: {a.id}, Status: {a.status}, Created: {a.created_at}")
            print(f"Error: {a.error_message}")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
