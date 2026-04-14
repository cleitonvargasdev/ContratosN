"""add contract schedule and rent flags

Revision ID: 20260413_0037
Revises: 20260412_0036
Create Date: 2026-04-13 14:40:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260413_0037"
down_revision = "20260412_0036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("contratos", sa.Column("aluguel", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("contratos", sa.Column("cobranca_segunda", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("contratos", sa.Column("cobranca_terca", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("contratos", sa.Column("cobranca_quarta", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("contratos", sa.Column("cobranca_quinta", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("contratos", sa.Column("cobranca_sexta", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("contratos", sa.Column("cobranca_sabado", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("contratos", sa.Column("cobranca_domingo", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("contratos", sa.Column("cobranca_feriado", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("contratos", sa.Column("cobranca_mensal", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("contratos", sa.Column("cobranca_quinzenal", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute("UPDATE contratos SET recorrencia = false WHERE recorrencia IS NULL")
    op.execute("UPDATE contratos SET cobranca_mensal = true WHERE recorrencia = true")


def downgrade() -> None:
    op.drop_column("contratos", "cobranca_quinzenal")
    op.drop_column("contratos", "cobranca_mensal")
    op.drop_column("contratos", "cobranca_feriado")
    op.drop_column("contratos", "cobranca_domingo")
    op.drop_column("contratos", "cobranca_sabado")
    op.drop_column("contratos", "cobranca_sexta")
    op.drop_column("contratos", "cobranca_quinta")
    op.drop_column("contratos", "cobranca_quarta")
    op.drop_column("contratos", "cobranca_terca")
    op.drop_column("contratos", "cobranca_segunda")
    op.drop_column("contratos", "aluguel")