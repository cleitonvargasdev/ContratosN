"""add commission ledger

Revision ID: 20260808_0047
Revises: 20260808_0046
"""
from alembic import op
import sqlalchemy as sa

revision = "20260808_0047"
down_revision = "20260808_0046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comissoes_lancamentos",
        sa.Column("comissao_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tipo", sa.String(12), nullable=False),
        sa.Column("situacao", sa.String(16), nullable=False, server_default="pendente"),
        sa.Column("funcionario_id", sa.BigInteger(), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("contrato_id", sa.BigInteger(), sa.ForeignKey("contratos.contratos_id", ondelete="SET NULL")),
        sa.Column("recebimento_id", sa.BigInteger(), sa.ForeignKey("recebimentos.recebimento_id", ondelete="SET NULL")),
        sa.Column("competencia", sa.Date(), nullable=False),
        sa.Column("base_calculo", sa.Numeric(19, 4), nullable=False),
        sa.Column("percentual", sa.Numeric(8, 2), nullable=False),
        sa.Column("valor_comissao", sa.Numeric(19, 4), nullable=False),
        sa.Column("conta_pagar_id", sa.BigInteger(), sa.ForeignKey("contas_pagar.conta_pagar_id", ondelete="SET NULL")),
        sa.Column("origem_comissao_id", sa.BigInteger(), sa.ForeignKey("comissoes_lancamentos.comissao_id", ondelete="SET NULL")),
        sa.Column("motivo", sa.Text()),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    for column in ("tipo", "situacao", "funcionario_id", "contrato_id", "recebimento_id", "competencia", "conta_pagar_id"):
        op.create_index(f"ix_comissoes_lancamentos_{column}", "comissoes_lancamentos", [column])


def downgrade() -> None:
    op.drop_table("comissoes_lancamentos")
