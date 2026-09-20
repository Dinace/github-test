"""encrypt client access tokens

Revision ID: 159f376bd70b
Revises: 350f53dcfbc7
Create Date: 2026-09-20 03:08:56.415871

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '159f376bd70b'
down_revision: Union[str, None] = '350f53dcfbc7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Client.meta_page_access_token / whatsapp_access_token passent en chiffré au repos
    # (platform_core.models.EncryptedString, Fernet) : la colonne stocke désormais du
    # ciphertext, plus volumineux qu'un token en clair — longueur doublée pour l'absorber.
    # Type SQL inchangé (VARCHAR) : EncryptedString est un TypeDecorator applicatif, pas un
    # nouveau type SQL, donc la migration se limite à la longueur.
    # batch_alter_table : SQLite ne supporte pas ALTER COLUMN ... TYPE directement (utilisé
    # en test uniquement, voir CLAUDE.md §3) ; sans lui, `ALTER TABLE ... ALTER COLUMN`
    # échoue avec une erreur de syntaxe sur ce dialecte. Sans effet sur PostgreSQL, qui
    # continue de générer un simple ALTER COLUMN.
    with op.batch_alter_table('clients') as batch_op:
        batch_op.alter_column('meta_page_access_token',
                   existing_type=sa.VARCHAR(length=500),
                   type_=sa.VARCHAR(length=1000),
                   existing_nullable=True)
        batch_op.alter_column('whatsapp_access_token',
                   existing_type=sa.VARCHAR(length=500),
                   type_=sa.VARCHAR(length=1000),
                   existing_nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('clients') as batch_op:
        batch_op.alter_column('whatsapp_access_token',
                   existing_type=sa.VARCHAR(length=1000),
                   type_=sa.VARCHAR(length=500),
                   existing_nullable=True)
        batch_op.alter_column('meta_page_access_token',
                   existing_type=sa.VARCHAR(length=1000),
                   type_=sa.VARCHAR(length=500),
                   existing_nullable=True)
