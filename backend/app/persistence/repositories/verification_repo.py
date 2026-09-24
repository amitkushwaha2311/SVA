from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.verification.models import VerificationReport
from app.persistence.models.verification import VerificationReportRow
from app.persistence.mappers.verification_mapper import VerificationMapper


class VerificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_report(self, report: VerificationReport) -> None:
        row = VerificationMapper.report_to_row(report)
        self.session.add(row)
        await self.session.flush()

    async def get_report(self, verification_id: str) -> Optional[VerificationReportRow]:
        stmt = select(VerificationReportRow).where(VerificationReportRow.verification_id == verification_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
