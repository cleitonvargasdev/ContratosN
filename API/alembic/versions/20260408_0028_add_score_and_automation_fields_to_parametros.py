"""add score and automation fields to parametros

Revision ID: 20260408_0028
Revises: 20260406_0027
Create Date: 2026-04-08 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260408_0028"
down_revision = "20260406_0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("parametros", sa.Column("emitir_sons", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("parametros", sa.Column("score_valor_inicial", sa.Integer(), nullable=False, server_default="1000"))
    op.add_column("parametros", sa.Column("score_pontos_atraso_parcela", sa.Integer(), nullable=False, server_default="15"))
    op.add_column("parametros", sa.Column("score_pontos_atraso_quitacao_contrato", sa.Integer(), nullable=False, server_default="30"))
    op.add_column("parametros", sa.Column("score_pontos_pagamento_em_dia", sa.Integer(), nullable=False, server_default="5"))
    op.add_column("parametros", sa.Column("score_pontos_quitacao_em_dia", sa.Integer(), nullable=False, server_default="20"))
    op.add_column("parametros", sa.Column("score_atualizacao_automatica", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("parametros", sa.Column("score_atualizacao_intervalo_minutos", sa.Integer(), nullable=False, server_default="60"))
    op.add_column("parametros", sa.Column("score_atualizacao_ultima_execucao", sa.DateTime(timezone=True), nullable=True))
    op.add_column("parametros", sa.Column("score_atualizacao_proxima_execucao", sa.DateTime(timezone=True), nullable=True))
    op.add_column("parametros", sa.Column("whatsapp_cobranca_automatica", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("parametros", sa.Column("whatsapp_cobranca_intervalo_minutos", sa.Integer(), nullable=False, server_default="60"))
    op.add_column("parametros", sa.Column("whatsapp_cobranca_ultima_execucao", sa.DateTime(timezone=True), nullable=True))
    op.add_column("parametros", sa.Column("whatsapp_cobranca_proxima_execucao", sa.DateTime(timezone=True), nullable=True))
    op.add_column("parametros", sa.Column("whatsapp_cobranca_dias_antes", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("parametros", sa.Column("whatsapp_cobranca_dias_depois", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("parametros", sa.Column("whatsapp_cobranca_hora_envio", sa.String(length=5), nullable=True, server_default="09:00"))
    op.add_column("parametros", sa.Column("whatsapp_cobranca_modelo", sa.String(length=500), nullable=True))

    op.alter_column("parametros", "emitir_sons", server_default=None)
    op.alter_column("parametros", "score_valor_inicial", server_default=None)
    op.alter_column("parametros", "score_pontos_atraso_parcela", server_default=None)
    op.alter_column("parametros", "score_pontos_atraso_quitacao_contrato", server_default=None)
    op.alter_column("parametros", "score_pontos_pagamento_em_dia", server_default=None)
    op.alter_column("parametros", "score_pontos_quitacao_em_dia", server_default=None)
    op.alter_column("parametros", "score_atualizacao_automatica", server_default=None)
    op.alter_column("parametros", "score_atualizacao_intervalo_minutos", server_default=None)
    op.alter_column("parametros", "whatsapp_cobranca_automatica", server_default=None)
    op.alter_column("parametros", "whatsapp_cobranca_intervalo_minutos", server_default=None)
    op.alter_column("parametros", "whatsapp_cobranca_dias_antes", server_default=None)
    op.alter_column("parametros", "whatsapp_cobranca_dias_depois", server_default=None)
    op.alter_column("parametros", "whatsapp_cobranca_hora_envio", server_default=None)


def downgrade() -> None:
    op.drop_column("parametros", "whatsapp_cobranca_modelo")
    op.drop_column("parametros", "whatsapp_cobranca_hora_envio")
    op.drop_column("parametros", "whatsapp_cobranca_dias_depois")
    op.drop_column("parametros", "whatsapp_cobranca_dias_antes")
    op.drop_column("parametros", "whatsapp_cobranca_proxima_execucao")
    op.drop_column("parametros", "whatsapp_cobranca_ultima_execucao")
    op.drop_column("parametros", "whatsapp_cobranca_intervalo_minutos")
    op.drop_column("parametros", "whatsapp_cobranca_automatica")
    op.drop_column("parametros", "score_atualizacao_proxima_execucao")
    op.drop_column("parametros", "score_atualizacao_ultima_execucao")
    op.drop_column("parametros", "score_atualizacao_intervalo_minutos")
    op.drop_column("parametros", "score_atualizacao_automatica")
    op.drop_column("parametros", "score_pontos_quitacao_em_dia")
    op.drop_column("parametros", "score_pontos_pagamento_em_dia")
    op.drop_column("parametros", "score_pontos_atraso_quitacao_contrato")
    op.drop_column("parametros", "score_pontos_atraso_parcela")
    op.drop_column("parametros", "score_valor_inicial")
    op.drop_column("parametros", "emitir_sons")