"""add regra_juros_id to contratos

Revision ID: 20260405_0020
Revises: 20260405_0019
Create Date: 2026-04-05 15:38:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0020"
down_revision = "20260405_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("contratos", sa.Column("regra_juros_id", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("contratos", "regra_juros_id")