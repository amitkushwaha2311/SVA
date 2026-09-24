"""Make scenario_id and normalized_statement nullable

Revision ID: 468fbcced3d7
Revises: c3e8837a4e67
Create Date: 2026-09-24 02:51:25.965845

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '468fbcced3d7'
down_revision: Union[str, Sequence[str], None] = 'c3e8837a4e67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('intent_candidates', schema=None) as batch_op:
        batch_op.alter_column('normalized_statement',
               existing_type=sa.VARCHAR(),
               nullable=True)

    with op.batch_alter_table('counterexamples', schema=None) as batch_op:
        batch_op.alter_column('scenario_id',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)

def downgrade() -> None:
    with op.batch_alter_table('counterexamples', schema=None) as batch_op:
        batch_op.alter_column('scenario_id',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)

    with op.batch_alter_table('intent_candidates', schema=None) as batch_op:
        batch_op.alter_column('normalized_statement',
               existing_type=sa.VARCHAR(),
               nullable=False)
