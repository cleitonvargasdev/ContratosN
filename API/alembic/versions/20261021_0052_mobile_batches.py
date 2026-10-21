"""create mobile batch and occurrence tables

Revision ID: 20261021_0052
Revises: 20261019_0051
"""

from alembic import op
import sqlalchemy as sa


revision = "20261021_0052"
down_revision = "20261019_0051"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mobile_batches",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="created"),
        sa.Column("blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("block_reason", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("execution_requested_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("unlocked_at", sa.DateTime(timezone=True)),
        sa.Column("unlocked_by_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="SET NULL")),
        sa.Column("unlock_reason", sa.Text()),
        sa.UniqueConstraint("user_id", "source_id", name="uq_mobile_batches_user_source"),
    )
    op.create_index("ix_mobile_batches_user_id", "mobile_batches", ["user_id"])
    op.create_index("ix_mobile_batches_status", "mobile_batches", ["status"])
    op.create_index("ix_mobile_batches_blocked", "mobile_batches", ["blocked"])
    op.create_table(
        "mobile_batch_items",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("batch_id", sa.BigInteger(), sa.ForeignKey("mobile_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_item_id", sa.String(100), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clientes.clientes_id", ondelete="SET NULL")),
        sa.Column("contract_id", sa.BigInteger(), sa.ForeignKey("contratos.contratos_id", ondelete="SET NULL")),
        sa.Column("installment_id", sa.BigInteger(), sa.ForeignKey("contas_receber.id", ondelete="SET NULL")),
        sa.Column("amount", sa.Numeric(19, 4)),
        sa.Column("latitude", sa.String(50)), sa.Column("longitude", sa.String(50)), sa.Column("gps_status", sa.String(20)),
        sa.Column("device_recorded_at", sa.DateTime(timezone=True)), sa.Column("server_date", sa.Date(), nullable=False),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("block_reason", sa.Text()), sa.Column("receipt_id", sa.BigInteger(), sa.ForeignKey("recebimentos.recebimento_id", ondelete="SET NULL")),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("batch_id", "source_item_id", name="uq_mobile_batch_items_source"),
        sa.UniqueConstraint("user_id", "source_item_id", name="uq_mobile_batch_items_user_source"),
    )
    for column in ("batch_id", "user_id", "client_id", "contract_id", "installment_id", "processed", "blocked"):
        op.create_index(f"ix_mobile_batch_items_{column}", "mobile_batch_items", [column])
    op.create_table(
        "mobile_occurrences",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("batch_id", sa.BigInteger(), sa.ForeignKey("mobile_batches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.BigInteger(), sa.ForeignKey("mobile_batch_items.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clientes.clientes_id", ondelete="SET NULL")),
        sa.Column("contract_id", sa.BigInteger(), sa.ForeignKey("contratos.contratos_id", ondelete="SET NULL")),
        sa.Column("kind", sa.String(20), nullable=False), sa.Column("latitude", sa.String(50)), sa.Column("longitude", sa.String(50)),
        sa.Column("gps_status", sa.String(20)), sa.Column("device_time", sa.DateTime(timezone=True)),
        sa.Column("server_date", sa.Date(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("batch_id", "user_id", "client_id", "contract_id"):
        op.create_index(f"ix_mobile_occurrences_{column}", "mobile_occurrences", [column])


def downgrade() -> None:
    op.drop_table("mobile_occurrences")
    op.drop_table("mobile_batch_items")
    op.drop_table("mobile_batches")
