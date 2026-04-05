"""create localidades tables

Revision ID: 20260404_0004
Revises: 20260401_0003
Create Date: 2026-04-04 00:00:00

"""

from alembic import op
import sqlalchemy as sa


revision = "20260404_0004"
down_revision = "20260401_0003"
branch_labels = None
depends_on = None


uf_table = sa.table(
    "uf",
    sa.column("uf_id", sa.Integer()),
    sa.column("uf", sa.String(length=2)),
    sa.column("uf_nome", sa.String(length=80)),
    sa.column("cod_ibge", sa.Integer()),
)

cidades_table = sa.table(
    "cidades",
    sa.column("cidade_id", sa.BigInteger()),
    sa.column("uf_id", sa.Integer()),
    sa.column("cidade", sa.String(length=75)),
)


def upgrade() -> None:
    op.create_table(
        "uf",
        sa.Column("uf_id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("uf", sa.String(length=2), nullable=False),
        sa.Column("uf_nome", sa.String(length=80), nullable=False),
        sa.Column("cod_ibge", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("uf_id", name="pk_uf"),
        sa.UniqueConstraint("uf", name="uq_uf_uf"),
    )
    op.create_index("ix_uf_uf_nome", "uf", ["uf_nome"], unique=False)

    op.create_table(
        "cidades",
        sa.Column("cidade_id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("uf_id", sa.Integer(), nullable=False),
        sa.Column("cidade", sa.String(length=75), nullable=False),
        sa.ForeignKeyConstraint(["uf_id"], ["uf.uf_id"], name="fk_cidades_uf_id", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("cidade_id", name="pk_cidades"),
        sa.UniqueConstraint("uf_id", "cidade", name="uq_cidades_uf_id_cidade"),
    )
    op.create_index("ix_cidades_cidade", "cidades", ["cidade"], unique=False)
    op.create_index("ix_cidades_uf_id", "cidades", ["uf_id"], unique=False)

    op.create_table(
        "bairro",
        sa.Column("bairro_id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("bairro_nome", sa.String(length=80), nullable=False),
        sa.Column("cidade_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["cidade_id"], ["cidades.cidade_id"], name="fk_bairro_cidade_id", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("bairro_id", name="pk_bairro"),
        sa.UniqueConstraint("cidade_id", "bairro_nome", name="uq_bairro_cidade_id_bairro_nome"),
    )
    op.create_index("ix_bairro_bairro_nome", "bairro", ["bairro_nome"], unique=False)
    op.create_index("ix_bairro_cidade_id", "bairro", ["cidade_id"], unique=False)

    op.bulk_insert(
        uf_table,
        [
            {"uf_id": 1, "uf": "MS", "uf_nome": "Mato Grosso do Sul", "cod_ibge": 50},
            {"uf_id": 2, "uf": "MT", "uf_nome": "Mato Grosso", "cod_ibge": 51},
        ],
    )

    op.bulk_insert(
        cidades_table,
        [
            {"cidade_id": 1, "uf_id": 1, "cidade": "Campo Grande"},
            {"cidade_id": 2, "uf_id": 2, "cidade": "Cuiaba"},
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_bairro_cidade_id", table_name="bairro")
    op.drop_index("ix_bairro_bairro_nome", table_name="bairro")
    op.drop_table("bairro")

    op.drop_index("ix_cidades_uf_id", table_name="cidades")
    op.drop_index("ix_cidades_cidade", table_name="cidades")
    op.drop_table("cidades")

    op.drop_index("ix_uf_uf_nome", table_name="uf")
    op.drop_table("uf")