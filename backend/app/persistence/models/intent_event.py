"""
SVA Intent Confirmation Event Model
====================================

Auditable record of a human explicitly confirming or rejecting an
IntentCandidate.  One row is created per unique confirmation action.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String

from app.persistence.database import Base


def _generate_uuid() -> str:
    return str(uuid.uuid4())


class IntentConfirmationEventRow(Base):
    """
    Records each human confirmation action against an IntentCandidate.

    Invariants:
    - event_id is a UUID, generated at insert time.
    - confirmed_by_user_id references users.id.
    - At most one CONFIRMED event is created per candidate (enforced in the
      repository layer via idempotency check).
    - action is always 'CONFIRMED' in Phase 1 of this implementation.
    """

    __tablename__ = "intent_confirmation_events"

    event_id = Column(String(36), primary_key=True, default=_generate_uuid)
    candidate_id = Column(
        String(255),
        ForeignKey("intent_candidates.candidate_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_id = Column(String(255), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=False, index=True)
    confirmed_by_user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    confirmed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    action = Column(String(20), nullable=False, default="CONFIRMED")
