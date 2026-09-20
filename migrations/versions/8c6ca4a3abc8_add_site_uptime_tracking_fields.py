"""add site uptime tracking fields

Revision ID: 8c6ca4a3abc8
Revises: 159f376bd70b
Create Date: 2026-09-20 03:22:16.635019

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c6ca4a3abc8'
down_revision: Union[str, None] = '159f376bd70b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sites', sa.Column('uptime_monitor_id', sa.String(length=100), nullable=True))
    op.add_column('sites', sa.Column('last_uptime_check_at', sa.DateTime(), nullable=True))
    op.add_column('sites', sa.Column('down_since', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('sites', 'down_since')
    op.drop_column('sites', 'last_uptime_check_at')
    op.drop_column('sites', 'uptime_monitor_id')
