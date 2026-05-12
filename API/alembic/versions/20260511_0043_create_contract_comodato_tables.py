"""create contract comodato tables

Revision ID: 20260511_0043
Revises: 20260506_0042
Create Date: 2026-05-11 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260511_0043"
down_revision: str | Sequence[str] | None = "20260506_0042"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contratos_comodatos",
        sa.Column("comodato_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("contrato_id", sa.BigInteger(), nullable=False),
        sa.Column("avalista_cliente_id", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(["avalista_cliente_id"], ["clientes.clientes_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["contrato_id"], ["contratos.contratos_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("comodato_id"),
        sa.UniqueConstraint("contrato_id"),
    )
    op.create_index(op.f("ix_contratos_comodatos_comodato_id"), "contratos_comodatos", ["comodato_id"], unique=False)
    op.create_index(op.f("ix_contratos_comodatos_contrato_id"), "contratos_comodatos", ["contrato_id"], unique=False)
    op.create_index(op.f("ix_contratos_comodatos_avalista_cliente_id"), "contratos_comodatos", ["avalista_cliente_id"], unique=False)

    op.create_table(
        "contratos_comodato_itens",
        sa.Column("item_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("comodato_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("descricao_produto", sa.String(length=120), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column("valor_unitario", sa.Numeric(precision=19, scale=2, asdecimal=False), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["comodato_id"], ["contratos_comodatos.comodato_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.produto_id"]),
        sa.PrimaryKeyConstraint("item_id"),
    )
    op.create_index(op.f("ix_contratos_comodato_itens_item_id"), "contratos_comodato_itens", ["item_id"], unique=False)
    op.create_index(op.f("ix_contratos_comodato_itens_comodato_id"), "contratos_comodato_itens", ["comodato_id"], unique=False)
    op.create_index(op.f("ix_contratos_comodato_itens_produto_id"), "contratos_comodato_itens", ["produto_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_contratos_comodato_itens_produto_id"), table_name="contratos_comodato_itens")
    op.drop_index(op.f("ix_contratos_comodato_itens_comodato_id"), table_name="contratos_comodato_itens")
    op.drop_index(op.f("ix_contratos_comodato_itens_item_id"), table_name="contratos_comodato_itens")
    op.drop_table("contratos_comodato_itens")

    op.drop_index(op.f("ix_contratos_comodatos_avalista_cliente_id"), table_name="contratos_comodatos")
    op.drop_index(op.f("ix_contratos_comodatos_contrato_id"), table_name="contratos_comodatos")
    op.drop_index(op.f("ix_contratos_comodatos_comodato_id"), table_name="contratos_comodatos")
    op.drop_table("contratos_comodatos")
