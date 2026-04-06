"""create recebimentos table

Revision ID: 20260405_0022
Revises: 20260405_0021
Create Date: 2026-04-05 15:55:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0022"
down_revision = "20260405_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recebimentos",
        sa.Column("recebimento_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("contrato_id", sa.BigInteger(), nullable=True),
        sa.Column("valor_recebido", sa.Numeric(19, 4), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("data_recebimento", sa.DateTime(timezone=True), nullable=True),
        sa.Column("parcela_nro", sa.Integer(), nullable=True),
        sa.Column("latitude", sa.String(length=50), nullable=True),
        sa.Column("longitude", sa.String(length=50), nullable=True),
        sa.Column("desconto", sa.Numeric(19, 4), nullable=True),
        sa.Column("juros", sa.Numeric(19, 4), nullable=True),
        sa.Column("lote_id", sa.BigInteger(), nullable=True),
        sa.Column("item_lote_id", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["contrato_id"], ["contratos.contratos_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("recebimento_id"),
    )

    op.create_index(op.f("ix_recebimentos_recebimento_id"), "recebimentos", ["recebimento_id"], unique=False)
    op.create_index(op.f("ix_recebimentos_contrato_id"), "recebimentos", ["contrato_id"], unique=False)
    op.create_index(op.f("ix_recebimentos_usuario_id"), "recebimentos", ["usuario_id"], unique=False)
    op.create_index(op.f("ix_recebimentos_data_recebimento"), "recebimentos", ["data_recebimento"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_recebimentos_data_recebimento"), table_name="recebimentos")
    op.drop_index(op.f("ix_recebimentos_usuario_id"), table_name="recebimentos")
    op.drop_index(op.f("ix_recebimentos_contrato_id"), table_name="recebimentos")
    op.drop_index(op.f("ix_recebimentos_recebimento_id"), table_name="recebimentos")
    op.drop_table("recebimentos")