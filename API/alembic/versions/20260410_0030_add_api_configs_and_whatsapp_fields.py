"""add api configs and whatsapp fields

Revision ID: 20260410_0030
Revises: 20260408_0029
Create Date: 2026-04-10 10:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260410_0030"
down_revision = "20260408_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("parametros", sa.Column("usuario_api_whatsapp", sa.String(length=100), nullable=True))
    op.add_column("parametros", sa.Column("token_api_whatsapp", sa.String(length=30), nullable=True))
    op.add_column("parametros", sa.Column("regra_nono_dig_whats", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("parametros", sa.Column("sufixo_whatsapp", sa.String(length=30), nullable=True))
    op.add_column("parametros", sa.Column("msg_renovacao", sa.Text(), nullable=True))
    op.add_column("parametros", sa.Column("msg_negociacao", sa.Text(), nullable=True))
    op.add_column("parametros", sa.Column("pais_whatsapp", sa.Integer(), nullable=False, server_default="55"))
    op.add_column("parametros", sa.Column("msg_campanha", sa.Text(), nullable=True))
    op.add_column("parametros", sa.Column("ligar_websocket", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("parametros", sa.Column("silenciar_mensagem", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column("parametros", "regra_nono_dig_whats", server_default=None)
    op.alter_column("parametros", "pais_whatsapp", server_default=None)
    op.alter_column("parametros", "ligar_websocket", server_default=None)
    op.alter_column("parametros", "silenciar_mensagem", server_default=None)

    op.create_table(
        "apis",
        sa.Column("api_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("nome_api", sa.String(length=120), nullable=True),
        sa.Column("funcionalidade", sa.String(length=200), nullable=True),
        sa.Column("url", sa.String(length=255), nullable=True),
        sa.Column("key1", sa.String(length=100), nullable=True),
        sa.Column("value1", sa.String(length=255), nullable=True),
        sa.Column("key2", sa.String(length=100), nullable=True),
        sa.Column("value2", sa.String(length=255), nullable=True),
        sa.Column("key3", sa.String(length=100), nullable=True),
        sa.Column("value3", sa.String(length=255), nullable=True),
        sa.Column("key4", sa.String(length=100), nullable=True),
        sa.Column("value4", sa.String(length=255), nullable=True),
        sa.Column("key5", sa.String(length=100), nullable=True),
        sa.Column("value5", sa.String(length=255), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("api_id"),
    )
    op.create_index(op.f("ix_apis_api_id"), "apis", ["api_id"], unique=False)
    op.create_index(op.f("ix_apis_nome_api"), "apis", ["nome_api"], unique=False)
    op.create_index(op.f("ix_apis_usuario_id"), "apis", ["usuario_id"], unique=False)

    op.add_column("contas_receber", sa.Column("msg_whatsapp", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("contas_receber", sa.Column("dt_hora_envio", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contas_receber", sa.Column("tipo_envio", sa.Integer(), nullable=True))
    op.alter_column("contas_receber", "msg_whatsapp", server_default=None)

    op.add_column("clientes", sa.Column("nao_enviar_whatsapp", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column("clientes", "nao_enviar_whatsapp", server_default=None)


def downgrade() -> None:
    op.drop_column("clientes", "nao_enviar_whatsapp")

    op.drop_column("contas_receber", "tipo_envio")
    op.drop_column("contas_receber", "dt_hora_envio")
    op.drop_column("contas_receber", "msg_whatsapp")

    op.drop_index(op.f("ix_apis_usuario_id"), table_name="apis")
    op.drop_index(op.f("ix_apis_nome_api"), table_name="apis")
    op.drop_index(op.f("ix_apis_api_id"), table_name="apis")
    op.drop_table("apis")

    op.drop_column("parametros", "silenciar_mensagem")
    op.drop_column("parametros", "ligar_websocket")
    op.drop_column("parametros", "msg_campanha")
    op.drop_column("parametros", "pais_whatsapp")
    op.drop_column("parametros", "msg_negociacao")
    op.drop_column("parametros", "msg_renovacao")
    op.drop_column("parametros", "sufixo_whatsapp")
    op.drop_column("parametros", "regra_nono_dig_whats")
    op.drop_column("parametros", "token_api_whatsapp")
    op.drop_column("parametros", "usuario_api_whatsapp")