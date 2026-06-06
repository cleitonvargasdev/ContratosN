"""create suppliers and accounts payable tables

Revision ID: 20260606_0044
Revises: 20260511_0043
Create Date: 2026-06-06 11:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260606_0044"
down_revision = "20260511_0043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fornecedores",
        sa.Column("fornecedor_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("cpf_cnpj", sa.String(length=18), nullable=True),
        sa.Column("telefone", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("observacao", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("fornecedor_id"),
    )
    op.create_index(op.f("ix_fornecedores_fornecedor_id"), "fornecedores", ["fornecedor_id"], unique=False)
    op.create_index(op.f("ix_fornecedores_nome"), "fornecedores", ["nome"], unique=False)
    op.create_index(op.f("ix_fornecedores_cpf_cnpj"), "fornecedores", ["cpf_cnpj"], unique=False)
    op.create_index(op.f("ix_fornecedores_email"), "fornecedores", ["email"], unique=False)

    op.create_table(
        "contas_pagar",
        sa.Column("conta_pagar_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("descricao", sa.String(length=160), nullable=False),
        sa.Column("tipo_pessoa", sa.String(length=20), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("fornecedor_id", sa.Integer(), nullable=True),
        sa.Column("data_referencia_inicial", sa.Date(), nullable=True),
        sa.Column("data_referencia_final", sa.Date(), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("valor_total", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("valor_pago", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("saldo_pagar", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("quitado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("usuario_lancamento_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("tipo_pessoa in ('cliente', 'fornecedor', 'funcionario')", name="ck_contas_pagar_tipo_pessoa"),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.clientes_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedores.fornecedor_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["usuario_lancamento_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("conta_pagar_id"),
    )
    op.create_index(op.f("ix_contas_pagar_tipo_pessoa"), "contas_pagar", ["tipo_pessoa"], unique=False)
    op.create_index(op.f("ix_contas_pagar_cliente_id"), "contas_pagar", ["cliente_id"], unique=False)
    op.create_index(op.f("ix_contas_pagar_usuario_id"), "contas_pagar", ["usuario_id"], unique=False)
    op.create_index(op.f("ix_contas_pagar_fornecedor_id"), "contas_pagar", ["fornecedor_id"], unique=False)
    op.create_index(op.f("ix_contas_pagar_data_referencia_inicial"), "contas_pagar", ["data_referencia_inicial"], unique=False)
    op.create_index(op.f("ix_contas_pagar_data_referencia_final"), "contas_pagar", ["data_referencia_final"], unique=False)
    op.create_index(op.f("ix_contas_pagar_quitado"), "contas_pagar", ["quitado"], unique=False)
    op.create_index(op.f("ix_contas_pagar_usuario_lancamento_id"), "contas_pagar", ["usuario_lancamento_id"], unique=False)

    op.create_table(
        "contas_pagar_parcelas",
        sa.Column("parcela_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("conta_pagar_id", sa.BigInteger(), nullable=False),
        sa.Column("numero_parcela", sa.Integer(), nullable=False),
        sa.Column("descricao", sa.String(length=160), nullable=True),
        sa.Column("data_referencia_inicial", sa.Date(), nullable=True),
        sa.Column("data_referencia_final", sa.Date(), nullable=True),
        sa.Column("vencimento", sa.Date(), nullable=False),
        sa.Column("valor_original", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("acrescimos", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("desconto", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("valor_total", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("valor_pago", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("saldo_pagar", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("quitado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["conta_pagar_id"], ["contas_pagar.conta_pagar_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("parcela_id"),
    )
    op.create_index(op.f("ix_contas_pagar_parcelas_conta_pagar_id"), "contas_pagar_parcelas", ["conta_pagar_id"], unique=False)
    op.create_index(op.f("ix_contas_pagar_parcelas_data_referencia_inicial"), "contas_pagar_parcelas", ["data_referencia_inicial"], unique=False)
    op.create_index(op.f("ix_contas_pagar_parcelas_data_referencia_final"), "contas_pagar_parcelas", ["data_referencia_final"], unique=False)
    op.create_index(op.f("ix_contas_pagar_parcelas_vencimento"), "contas_pagar_parcelas", ["vencimento"], unique=False)
    op.create_index(op.f("ix_contas_pagar_parcelas_quitado"), "contas_pagar_parcelas", ["quitado"], unique=False)

    op.create_table(
        "contas_pagar_pagamentos",
        sa.Column("pagamento_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("parcela_id", sa.BigInteger(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("data_pagamento", sa.Date(), nullable=False),
        sa.Column("valor_pago", sa.Numeric(19, 4), nullable=False, server_default="0"),
        sa.Column("juros", sa.Float(), nullable=False, server_default="0"),
        sa.Column("acrescimos", sa.Float(), nullable=False, server_default="0"),
        sa.Column("desconto", sa.Float(), nullable=False, server_default="0"),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["parcela_id"], ["contas_pagar_parcelas.parcela_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("pagamento_id"),
    )
    op.create_index(op.f("ix_contas_pagar_pagamentos_parcela_id"), "contas_pagar_pagamentos", ["parcela_id"], unique=False)
    op.create_index(op.f("ix_contas_pagar_pagamentos_usuario_id"), "contas_pagar_pagamentos", ["usuario_id"], unique=False)
    op.create_index(op.f("ix_contas_pagar_pagamentos_data_pagamento"), "contas_pagar_pagamentos", ["data_pagamento"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_contas_pagar_pagamentos_data_pagamento"), table_name="contas_pagar_pagamentos")
    op.drop_index(op.f("ix_contas_pagar_pagamentos_usuario_id"), table_name="contas_pagar_pagamentos")
    op.drop_index(op.f("ix_contas_pagar_pagamentos_parcela_id"), table_name="contas_pagar_pagamentos")
    op.drop_table("contas_pagar_pagamentos")

    op.drop_index(op.f("ix_contas_pagar_parcelas_quitado"), table_name="contas_pagar_parcelas")
    op.drop_index(op.f("ix_contas_pagar_parcelas_vencimento"), table_name="contas_pagar_parcelas")
    op.drop_index(op.f("ix_contas_pagar_parcelas_data_referencia_final"), table_name="contas_pagar_parcelas")
    op.drop_index(op.f("ix_contas_pagar_parcelas_data_referencia_inicial"), table_name="contas_pagar_parcelas")
    op.drop_index(op.f("ix_contas_pagar_parcelas_conta_pagar_id"), table_name="contas_pagar_parcelas")
    op.drop_table("contas_pagar_parcelas")

    op.drop_index(op.f("ix_contas_pagar_usuario_lancamento_id"), table_name="contas_pagar")
    op.drop_index(op.f("ix_contas_pagar_quitado"), table_name="contas_pagar")
    op.drop_index(op.f("ix_contas_pagar_data_referencia_final"), table_name="contas_pagar")
    op.drop_index(op.f("ix_contas_pagar_data_referencia_inicial"), table_name="contas_pagar")
    op.drop_index(op.f("ix_contas_pagar_fornecedor_id"), table_name="contas_pagar")
    op.drop_index(op.f("ix_contas_pagar_usuario_id"), table_name="contas_pagar")
    op.drop_index(op.f("ix_contas_pagar_cliente_id"), table_name="contas_pagar")
    op.drop_index(op.f("ix_contas_pagar_tipo_pessoa"), table_name="contas_pagar")
    op.drop_table("contas_pagar")

    op.drop_index(op.f("ix_fornecedores_email"), table_name="fornecedores")
    op.drop_index(op.f("ix_fornecedores_cpf_cnpj"), table_name="fornecedores")
    op.drop_index(op.f("ix_fornecedores_nome"), table_name="fornecedores")
    op.drop_index(op.f("ix_fornecedores_fornecedor_id"), table_name="fornecedores")
    op.drop_table("fornecedores")