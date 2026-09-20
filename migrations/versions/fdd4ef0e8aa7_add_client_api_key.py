"""add client api key

Revision ID: fdd4ef0e8aa7
Revises: 72ac7a34d02a
Create Date: 2026-09-20 00:15:08.243999

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fdd4ef0e8aa7'
down_revision: Union[str, None] = '72ac7a34d02a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('clients', sa.Column('api_key_hash', sa.String(length=64), nullable=False))
    op.create_index(op.f('ix_clients_api_key_hash'), 'clients', ['api_key_hash'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_clients_api_key_hash'), table_name='clients')
    op.drop_column('clients', 'api_key_hash')
