"""add recorrencia to contratos

Revision ID: 20260405_0023
Revises: 20260405_0022
Create Date: 2026-04-05 16:02:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0023"
down_revision = "20260405_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("contratos", sa.Column("recorrencia", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("contratos", "recorrencia")