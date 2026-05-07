"""create produtos and marcas tables

Revision ID: 20260506_0041
Revises: 20260418_0040
Create Date: 2026-05-06 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260506_0041"
down_revision = "20260418_0040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "marcas",
        sa.Column("marca_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("descricao", sa.String(length=30), nullable=False),
        sa.PrimaryKeyConstraint("marca_id"),
        sa.UniqueConstraint("descricao", name="uq_marcas_descricao"),
    )
    op.create_index(op.f("ix_marcas_marca_id"), "marcas", ["marca_id"], unique=False)
    op.create_index(op.f("ix_marcas_descricao"), "marcas", ["descricao"], unique=False)

    op.create_table(
        "produtos",
        sa.Column("produto_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("descricao", sa.String(length=60), nullable=False),
        sa.Column("valor_compra", sa.Float(), nullable=True),
        sa.Column("valor_venda", sa.Float(), nullable=True),
        sa.Column("marca_id", sa.Integer(), nullable=True),
        sa.Column("garantia", sa.Integer(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("estoque", sa.Integer(), nullable=True),
        sa.Column("modelo", sa.String(length=20), nullable=True),
        sa.Column("cor", sa.String(length=15), nullable=True),
        sa.ForeignKeyConstraint(["marca_id"], ["marcas.marca_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("produto_id"),
    )
    op.create_index(op.f("ix_produtos_produto_id"), "produtos", ["produto_id"], unique=False)
    op.create_index(op.f("ix_produtos_descricao"), "produtos", ["descricao"], unique=False)
    op.create_index(op.f("ix_produtos_marca_id"), "produtos", ["marca_id"], unique=False)

    op.execute(
        """
        INSERT INTO perfil_permissoes (perfil_id, resource_key, resource_label, can_read, can_create, can_update, can_delete)
        SELECT p.id, v.resource_key, v.resource_label, v.can_read, v.can_create, v.can_update, v.can_delete
        FROM perfis p
        JOIN (
            VALUES
                ('marcas', 'Marcas', true, true, true, true),
                ('produtos', 'Produtos', true, true, true, true)
        ) AS v(resource_key, resource_label, can_read, can_create, can_update, can_delete)
            ON true
        WHERE p.nome = 'Administrador'
            AND NOT EXISTS (
                SELECT 1
                FROM perfil_permissoes pp
                WHERE pp.perfil_id = p.id
                    AND pp.resource_key = v.resource_key
            )
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM perfil_permissoes WHERE resource_key IN ('marcas', 'produtos')")

    op.drop_index(op.f("ix_produtos_marca_id"), table_name="produtos")
    op.drop_index(op.f("ix_produtos_descricao"), table_name="produtos")
    op.drop_index(op.f("ix_produtos_produto_id"), table_name="produtos")
    op.drop_table("produtos")

    op.drop_index(op.f("ix_marcas_descricao"), table_name="marcas")
    op.drop_index(op.f("ix_marcas_marca_id"), table_name="marcas")
    op.drop_table("marcas")