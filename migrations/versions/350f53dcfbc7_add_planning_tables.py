"""add planning tables

Revision ID: 350f53dcfbc7
Revises: e0c36d7eefb7
Create Date: 2026-09-20 01:49:53.886711

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '350f53dcfbc7'
down_revision: Union[str, None] = 'e0c36d7eefb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('activity_events',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('client_id', sa.UUID(), nullable=False),
    sa.Column('agent', sa.String(length=50), nullable=False),
    sa.Column('entity_type', sa.String(length=50), nullable=False),
    sa.Column('entity_id', sa.UUID(), nullable=False),
    sa.Column('event_type', sa.String(length=100), nullable=False),
    sa.Column('details', sa.JSON().with_variant(postgresql.JSONB(astext_type=Text()), 'postgresql'), nullable=False),
    sa.Column('occurred_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('appointments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('client_id', sa.UUID(), nullable=False),
    sa.Column('staff_contact', sa.String(length=255), nullable=False),
    sa.Column('purpose', sa.String(length=255), nullable=False),
    sa.Column('scheduled_at', sa.DateTime(), nullable=False),
    sa.Column('duration_minutes', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('proposed', 'confirmed', 'cancelled', 'completed', name='appointment_status_enum'), nullable=False),
    sa.Column('notes', sa.String(length=2000), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('confirmed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('appointments')
    op.drop_table('activity_events')
