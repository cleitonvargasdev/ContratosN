"""add rule snapshot to client score logs

Revision ID: 20260412_0036
Revises: 20260412_0035
Create Date: 2026-04-12 20:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260412_0036"
down_revision = "20260412_0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("client_score_logs", sa.Column("regra_pontos", sa.Integer(), nullable=True))
    op.add_column("client_score_logs", sa.Column("quantidade_referencia", sa.Integer(), nullable=True))
    op.add_column("client_score_logs", sa.Column("detalhe_calculo", sa.String(length=200), nullable=True))


def downgrade() -> None:
    op.drop_column("client_score_logs", "detalhe_calculo")
    op.drop_column("client_score_logs", "quantidade_referencia")
    op.drop_column("client_score_logs", "regra_pontos")
