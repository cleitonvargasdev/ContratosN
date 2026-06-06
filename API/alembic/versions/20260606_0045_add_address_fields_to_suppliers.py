"""add address fields to suppliers

Revision ID: 20260606_0045
Revises: 20260606_0044
Create Date: 2026-06-06 13:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260606_0045"
down_revision = "20260606_0044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("fornecedores", sa.Column("cep", sa.String(length=8), nullable=True))
    op.add_column("fornecedores", sa.Column("endereco", sa.String(length=180), nullable=True))
    op.add_column("fornecedores", sa.Column("numero", sa.String(length=20), nullable=True))
    op.add_column("fornecedores", sa.Column("complemento", sa.String(length=120), nullable=True))
    op.add_column("fornecedores", sa.Column("bairro", sa.String(length=120), nullable=True))
    op.add_column("fornecedores", sa.Column("cidade", sa.String(length=120), nullable=True))
    op.add_column("fornecedores", sa.Column("uf", sa.String(length=2), nullable=True))


def downgrade() -> None:
    op.drop_column("fornecedores", "uf")
    op.drop_column("fornecedores", "cidade")
    op.drop_column("fornecedores", "bairro")
    op.drop_column("fornecedores", "complemento")
    op.drop_column("fornecedores", "numero")
    op.drop_column("fornecedores", "endereco")
    op.drop_column("fornecedores", "cep")