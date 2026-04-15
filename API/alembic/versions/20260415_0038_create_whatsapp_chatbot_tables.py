"""create whatsapp chatbot tables

Revision ID: 20260415_0038
Revises: 20260413_0037
Create Date: 2026-04-15 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260415_0038"
down_revision = "20260413_0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_chatbot_sessions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("current_state", sa.String(length=40), nullable=False),
        sa.Column("identified_name", sa.String(length=120), nullable=True),
        sa.Column("identified_document", sa.String(length=18), nullable=True),
        sa.Column("context_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_interaction_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opted_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clientes.clientes_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_whatsapp_chatbot_sessions_chat_id"), "whatsapp_chatbot_sessions", ["chat_id"], unique=True)
    op.create_index(op.f("ix_whatsapp_chatbot_sessions_phone"), "whatsapp_chatbot_sessions", ["phone"], unique=False)
    op.create_index(op.f("ix_whatsapp_chatbot_sessions_client_id"), "whatsapp_chatbot_sessions", ["client_id"], unique=False)

    op.create_table(
        "solicitacoes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.BigInteger(), nullable=True),
        sa.Column("nome_informado", sa.String(length=120), nullable=True),
        sa.Column("telefone", sa.String(length=20), nullable=True),
        sa.Column("cpf_cnpj", sa.String(length=18), nullable=True),
        sa.Column("valor_pretendido", sa.Numeric(19, 4), nullable=True),
        sa.Column("frequencia_pagamento", sa.String(length=20), nullable=True),
        sa.Column("numero_parcelas", sa.Integer(), nullable=True),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("vendedor_id", sa.Integer(), nullable=True),
        sa.Column("valor_parcela", sa.Numeric(19, 4), nullable=True),
        sa.Column("taxa_juros", sa.Numeric(19, 6), nullable=True),
        sa.Column("contrato_id", sa.BigInteger(), nullable=True),
        sa.Column("usuario_id_aprovou", sa.Integer(), nullable=True),
        sa.Column("datahora_solicitacao", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("datahora_aprovacao", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.clientes_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["session_id"], ["whatsapp_chatbot_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["vendedor_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["contrato_id"], ["contratos.contratos_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["usuario_id_aprovou"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_solicitacoes_cliente_id"), "solicitacoes", ["cliente_id"], unique=False)
    op.create_index(op.f("ix_solicitacoes_session_id"), "solicitacoes", ["session_id"], unique=False)
    op.create_index(op.f("ix_solicitacoes_telefone"), "solicitacoes", ["telefone"], unique=False)
    op.create_index(op.f("ix_solicitacoes_cpf_cnpj"), "solicitacoes", ["cpf_cnpj"], unique=False)
    op.create_index(op.f("ix_solicitacoes_vendedor_id"), "solicitacoes", ["vendedor_id"], unique=False)
    op.create_index(op.f("ix_solicitacoes_contrato_id"), "solicitacoes", ["contrato_id"], unique=False)
    op.create_index(op.f("ix_solicitacoes_usuario_id_aprovou"), "solicitacoes", ["usuario_id_aprovou"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_solicitacoes_usuario_id_aprovou"), table_name="solicitacoes")
    op.drop_index(op.f("ix_solicitacoes_contrato_id"), table_name="solicitacoes")
    op.drop_index(op.f("ix_solicitacoes_vendedor_id"), table_name="solicitacoes")
    op.drop_index(op.f("ix_solicitacoes_cpf_cnpj"), table_name="solicitacoes")
    op.drop_index(op.f("ix_solicitacoes_telefone"), table_name="solicitacoes")
    op.drop_index(op.f("ix_solicitacoes_session_id"), table_name="solicitacoes")
    op.drop_index(op.f("ix_solicitacoes_cliente_id"), table_name="solicitacoes")
    op.drop_table("solicitacoes")

    op.drop_index(op.f("ix_whatsapp_chatbot_sessions_client_id"), table_name="whatsapp_chatbot_sessions")
    op.drop_index(op.f("ix_whatsapp_chatbot_sessions_phone"), table_name="whatsapp_chatbot_sessions")
    op.drop_index(op.f("ix_whatsapp_chatbot_sessions_chat_id"), table_name="whatsapp_chatbot_sessions")
    op.drop_table("whatsapp_chatbot_sessions")