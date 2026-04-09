"""replace interval scheduling with weekday schedules on parametros

Revision ID: 20260408_0029
Revises: 20260408_0028
Create Date: 2026-04-08 14:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260408_0029"
down_revision = "20260408_0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("parametros", sa.Column("score_agendamentos", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("parametros", sa.Column("score_ultima_execucao_sucesso", sa.Boolean(), nullable=True))
    op.add_column("parametros", sa.Column("score_ultimo_erro", sa.Text(), nullable=True))
    op.add_column("parametros", sa.Column("whatsapp_agendamentos", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("parametros", sa.Column("whatsapp_ultima_execucao_sucesso", sa.Boolean(), nullable=True))
    op.add_column("parametros", sa.Column("whatsapp_ultimo_erro", sa.Text(), nullable=True))

    op.alter_column("parametros", "score_agendamentos", server_default=None)
    op.alter_column("parametros", "whatsapp_agendamentos", server_default=None)

    op.drop_column("parametros", "score_atualizacao_intervalo_minutos")
    op.drop_column("parametros", "whatsapp_cobranca_intervalo_minutos")
    op.drop_column("parametros", "whatsapp_cobranca_hora_envio")


def downgrade() -> None:
    op.add_column("parametros", sa.Column("whatsapp_cobranca_hora_envio", sa.String(length=5), nullable=True))
    op.add_column("parametros", sa.Column("whatsapp_cobranca_intervalo_minutos", sa.Integer(), nullable=False, server_default="60"))
    op.add_column("parametros", sa.Column("score_atualizacao_intervalo_minutos", sa.Integer(), nullable=False, server_default="60"))
    op.alter_column("parametros", "whatsapp_cobranca_intervalo_minutos", server_default=None)
    op.alter_column("parametros", "score_atualizacao_intervalo_minutos", server_default=None)
    op.drop_column("parametros", "whatsapp_ultimo_erro")
    op.drop_column("parametros", "whatsapp_ultima_execucao_sucesso")
    op.drop_column("parametros", "whatsapp_agendamentos")
    op.drop_column("parametros", "score_ultimo_erro")
    op.drop_column("parametros", "score_ultima_execucao_sucesso")
    op.drop_column("parametros", "score_agendamentos")