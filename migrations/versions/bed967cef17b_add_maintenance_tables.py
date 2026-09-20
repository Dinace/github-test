"""add maintenance tables

Revision ID: bed967cef17b
Revises: bbb7ab996621
Create Date: 2026-09-20 01:14:41.670500

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bed967cef17b'
down_revision: Union[str, None] = 'bbb7ab996621'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('backups',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('r2_key', sa.String(length=255), nullable=False),
    sa.Column('size_bytes', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('r2_key')
    )
    op.create_table('restore_requests',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('backup_id', sa.UUID(), nullable=False),
    sa.Column('reason', sa.String(length=1000), nullable=False),
    sa.Column('status', sa.Enum('proposed', 'confirmed', 'executed', 'rejected', name='restore_status_enum'), nullable=False),
    sa.Column('requested_at', sa.DateTime(), nullable=False),
    sa.Column('confirmed_by', sa.String(length=255), nullable=True),
    sa.Column('confirmed_at', sa.DateTime(), nullable=True),
    sa.Column('executed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['backup_id'], ['backups.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('notifications',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('category', sa.Enum('site_down', 'backup_failure', 'security_finding', 'error_spike', name='notif_category_enum'), nullable=False),
    sa.Column('severity', sa.Enum('info', 'warning', 'critical', name='notif_severity_enum'), nullable=False),
    sa.Column('message', sa.String(length=1000), nullable=False),
    sa.Column('client_id', sa.UUID(), nullable=True),
    sa.Column('site_id', sa.UUID(), nullable=True),
    sa.Column('status', sa.Enum('pending', 'acknowledged', name='notif_status_enum'), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
    sa.Column('acknowledged_by', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.ForeignKeyConstraint(['site_id'], ['sites.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('notifications')
    op.drop_table('restore_requests')
    op.drop_table('backups')
