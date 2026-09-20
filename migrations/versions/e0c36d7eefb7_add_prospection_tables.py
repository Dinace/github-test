"""add prospection tables

Revision ID: e0c36d7eefb7
Revises: bed967cef17b
Create Date: 2026-09-20 01:32:04.800567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e0c36d7eefb7'
down_revision: Union[str, None] = 'bed967cef17b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('prospects',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('client_id', sa.UUID(), nullable=False),
    sa.Column('business_name', sa.String(length=255), nullable=False),
    sa.Column('sector', sa.String(length=50), nullable=False),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('source', sa.String(length=50), nullable=False),
    sa.Column('raw_data', sa.JSON().with_variant(postgresql.JSONB(astext_type=Text()), 'postgresql'), nullable=False),
    sa.Column('category', sa.Enum('favorable', 'a_qualifier', 'non_favorable', 'non_joignable', name='prospect_category_enum'), nullable=False),
    sa.Column('score', sa.Integer(), nullable=False),
    sa.Column('contact_message', sa.JSON().with_variant(postgresql.JSONB(astext_type=Text()), 'postgresql'), nullable=True),
    sa.Column('contact_status', sa.Enum('none', 'draft', 'pending_validation', 'validated', 'sent', name='contact_status_enum'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('contacted_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('clients', sa.Column('whatsapp_phone_number_id', sa.String(length=100), nullable=True))
    op.add_column('clients', sa.Column('whatsapp_access_token', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('clients', 'whatsapp_access_token')
    op.drop_column('clients', 'whatsapp_phone_number_id')
    op.drop_table('prospects')
