"""add score pontos negociacao to parametros

Revision ID: 20260418_0040
Revises: 20260418_0039
Create Date: 2026-04-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260418_0040"
down_revision = "20260418_0039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "parametros",
        sa.Column("score_pontos_negociacao", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("parametros", "score_pontos_negociacao", server_default=None)


def downgrade() -> None:
    op.drop_column("parametros", "score_pontos_negociacao")