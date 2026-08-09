"""add commission batches

Revision ID: 20260808_0048
Revises: 20260808_0047
"""
from alembic import op
import sqlalchemy as sa

revision = "20260808_0048"
down_revision = "20260808_0047"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("comissoes_lotes",
        sa.Column("lote_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("funcionario_id", sa.BigInteger(), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("data_inicial", sa.Date(), nullable=False), sa.Column("data_final", sa.Date(), nullable=False),
        sa.Column("situacao", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("conta_pagar_id", sa.BigInteger(), sa.ForeignKey("contas_pagar.conta_pagar_id", ondelete="SET NULL")),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.add_column("comissoes_lancamentos", sa.Column("lote_id", sa.BigInteger(), sa.ForeignKey("comissoes_lotes.lote_id", ondelete="SET NULL"), nullable=True))

def downgrade() -> None:
    op.drop_column("comissoes_lancamentos", "lote_id")
    op.drop_table("comissoes_lotes")
