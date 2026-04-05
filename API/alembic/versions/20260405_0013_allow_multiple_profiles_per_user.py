"""allow multiple profiles per user

Revision ID: 20260405_0013
Revises: 20260404_0012
Create Date: 2026-04-05 00:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0013"
down_revision = "20260404_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuarios_perfis",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("perfil_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["perfil_id"], ["perfis.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "perfil_id", name="pk_usuarios_perfis"),
    )
    op.create_index(op.f("ix_usuarios_perfis_user_id"), "usuarios_perfis", ["user_id"], unique=False)
    op.create_index(op.f("ix_usuarios_perfis_perfil_id"), "usuarios_perfis", ["perfil_id"], unique=False)

    op.execute(
        """
        INSERT INTO usuarios_perfis (user_id, perfil_id)
        SELECT id, perfil_id
        FROM usuarios
        WHERE perfil_id IS NOT NULL
        """
    )

    op.drop_constraint("fk_usuarios_perfil_id_perfis", "usuarios", type_="foreignkey")
    op.drop_index(op.f("ix_usuarios_perfil_id"), table_name="usuarios")
    op.drop_column("usuarios", "perfil_id")


def downgrade() -> None:
    op.add_column("usuarios", sa.Column("perfil_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_usuarios_perfil_id"), "usuarios", ["perfil_id"], unique=False)
    op.create_foreign_key("fk_usuarios_perfil_id_perfis", "usuarios", "perfis", ["perfil_id"], ["id"], ondelete="SET NULL")

    op.execute(
        """
        UPDATE usuarios AS u
        SET perfil_id = source.perfil_id
        FROM (
            SELECT user_id, MIN(perfil_id) AS perfil_id
            FROM usuarios_perfis
            GROUP BY user_id
        ) AS source
        WHERE u.id = source.user_id
        """
    )

    op.drop_index(op.f("ix_usuarios_perfis_perfil_id"), table_name="usuarios_perfis")
    op.drop_index(op.f("ix_usuarios_perfis_user_id"), table_name="usuarios_perfis")
    op.drop_table("usuarios_perfis")