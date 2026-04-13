"""create whatsapp dispatch tables

Revision ID: 20260412_0034
Revises: 20260411_0033
Create Date: 2026-04-12 10:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260412_0034"
down_revision = "20260411_0033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_dispatch_batches",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("parametros_id", sa.BigInteger(), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("source_phone", sa.String(length=30), nullable=True),
        sa.Column("schedule_snapshot", sa.JSON(), nullable=True),
        sa.Column("summary_json", sa.JSON(), nullable=True),
        sa.Column("total_items", sa.Integer(), nullable=False),
        sa.Column("total_sent", sa.Integer(), nullable=False),
        sa.Column("total_errors", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["parametros_id"], ["parametros.parametros_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_whatsapp_dispatch_batches_executed_at"), "whatsapp_dispatch_batches", ["executed_at"], unique=False)
    op.create_index(op.f("ix_whatsapp_dispatch_batches_id"), "whatsapp_dispatch_batches", ["id"], unique=False)
    op.create_index(op.f("ix_whatsapp_dispatch_batches_parametros_id"), "whatsapp_dispatch_batches", ["parametros_id"], unique=False)
    op.create_index(op.f("ix_whatsapp_dispatch_batches_scheduled_for"), "whatsapp_dispatch_batches", ["scheduled_for"], unique=False)

    op.create_table(
        "whatsapp_dispatch_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("batch_id", sa.BigInteger(), nullable=False),
        sa.Column("conta_receber_id", sa.BigInteger(), nullable=True),
        sa.Column("contratos_id", sa.BigInteger(), nullable=True),
        sa.Column("cliente_id", sa.Integer(), nullable=True),
        sa.Column("parcela_nro", sa.Integer(), nullable=True),
        sa.Column("client_name", sa.String(length=120), nullable=True),
        sa.Column("destination_phone", sa.String(length=30), nullable=True),
        sa.Column("source_phone", sa.String(length=30), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(precision=19, scale=4, asdecimal=False), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("message_payload", sa.JSON(), nullable=False),
        sa.Column("provider_payload", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["batch_id"], ["whatsapp_dispatch_batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.clientes_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["conta_receber_id"], ["contas_receber.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["contratos_id"], ["contratos.contratos_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_whatsapp_dispatch_items_batch_id"), "whatsapp_dispatch_items", ["batch_id"], unique=False)
    op.create_index(op.f("ix_whatsapp_dispatch_items_cliente_id"), "whatsapp_dispatch_items", ["cliente_id"], unique=False)
    op.create_index(op.f("ix_whatsapp_dispatch_items_conta_receber_id"), "whatsapp_dispatch_items", ["conta_receber_id"], unique=False)
    op.create_index(op.f("ix_whatsapp_dispatch_items_contratos_id"), "whatsapp_dispatch_items", ["contratos_id"], unique=False)
    op.create_index(op.f("ix_whatsapp_dispatch_items_id"), "whatsapp_dispatch_items", ["id"], unique=False)
    op.create_index(op.f("ix_whatsapp_dispatch_items_sent_at"), "whatsapp_dispatch_items", ["sent_at"], unique=False)
    op.create_index(op.f("ix_whatsapp_dispatch_items_status"), "whatsapp_dispatch_items", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_whatsapp_dispatch_items_status"), table_name="whatsapp_dispatch_items")
    op.drop_index(op.f("ix_whatsapp_dispatch_items_sent_at"), table_name="whatsapp_dispatch_items")
    op.drop_index(op.f("ix_whatsapp_dispatch_items_id"), table_name="whatsapp_dispatch_items")
    op.drop_index(op.f("ix_whatsapp_dispatch_items_contratos_id"), table_name="whatsapp_dispatch_items")
    op.drop_index(op.f("ix_whatsapp_dispatch_items_conta_receber_id"), table_name="whatsapp_dispatch_items")
    op.drop_index(op.f("ix_whatsapp_dispatch_items_cliente_id"), table_name="whatsapp_dispatch_items")
    op.drop_index(op.f("ix_whatsapp_dispatch_items_batch_id"), table_name="whatsapp_dispatch_items")
    op.drop_table("whatsapp_dispatch_items")

    op.drop_index(op.f("ix_whatsapp_dispatch_batches_scheduled_for"), table_name="whatsapp_dispatch_batches")
    op.drop_index(op.f("ix_whatsapp_dispatch_batches_parametros_id"), table_name="whatsapp_dispatch_batches")
    op.drop_index(op.f("ix_whatsapp_dispatch_batches_id"), table_name="whatsapp_dispatch_batches")
    op.drop_index(op.f("ix_whatsapp_dispatch_batches_executed_at"), table_name="whatsapp_dispatch_batches")
    op.drop_table("whatsapp_dispatch_batches")