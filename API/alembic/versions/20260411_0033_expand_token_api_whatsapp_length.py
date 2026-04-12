"""expand token_api_whatsapp length

Revision ID: 20260411_0033
Revises: 20260411_0032
Create Date: 2026-04-11 23:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260411_0033"
down_revision = "20260411_0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "parametros",
        "token_api_whatsapp",
        existing_type=sa.String(length=30),
        type_=sa.String(length=120),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "parametros",
        "token_api_whatsapp",
        existing_type=sa.String(length=120),
        type_=sa.String(length=30),
        existing_nullable=True,
    )