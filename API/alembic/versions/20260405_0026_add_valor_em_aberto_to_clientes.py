"""add valor_em_aberto to clientes

Revision ID: 20260405_0026
Revises: 20260405_0025
Create Date: 2026-04-05 19:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0026"
down_revision = "20260405_0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clientes", sa.Column("valor_em_aberto", sa.Numeric(19, 4), nullable=True))


def downgrade() -> None:
    op.drop_column("clientes", "valor_em_aberto")