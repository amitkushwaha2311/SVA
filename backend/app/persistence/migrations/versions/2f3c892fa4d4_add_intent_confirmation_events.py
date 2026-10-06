"""add_intent_confirmation_events

Revision ID: 2f3c892fa4d4
Revises: c3e8837a4e67
Create Date: 2026-10-05 20:46:40.220137

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f3c892fa4d4'
down_revision: Union[str, Sequence[str], None] = '468fbcced3d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'intent_confirmation_events',
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('candidate_id', sa.String(length=255), nullable=False),
        sa.Column('analysis_id', sa.String(length=255), nullable=False),
        sa.Column('workspace_id', sa.String(length=36), nullable=False),
        sa.Column('confirmed_by_user_id', sa.String(length=36), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['intent_candidates.candidate_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['confirmed_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('event_id')
    )
    with op.batch_alter_table('intent_confirmation_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_intent_confirmation_events_analysis_id'), ['analysis_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_intent_confirmation_events_candidate_id'), ['candidate_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_intent_confirmation_events_confirmed_by_user_id'), ['confirmed_by_user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_intent_confirmation_events_workspace_id'), ['workspace_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('intent_confirmation_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_intent_confirmation_events_workspace_id'))
        batch_op.drop_index(batch_op.f('ix_intent_confirmation_events_confirmed_by_user_id'))
        batch_op.drop_index(batch_op.f('ix_intent_confirmation_events_candidate_id'))
        batch_op.drop_index(batch_op.f('ix_intent_confirmation_events_analysis_id'))
    op.drop_table('intent_confirmation_events')
