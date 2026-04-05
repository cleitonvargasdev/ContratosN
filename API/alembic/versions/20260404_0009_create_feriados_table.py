"""create feriados table

Revision ID: 20260404_0009
Revises: 20260404_0008
Create Date: 2026-04-04 20:15:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260404_0009"
down_revision = "20260404_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feriados",
        sa.Column("feriados_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.String(length=10), nullable=False),
        sa.Column("cidade_id", sa.BigInteger(), nullable=True),
        sa.Column("uf", sa.String(length=2), nullable=True),
        sa.Column("descricao", sa.String(length=50), nullable=False),
        sa.Column("nivel", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["cidade_id"], ["cidades.cidade_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["uf"], ["uf.uf"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("feriados_id"),
    )
    op.create_index(op.f("ix_feriados_feriados_id"), "feriados", ["feriados_id"], unique=False)
    op.create_index(op.f("ix_feriados_data"), "feriados", ["data"], unique=False)
    op.create_index(op.f("ix_feriados_cidade_id"), "feriados", ["cidade_id"], unique=False)
    op.create_index(op.f("ix_feriados_uf"), "feriados", ["uf"], unique=False)
    op.create_index(op.f("ix_feriados_descricao"), "feriados", ["descricao"], unique=False)
    op.create_index(op.f("ix_feriados_nivel"), "feriados", ["nivel"], unique=False)

    op.execute(
        """
        INSERT INTO perfil_permissoes (perfil_id, resource_key, resource_label, can_read, can_create, can_update, can_delete)
        SELECT p.id, 'localidades_feriados', 'Feriados', true, true, true, true
        FROM perfis p
        WHERE p.nome = 'Administrador'
          AND NOT EXISTS (
            SELECT 1 FROM perfil_permissoes existing
            WHERE existing.perfil_id = p.id AND existing.resource_key = 'localidades_feriados'
          )
        """
    )

    op.execute(
        """
        INSERT INTO perfil_permissoes (perfil_id, resource_key, resource_label, can_read, can_create, can_update, can_delete)
        SELECT p.id, 'localidades_feriados', 'Feriados', true, false, false, false
        FROM perfis p
        WHERE p.nome = 'Operacional'
          AND NOT EXISTS (
            SELECT 1 FROM perfil_permissoes existing
            WHERE existing.perfil_id = p.id AND existing.resource_key = 'localidades_feriados'
          )
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM perfil_permissoes WHERE resource_key = 'localidades_feriados'")
    op.drop_index(op.f("ix_feriados_nivel"), table_name="feriados")
    op.drop_index(op.f("ix_feriados_descricao"), table_name="feriados")
    op.drop_index(op.f("ix_feriados_uf"), table_name="feriados")
    op.drop_index(op.f("ix_feriados_cidade_id"), table_name="feriados")
    op.drop_index(op.f("ix_feriados_data"), table_name="feriados")
    op.drop_index(op.f("ix_feriados_feriados_id"), table_name="feriados")
    op.drop_table("feriados")
