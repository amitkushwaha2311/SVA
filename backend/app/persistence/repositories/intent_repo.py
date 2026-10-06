"""
Intent Repository
"""
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.persistence.models.intent import IntentCandidateRow
from app.persistence.models.intent_event import IntentConfirmationEventRow


class IntentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_candidate(self, candidate_id: str, analysis_id: str) -> Optional[IntentCandidateRow]:
        """Fetch a candidate scoped to a specific analysis."""
        stmt = select(IntentCandidateRow).where(
            IntentCandidateRow.candidate_id == candidate_id,
            IntentCandidateRow.analysis_id == analysis_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def confirm_candidate(
        self,
        candidate_id: str,
        analysis_id: str,
        workspace_id: str,
        user_id: str
    ) -> IntentCandidateRow:
        """
        Marks an intent candidate as HUMAN_CONFIRMED and records an audit event.
        Idempotent: if already confirmed, returns the candidate without creating duplicates.
        Raises ValueError if candidate is not found.
        """
        candidate = await self.get_candidate(candidate_id, analysis_id)
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found in analysis {analysis_id}")

        if candidate.human_confirmed:
            return candidate

        candidate.human_confirmed = True
        self.db.add(candidate)

        event = IntentConfirmationEventRow(
            candidate_id=candidate.candidate_id,
            analysis_id=analysis_id,
            workspace_id=workspace_id,
            confirmed_by_user_id=user_id,
            confirmed_at=datetime.now(timezone.utc),
            action="CONFIRMED"
        )
        self.db.add(event)
        
        await self.db.commit()
        await self.db.refresh(candidate)
        return candidate
