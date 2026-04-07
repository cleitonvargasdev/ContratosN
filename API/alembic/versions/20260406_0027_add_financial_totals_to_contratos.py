"""add financial totals to contratos

Revision ID: 20260406_0027
Revises: 20260405_0026
Create Date: 2026-04-06 12:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260406_0027"
down_revision = "20260405_0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("contratos", sa.Column("valor_recebido", sa.Numeric(19, 4), nullable=False, server_default="0"))
    op.add_column("contratos", sa.Column("valor_em_aberto", sa.Numeric(19, 4), nullable=False, server_default="0"))
    op.add_column("contratos", sa.Column("valor_em_atraso", sa.Numeric(19, 4), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("contratos", "valor_em_atraso")
    op.drop_column("contratos", "valor_em_aberto")
    op.drop_column("contratos", "valor_recebido")