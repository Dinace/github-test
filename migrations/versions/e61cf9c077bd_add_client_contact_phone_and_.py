"""add client contact phone and appointment reminder tracking

Revision ID: e61cf9c077bd
Revises: 8c6ca4a3abc8
Create Date: 2026-09-20 03:57:41.179676

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e61cf9c077bd'
down_revision: Union[str, None] = '8c6ca4a3abc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('clients', sa.Column('contact_phone', sa.String(length=50), nullable=True))
    op.add_column('appointments', sa.Column('reminder_sent_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('appointments', 'reminder_sent_at')
    op.drop_column('clients', 'contact_phone')
