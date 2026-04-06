"""create clientes table

Revision ID: 20260405_0017
Revises: 20260405_0016
Create Date: 2026-04-05 15:05:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0017"
down_revision = "20260405_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clientes",
        sa.Column("clientes_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(length=70), nullable=True),
        sa.Column("rg", sa.Numeric(19, 0), nullable=True),
        sa.Column("cpf_cnpj", sa.String(length=18), nullable=True),
        sa.Column("endereco", sa.String(length=70), nullable=True),
        sa.Column("bairro_id", sa.Integer(), nullable=True),
        sa.Column("cidade_id", sa.BigInteger(), nullable=True),
        sa.Column("uf", sa.String(length=2), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("cnpj", sa.String(length=18), nullable=True),
        sa.Column("telefone", sa.String(length=15), nullable=True),
        sa.Column("celular01", sa.String(length=15), nullable=True),
        sa.Column("celular02", sa.String(length=15), nullable=True),
        sa.Column("flag_whatsapp", sa.Boolean(), nullable=True),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("limite_credito", sa.Numeric(24, 6), nullable=True),
        sa.Column("debito_atual", sa.Numeric(24, 6), nullable=True),
        sa.Column("prox_vencto", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_ultcompra", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rg_ie", sa.String(length=20), nullable=True),
        sa.Column("latitude", sa.String(length=50), nullable=True),
        sa.Column("longitude", sa.String(length=50), nullable=True),
        sa.Column("cep", sa.String(length=9), nullable=True),
        sa.Column("nro", sa.String(length=6), nullable=True),
        sa.Column("complemento", sa.String(length=50), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=True),
        sa.Column("bloqueado", sa.Boolean(), nullable=True),
        sa.Column("comissao_diferente", sa.Boolean(), nullable=True),
        sa.Column("percent_comissao", sa.Numeric(19, 4), nullable=True),
        sa.Column("naopagarcomissao", sa.Boolean(), nullable=True),
        sa.Column("desativado", sa.Boolean(), nullable=True),
        sa.Column("data_desat", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contato_responsavel", sa.String(length=50), nullable=True),
        sa.Column("endereco_responsavel", sa.String(length=100), nullable=True),
        sa.Column("fone_responsavel", sa.String(length=15), nullable=True),
        sa.Column("cel_responsavel", sa.String(length=15), nullable=True),
        sa.Column("flag_whatsapp_responsavel", sa.Boolean(), nullable=True),
        sa.Column("complemento_responsavel", sa.String(length=50), nullable=True),
        sa.Column("uf_referencia", sa.String(length=2), nullable=True),
        sa.Column("cidade_ref_id", sa.BigInteger(), nullable=True),
        sa.Column("bairro_id_responsavel", sa.Integer(), nullable=True),
        sa.Column("nro_responsavel", sa.String(length=6), nullable=True),
        sa.Column("uf_responsavel", sa.String(length=2), nullable=True),
        sa.Column("cidade_responsavel_id", sa.BigInteger(), nullable=True),
        sa.Column("nacionalidade", sa.String(length=40), nullable=True),
        sa.Column("estado_civil", sa.String(length=30), nullable=True),
        sa.Column("profissao", sa.String(length=30), nullable=True),
        sa.Column("mais_atrasada", sa.String(length=10), nullable=True),
        sa.Column("parc_atrasadas", sa.Integer(), nullable=True),
        sa.Column("valor_atrasado", sa.Numeric(19, 4), nullable=True),
        sa.Column("parc_aberto", sa.Integer(), nullable=True),
        sa.Column("turno_cobranca", sa.String(length=15), nullable=True),
        sa.Column("user_add", sa.Integer(), nullable=True),
        sa.Column("data_add", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("media_atraso_parcelas", sa.Numeric(12, 6), nullable=True),
        sa.Column("media_atraso_contratos", sa.Numeric(12, 6), nullable=True),
        sa.ForeignKeyConstraint(["bairro_id"], ["bairros.bairro_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["bairro_id_responsavel"], ["bairros.bairro_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cidade_id"], ["cidades.cidade_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cidade_ref_id"], ["cidades.cidade_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cidade_responsavel_id"], ["cidades.cidade_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["uf"], ["uf.uf"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["uf_referencia"], ["uf.uf"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["uf_responsavel"], ["uf.uf"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_add"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("clientes_id"),
    )

    op.create_index(op.f("ix_clientes_clientes_id"), "clientes", ["clientes_id"], unique=False)
    op.create_index(op.f("ix_clientes_nome"), "clientes", ["nome"], unique=False)
    op.create_index(op.f("ix_clientes_cpf_cnpj"), "clientes", ["cpf_cnpj"], unique=False)
    op.create_index(op.f("ix_clientes_email"), "clientes", ["email"], unique=False)
    op.create_index(op.f("ix_clientes_bairro_id"), "clientes", ["bairro_id"], unique=False)
    op.create_index(op.f("ix_clientes_cidade_id"), "clientes", ["cidade_id"], unique=False)
    op.create_index(op.f("ix_clientes_uf"), "clientes", ["uf"], unique=False)
    op.create_index(op.f("ix_clientes_usuario_id"), "clientes", ["usuario_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_clientes_usuario_id"), table_name="clientes")
    op.drop_index(op.f("ix_clientes_uf"), table_name="clientes")
    op.drop_index(op.f("ix_clientes_cidade_id"), table_name="clientes")
    op.drop_index(op.f("ix_clientes_bairro_id"), table_name="clientes")
    op.drop_index(op.f("ix_clientes_email"), table_name="clientes")
    op.drop_index(op.f("ix_clientes_cpf_cnpj"), table_name="clientes")
    op.drop_index(op.f("ix_clientes_nome"), table_name="clientes")
    op.drop_index(op.f("ix_clientes_clientes_id"), table_name="clientes")
    op.drop_table("clientes")