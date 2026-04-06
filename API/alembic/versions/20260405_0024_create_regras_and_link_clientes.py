"""create regras tables and link clientes to regra_juros

Revision ID: 20260405_0024
Revises: 20260405_0023
Create Date: 2026-04-05 16:18:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0024"
down_revision = "20260405_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "regras_juros",
        sa.Column("regra_juros_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("descricao", sa.String(length=25), nullable=True),
        sa.Column("juros_dia", sa.Numeric(8, 2), nullable=True),
        sa.Column("mora_dia", sa.Numeric(8, 2), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("regra_juros_id"),
    )
    op.create_index(op.f("ix_regras_juros_regra_juros_id"), "regras_juros", ["regra_juros_id"], unique=False)
    op.create_index(op.f("ix_regras_juros_descricao"), "regras_juros", ["descricao"], unique=False)

    op.create_table(
        "regras_comissao",
        sa.Column("regra_comissao_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("descricao", sa.String(length=25), nullable=True),
        sa.Column("percentual_comissao", sa.Numeric(8, 2), nullable=True),
        sa.Column("com_quitacao", sa.Boolean(), nullable=True),
        sa.Column("a_partir_perc_total", sa.Numeric(8, 2), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("regra_comissao_id"),
    )
    op.create_index(op.f("ix_regras_comissao_regra_comissao_id"), "regras_comissao", ["regra_comissao_id"], unique=False)
    op.create_index(op.f("ix_regras_comissao_descricao"), "regras_comissao", ["descricao"], unique=False)

    op.add_column("clientes", sa.Column("regra_juros_id", sa.BigInteger(), nullable=True))
    op.create_index(op.f("ix_clientes_regra_juros_id"), "clientes", ["regra_juros_id"], unique=False)
    op.create_foreign_key(
        "fk_clientes_regra_juros_id",
        "clientes",
        "regras_juros",
        ["regra_juros_id"],
        ["regra_juros_id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_clientes_regra_juros_id", "clientes", type_="foreignkey")
    op.drop_index(op.f("ix_clientes_regra_juros_id"), table_name="clientes")
    op.drop_column("clientes", "regra_juros_id")

    op.drop_index(op.f("ix_regras_comissao_descricao"), table_name="regras_comissao")
    op.drop_index(op.f("ix_regras_comissao_regra_comissao_id"), table_name="regras_comissao")
    op.drop_table("regras_comissao")

    op.drop_index(op.f("ix_regras_juros_descricao"), table_name="regras_juros")
    op.drop_index(op.f("ix_regras_juros_regra_juros_id"), table_name="regras_juros")
    op.drop_table("regras_juros")