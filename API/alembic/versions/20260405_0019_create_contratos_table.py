"""create contratos table

Revision ID: 20260405_0019
Revises: 20260405_0018
Create Date: 2026-04-05 15:32:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0019"
down_revision = "20260405_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contratos",
        sa.Column("contratos_id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("data_lancto", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_contrato", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cliente_id", sa.Integer(), nullable=True),
        sa.Column("plano_id", sa.BigInteger(), nullable=True),
        sa.Column("qtde_dias", sa.Integer(), nullable=True),
        sa.Column("percent_juros", sa.Float(), nullable=True),
        sa.Column("valor_empretismo", sa.Numeric(19, 4), nullable=True),
        sa.Column("data_final", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valor_final", sa.Numeric(19, 4), nullable=True),
        sa.Column("quitado", sa.Boolean(), nullable=True),
        sa.Column("obs", sa.Text(), nullable=True),
        sa.Column("valor_parcela", sa.Numeric(19, 4), nullable=True),
        sa.Column("user_add", sa.Integer(), nullable=True),
        sa.Column("contrato_status", sa.Integer(), nullable=False),
        sa.Column("negociacao_id", sa.BigInteger(), nullable=True),
        sa.Column("usuario_id_vendedor", sa.Integer(), nullable=True),
        sa.Column("comissao_percentual", sa.Numeric(19, 0), nullable=True),
        sa.Column("valor_comissao_previsto", sa.Numeric(19, 4), nullable=True),
        sa.Column("valor_comissao_apurada", sa.Numeric(19, 4), nullable=True),
        sa.Column("regra_comissao_id", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.clientes_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["plano_id"], ["planos_pagamentos.planos_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_add"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["usuario_id_vendedor"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("contratos_id"),
    )

    op.create_index(op.f("ix_contratos_contratos_id"), "contratos", ["contratos_id"], unique=False)
    op.create_index(op.f("ix_contratos_data_lancto"), "contratos", ["data_lancto"], unique=False)
    op.create_index(op.f("ix_contratos_data_contrato"), "contratos", ["data_contrato"], unique=False)
    op.create_index(op.f("ix_contratos_cliente_id"), "contratos", ["cliente_id"], unique=False)
    op.create_index(op.f("ix_contratos_plano_id"), "contratos", ["plano_id"], unique=False)
    op.create_index(op.f("ix_contratos_user_add"), "contratos", ["user_add"], unique=False)
    op.create_index(op.f("ix_contratos_contrato_status"), "contratos", ["contrato_status"], unique=False)
    op.create_index(op.f("ix_contratos_usuario_id_vendedor"), "contratos", ["usuario_id_vendedor"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_contratos_usuario_id_vendedor"), table_name="contratos")
    op.drop_index(op.f("ix_contratos_contrato_status"), table_name="contratos")
    op.drop_index(op.f("ix_contratos_user_add"), table_name="contratos")
    op.drop_index(op.f("ix_contratos_plano_id"), table_name="contratos")
    op.drop_index(op.f("ix_contratos_cliente_id"), table_name="contratos")
    op.drop_index(op.f("ix_contratos_data_contrato"), table_name="contratos")
    op.drop_index(op.f("ix_contratos_data_lancto"), table_name="contratos")
    op.drop_index(op.f("ix_contratos_contratos_id"), table_name="contratos")
    op.drop_table("contratos")