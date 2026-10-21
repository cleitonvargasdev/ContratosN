"""store solicitation payloads in mobile batches

Revision ID: 20261021_0053
Revises: 20261021_0052
"""

from alembic import op
import sqlalchemy as sa


revision = "20261021_0053"
down_revision = "20261021_0052"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("mobile_batch_items", sa.Column("solicitation_id", sa.BigInteger(), sa.ForeignKey("solicitacoes.id", ondelete="SET NULL")))
    op.add_column("mobile_batch_items", sa.Column("solicitation_data", sa.JSON(), nullable=True))
    op.create_index("ix_mobile_batch_items_solicitation_id", "mobile_batch_items", ["solicitation_id"])


def downgrade() -> None:
    op.drop_index("ix_mobile_batch_items_solicitation_id", table_name="mobile_batch_items")
    op.drop_column("mobile_batch_items", "solicitation_data")
    op.drop_column("mobile_batch_items", "solicitation_id")
