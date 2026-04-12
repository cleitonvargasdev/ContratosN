"""add whatsapp flags to parametros

Revision ID: 20260411_0032
Revises: 20260411_0031
Create Date: 2026-04-11 21:25:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260411_0032"
down_revision = "20260411_0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("parametros", sa.Column("flag_whatsapp_telefone1", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("parametros", sa.Column("flag_whatsapp_telefone2", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column("parametros", "flag_whatsapp_telefone1", server_default=None)
    op.alter_column("parametros", "flag_whatsapp_telefone2", server_default=None)


def downgrade() -> None:
    op.drop_column("parametros", "flag_whatsapp_telefone2")
    op.drop_column("parametros", "flag_whatsapp_telefone1")