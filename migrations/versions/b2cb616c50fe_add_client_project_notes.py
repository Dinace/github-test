"""add client project notes

Revision ID: b2cb616c50fe
Revises: 9e07474bf202
Create Date: 2026-09-20 09:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2cb616c50fe'
down_revision: Union[str, None] = '9e07474bf202'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('clients', sa.Column('project_notes', sa.String(length=2000), nullable=True))


def downgrade() -> None:
    op.drop_column('clients', 'project_notes')
