"""add api whatsapp to parametros

Revision ID: 20260411_0031
Revises: 20260410_0030
Create Date: 2026-04-11 19:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260411_0031"
down_revision = "20260410_0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("parametros", sa.Column("api_whatsapp", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("parametros", "api_whatsapp")
