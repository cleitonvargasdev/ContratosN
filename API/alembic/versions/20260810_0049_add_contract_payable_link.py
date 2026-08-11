"""add contract payable link

Revision ID: 20260810_0049
Revises: 20260808_0048
"""
from alembic import op
import sqlalchemy as sa

revision = "20260810_0049"
down_revision = "20260808_0048"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("contratos", sa.Column("conta_pagar_id", sa.BigInteger(), sa.ForeignKey("contas_pagar.conta_pagar_id", ondelete="SET NULL"), nullable=True))
    op.create_index("ix_contratos_conta_pagar_id", "contratos", ["conta_pagar_id"])


def downgrade() -> None:
    op.drop_index("ix_contratos_conta_pagar_id", table_name="contratos")
    op.drop_column("contratos", "conta_pagar_id")
