"""add onboarding notifications table

Revision ID: 9e07474bf202
Revises: e61cf9c077bd
Create Date: 2026-09-20 08:25:18.150166

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e07474bf202'
down_revision: Union[str, None] = 'e61cf9c077bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'onboarding_notifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('client_id', sa.UUID(), nullable=False),
        sa.Column('step_key', sa.String(length=100), nullable=False),
        sa.Column('team', sa.Enum('commercial', 'technique', name='onboarding_team_enum'), nullable=False),
        sa.Column('message', sa.String(length=500), nullable=False),
        sa.Column(
            'status',
            sa.Enum('pending', 'acknowledged', name='onboarding_notif_status_enum'),
            nullable=False,
        ),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('onboarding_notifications')
