"""add posts and client social fields

Revision ID: bbb7ab996621
Revises: fdd4ef0e8aa7
Create Date: 2026-09-20 01:00:29.667127

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bbb7ab996621'
down_revision: Union[str, None] = 'fdd4ef0e8aa7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('posts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('client_id', sa.UUID(), nullable=False),
    sa.Column('brief', sa.JSON().with_variant(postgresql.JSONB(astext_type=Text()), 'postgresql'), nullable=False),
    sa.Column('content', sa.JSON().with_variant(postgresql.JSONB(astext_type=Text()), 'postgresql'), nullable=True),
    sa.Column('status', sa.Enum('draft', 'pending_validation', 'validated', 'scheduled', 'published', name='post_status_enum'), nullable=False),
    sa.Column('scheduled_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('published_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('clients', sa.Column('brand_voice', sa.String(length=500), nullable=True))
    op.add_column('clients', sa.Column('meta_page_id', sa.String(length=100), nullable=True))
    op.add_column('clients', sa.Column('meta_page_access_token', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('clients', 'meta_page_access_token')
    op.drop_column('clients', 'meta_page_id')
    op.drop_column('clients', 'brand_voice')
    op.drop_table('posts')
