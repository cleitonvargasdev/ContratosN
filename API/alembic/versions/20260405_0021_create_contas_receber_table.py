"""create contas_receber table

Revision ID: 20260405_0021
Revises: 20260405_0020
Create Date: 2026-04-05 15:46:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0021"
down_revision = "20260405_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contas_receber",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("contratos_id", sa.BigInteger(), nullable=True),
        sa.Column("vencimento_original", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vencimentol", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valor_base", sa.Float(), nullable=True),
        sa.Column("valor_total", sa.Float(), nullable=True),
        sa.Column("data_recebimento", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valor_recebido", sa.Numeric(19, 4), nullable=True),
        sa.Column("percent_juros", sa.Float(), nullable=True),
        sa.Column("quitado", sa.Boolean(), nullable=True),
        sa.Column("usuarios_id", sa.Integer(), nullable=True),
        sa.Column("parcela_nro", sa.Integer(), nullable=True),
        sa.Column("valor_juros", sa.Float(), nullable=True),
        sa.Column("dias_atraso_quitacao", sa.Integer(), nullable=True),
        sa.Column("dias_atrasado", sa.Integer(), nullable=True),
        sa.Column("desconto", sa.Float(), nullable=True),
        sa.Column("prorrogada", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["contratos_id"], ["contratos.contratos_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["usuarios_id"], ["usuarios.id"], ondelete="SET NULL"),
    )

    op.create_index(op.f("ix_contas_receber_contratos_id"), "contas_receber", ["contratos_id"], unique=False)
    op.create_index(op.f("ix_contas_receber_vencimento_original"), "contas_receber", ["vencimento_original"], unique=False)
    op.create_index(op.f("ix_contas_receber_vencimentol"), "contas_receber", ["vencimentol"], unique=False)
    op.create_index(op.f("ix_contas_receber_usuarios_id"), "contas_receber", ["usuarios_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_contas_receber_usuarios_id"), table_name="contas_receber")
    op.drop_index(op.f("ix_contas_receber_vencimentol"), table_name="contas_receber")
    op.drop_index(op.f("ix_contas_receber_vencimento_original"), table_name="contas_receber")
    op.drop_index(op.f("ix_contas_receber_contratos_id"), table_name="contas_receber")
    op.drop_table("contas_receber")