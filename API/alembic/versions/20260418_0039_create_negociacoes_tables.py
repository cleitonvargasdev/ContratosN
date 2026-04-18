"""create negociacoes tables

Revision ID: 20260418_0039
Revises: 20260415_0038
Create Date: 2026-04-18 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "20260418_0039"
down_revision = "20260415_0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "negociacoes",
        sa.Column("negociacao_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("cliente_id", sa.BigInteger(), sa.ForeignKey("clientes.clientes_id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("data_negociacao", sa.DateTime(timezone=True), nullable=True, index=True),
        sa.Column("valor_total_aberto", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("qtde_parcelas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valor_parcela", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("contrato_gerado_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("usuario_id", sa.BigInteger(), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("obs", sa.Text(), nullable=True),
        sa.Column("cobranca_segunda", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("cobranca_terca", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("cobranca_quarta", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("cobranca_quinta", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("cobranca_sexta", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("cobranca_sabado", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cobranca_domingo", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cobranca_feriado", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cobranca_mensal", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cobranca_quinzenal", sa.Boolean(), nullable=False, server_default="false"),
        sa.PrimaryKeyConstraint("negociacao_id"),
    )

    op.create_table(
        "negociacao_contratos",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("negociacao_id", sa.BigInteger(), sa.ForeignKey("negociacoes.negociacao_id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("contrato_id", sa.BigInteger(), sa.ForeignKey("contratos.contratos_id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("valor_aberto", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("negociacao_contratos")
    op.drop_table("negociacoes")
