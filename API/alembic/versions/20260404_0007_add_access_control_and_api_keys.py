"""add access control and api keys

Revision ID: 20260404_0007
Revises: 20260404_0006
Create Date: 2026-04-04 14:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260404_0007"
down_revision = "20260404_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "perfis",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=80), nullable=False),
        sa.Column("descricao", sa.String(length=255), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_perfis_id"), "perfis", ["id"], unique=False)
    op.create_index(op.f("ix_perfis_nome"), "perfis", ["nome"], unique=True)

    op.create_table(
        "perfil_permissoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("perfil_id", sa.Integer(), nullable=False),
        sa.Column("resource_key", sa.String(length=120), nullable=False),
        sa.Column("resource_label", sa.String(length=160), nullable=True),
        sa.Column("can_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_create", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_update", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_delete", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["perfil_id"], ["perfis.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("perfil_id", "resource_key", name="uq_perfil_permissoes_recurso"),
    )
    op.create_index(op.f("ix_perfil_permissoes_id"), "perfil_permissoes", ["id"], unique=False)
    op.create_index(op.f("ix_perfil_permissoes_perfil_id"), "perfil_permissoes", ["perfil_id"], unique=False)
    op.create_index(op.f("ix_perfil_permissoes_resource_key"), "perfil_permissoes", ["resource_key"], unique=False)

    op.create_table(
        "usuarios_api_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("key_prefix", sa.String(length=24), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_usuarios_api_keys_id"), "usuarios_api_keys", ["id"], unique=False)
    op.create_index(op.f("ix_usuarios_api_keys_user_id"), "usuarios_api_keys", ["user_id"], unique=True)
    op.create_index(op.f("ix_usuarios_api_keys_key_prefix"), "usuarios_api_keys", ["key_prefix"], unique=False)
    op.create_index(op.f("ix_usuarios_api_keys_key_hash"), "usuarios_api_keys", ["key_hash"], unique=True)

    op.add_column("usuarios", sa.Column("perfil_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_usuarios_perfil_id"), "usuarios", ["perfil_id"], unique=False)
    op.create_foreign_key("fk_usuarios_perfil_id_perfis", "usuarios", "perfis", ["perfil_id"], ["id"], ondelete="SET NULL")

    op.execute(
        """
        INSERT INTO perfis (nome, descricao, ativo)
        VALUES
          ('Administrador', 'Perfil padrao com administracao total do sistema.', true),
          ('Operacional', 'Perfil padrao para usuarios com acesso operacional.', true)
        """
    )

    op.execute(
        """
        INSERT INTO perfil_permissoes (perfil_id, resource_key, resource_label, can_read, can_create, can_update, can_delete)
        SELECT p.id, v.resource_key, v.resource_label, v.can_read, v.can_create, v.can_update, v.can_delete
        FROM perfis p
        JOIN (
          VALUES
            ('dashboard', 'Dashboard', true, false, false, false),
            ('usuarios', 'Usuarios', true, false, false, false),
            ('localidades_ufs', 'UFs', true, false, false, false),
            ('localidades_cidades', 'Cidades', true, false, false, false),
            ('localidades_bairros', 'Bairros', true, false, false, false)
        ) AS v(resource_key, resource_label, can_read, can_create, can_update, can_delete)
          ON true
        WHERE p.nome = 'Operacional'
        """
    )

    op.execute(
        """
        UPDATE usuarios
        SET perfil_id = (SELECT id FROM perfis WHERE nome = 'Administrador')
        WHERE role = 'admin'
        """
    )
    op.execute(
        """
        UPDATE usuarios
        SET perfil_id = (SELECT id FROM perfis WHERE nome = 'Operacional')
        WHERE role <> 'admin' AND perfil_id IS NULL
        """
    )


def downgrade() -> None:
    op.drop_constraint("fk_usuarios_perfil_id_perfis", "usuarios", type_="foreignkey")
    op.drop_index(op.f("ix_usuarios_perfil_id"), table_name="usuarios")
    op.drop_column("usuarios", "perfil_id")

    op.drop_index(op.f("ix_usuarios_api_keys_key_hash"), table_name="usuarios_api_keys")
    op.drop_index(op.f("ix_usuarios_api_keys_key_prefix"), table_name="usuarios_api_keys")
    op.drop_index(op.f("ix_usuarios_api_keys_user_id"), table_name="usuarios_api_keys")
    op.drop_index(op.f("ix_usuarios_api_keys_id"), table_name="usuarios_api_keys")
    op.drop_table("usuarios_api_keys")

    op.drop_index(op.f("ix_perfil_permissoes_resource_key"), table_name="perfil_permissoes")
    op.drop_index(op.f("ix_perfil_permissoes_perfil_id"), table_name="perfil_permissoes")
    op.drop_index(op.f("ix_perfil_permissoes_id"), table_name="perfil_permissoes")
    op.drop_table("perfil_permissoes")

    op.drop_index(op.f("ix_perfis_nome"), table_name="perfis")
    op.drop_index(op.f("ix_perfis_id"), table_name="perfis")
    op.drop_table("perfis")
