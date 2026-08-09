"""add commission settings

Revision ID: 20260808_0046
Revises: 20260606_0045
"""

from alembic import op
import sqlalchemy as sa


revision = "20260808_0046"
down_revision = "20260606_0045"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("recebe_comissao_venda", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("usuarios", sa.Column("taxa_venda", sa.Numeric(8, 2), nullable=True))
    op.add_column("usuarios", sa.Column("recebe_comissao_cob", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("usuarios", sa.Column("taxa_cob", sa.Numeric(8, 2), nullable=True))
    op.add_column("parametros", sa.Column("comissao_apos_quitacao_venda", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("parametros", sa.Column("comissao_apos_quitacao_cobranca", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("contratos", sa.Column("pagar_comissao_venda", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("contratos", sa.Column("pagar_comissao_cobranca", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("contratos", "pagar_comissao_cobranca")
    op.drop_column("contratos", "pagar_comissao_venda")
    op.drop_column("parametros", "comissao_apos_quitacao_cobranca")
    op.drop_column("parametros", "comissao_apos_quitacao_venda")
    op.drop_column("usuarios", "taxa_cob")
    op.drop_column("usuarios", "recebe_comissao_cob")
    op.drop_column("usuarios", "taxa_venda")
    op.drop_column("usuarios", "recebe_comissao_venda")
