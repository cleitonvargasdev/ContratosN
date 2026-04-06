"""add cep_responsavel to clientes

Revision ID: 20260405_0025
Revises: 20260405_0024
Create Date: 2026-04-05 18:40:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0025"
down_revision = "20260405_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clientes", sa.Column("cep_responsavel", sa.String(length=9), nullable=True))


def downgrade() -> None:
    op.drop_column("clientes", "cep_responsavel")