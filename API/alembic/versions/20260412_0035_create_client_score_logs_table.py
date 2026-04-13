"""create client score logs table

Revision ID: 20260412_0035
Revises: 20260412_0034
Create Date: 2026-04-12 16:40:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260412_0035"
down_revision = "20260412_0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_score_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("data_hora_evento", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evento", sa.String(length=40), nullable=False),
        sa.Column("pontuacao_anterior", sa.Integer(), nullable=False),
        sa.Column("variacao_pontos", sa.Integer(), nullable=False),
        sa.Column("pontuacao_atual", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.clientes_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_client_score_logs_cliente_id"), "client_score_logs", ["cliente_id"], unique=False)
    op.create_index(op.f("ix_client_score_logs_data_hora_evento"), "client_score_logs", ["data_hora_evento"], unique=False)
    op.create_index(op.f("ix_client_score_logs_evento"), "client_score_logs", ["evento"], unique=False)
    op.create_index(op.f("ix_client_score_logs_id"), "client_score_logs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_client_score_logs_id"), table_name="client_score_logs")
    op.drop_index(op.f("ix_client_score_logs_evento"), table_name="client_score_logs")
    op.drop_index(op.f("ix_client_score_logs_data_hora_evento"), table_name="client_score_logs")
    op.drop_index(op.f("ix_client_score_logs_cliente_id"), table_name="client_score_logs")
    op.drop_table("client_score_logs")
