"""create parametros table

Revision ID: 20260405_0018
Revises: 20260405_0017
Create Date: 2026-04-05 15:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0018"
down_revision = "20260405_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parametros",
        sa.Column("parametros_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("nome_fantasia", sa.String(length=150), nullable=True),
        sa.Column("razao_social", sa.String(length=150), nullable=True),
        sa.Column("endereco", sa.String(length=70), nullable=True),
        sa.Column("bairrosid", sa.Integer(), nullable=True),
        sa.Column("cep", sa.String(length=9), nullable=True),
        sa.Column("nro", sa.Integer(), nullable=True),
        sa.Column("cnpj", sa.String(length=18), nullable=True),
        sa.Column("uf", sa.String(length=2), nullable=True),
        sa.Column("cidade_id", sa.Integer(), nullable=True),
        sa.Column("telefone1", sa.String(length=17), nullable=True),
        sa.Column("telefone2", sa.String(length=17), nullable=True),
        sa.Column("e_mail", sa.String(length=200), nullable=True),
        sa.Column("responsavel", sa.String(length=120), nullable=True),
        sa.Column("complemento", sa.String(length=50), nullable=True),
        sa.Column("cpf", sa.String(length=14), nullable=True),
        sa.Column("rg", sa.String(length=25), nullable=True),
        sa.Column("cidade_id_responsavel", sa.Integer(), nullable=True),
        sa.Column("bairro_id_responsavel", sa.Integer(), nullable=True),
        sa.Column("uf_responsavel", sa.String(length=2), nullable=True),
        sa.Column("estado_civil", sa.String(length=30), nullable=True),
        sa.Column("nacionalidade", sa.String(length=40), nullable=True),
        sa.Column("endereco_responsavel", sa.String(length=80), nullable=True),
        sa.ForeignKeyConstraint(["bairro_id_responsavel"], ["bairros.bairro_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["bairrosid"], ["bairros.bairro_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cidade_id"], ["cidades.cidade_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cidade_id_responsavel"], ["cidades.cidade_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["uf"], ["uf.uf"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["uf_responsavel"], ["uf.uf"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("parametros_id"),
    )

    op.create_index(op.f("ix_parametros_parametros_id"), "parametros", ["parametros_id"], unique=False)
    op.create_index(op.f("ix_parametros_nome_fantasia"), "parametros", ["nome_fantasia"], unique=False)
    op.create_index(op.f("ix_parametros_razao_social"), "parametros", ["razao_social"], unique=False)
    op.create_index(op.f("ix_parametros_bairrosid"), "parametros", ["bairrosid"], unique=False)
    op.create_index(op.f("ix_parametros_cnpj"), "parametros", ["cnpj"], unique=False)
    op.create_index(op.f("ix_parametros_uf"), "parametros", ["uf"], unique=False)
    op.create_index(op.f("ix_parametros_cidade_id"), "parametros", ["cidade_id"], unique=False)
    op.create_index(op.f("ix_parametros_e_mail"), "parametros", ["e_mail"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_parametros_e_mail"), table_name="parametros")
    op.drop_index(op.f("ix_parametros_cidade_id"), table_name="parametros")
    op.drop_index(op.f("ix_parametros_uf"), table_name="parametros")
    op.drop_index(op.f("ix_parametros_cnpj"), table_name="parametros")
    op.drop_index(op.f("ix_parametros_bairrosid"), table_name="parametros")
    op.drop_index(op.f("ix_parametros_razao_social"), table_name="parametros")
    op.drop_index(op.f("ix_parametros_nome_fantasia"), table_name="parametros")
    op.drop_index(op.f("ix_parametros_parametros_id"), table_name="parametros")
    op.drop_table("parametros")