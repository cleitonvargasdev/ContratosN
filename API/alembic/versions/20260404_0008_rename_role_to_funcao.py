"""rename role to funcao and remove role-based authorization

Revision ID: 20260404_0008
Revises: 20260404_0007
Create Date: 2026-04-04 18:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260404_0008"
down_revision = "20260404_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("usuarios", "role", new_column_name="funcao", existing_type=sa.String(length=20), existing_nullable=False)
    op.execute("UPDATE usuarios SET funcao = 'Administrador' WHERE funcao = 'admin'")
    op.execute("UPDATE usuarios SET funcao = 'Operador' WHERE funcao = 'usuario' OR funcao IS NULL")
    op.alter_column(
        "usuarios",
        "funcao",
        existing_type=sa.String(length=20),
        type_=sa.String(length=40),
        existing_nullable=False,
        server_default="Operador",
    )

    op.execute(
        """
        INSERT INTO perfil_permissoes (perfil_id, resource_key, resource_label, can_read, can_create, can_update, can_delete)
        SELECT p.id, v.resource_key, v.resource_label, v.can_read, v.can_create, v.can_update, v.can_delete
        FROM perfis p
        JOIN (
          VALUES
            ('dashboard', 'Dashboard', true, false, false, false),
            ('usuarios', 'Usuarios', true, true, true, true),
            ('usuarios_api_keys', 'Chaves de API dos usuarios', true, false, true, false),
            ('perfis', 'Perfis e permissoes', true, true, true, true),
            ('localidades_ufs', 'UFs', true, true, true, true),
            ('localidades_cidades', 'Cidades', true, true, true, true),
            ('localidades_bairros', 'Bairros', true, true, true, true)
        ) AS v(resource_key, resource_label, can_read, can_create, can_update, can_delete)
          ON true
        WHERE p.nome = 'Administrador'
          AND NOT EXISTS (
            SELECT 1
            FROM perfil_permissoes existing
            WHERE existing.perfil_id = p.id
              AND existing.resource_key = v.resource_key
          )
        """
    )

    op.execute(
        """
        UPDATE perfil_permissoes
        SET can_read = true,
            can_create = true,
            can_update = true,
            can_delete = true
        WHERE perfil_id = (SELECT id FROM perfis WHERE nome = 'Administrador')
        """
    )

    op.execute(
        """
        UPDATE usuarios
        SET perfil_id = (SELECT id FROM perfis WHERE nome = 'Administrador')
        WHERE funcao = 'Administrador' AND perfil_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE usuarios
        SET perfil_id = (SELECT id FROM perfis WHERE nome = 'Operacional')
        WHERE funcao <> 'Administrador' AND perfil_id IS NULL
        """
    )


def downgrade() -> None:
    op.execute("UPDATE usuarios SET funcao = 'admin' WHERE funcao = 'Administrador'")
    op.execute("UPDATE usuarios SET funcao = 'usuario' WHERE funcao <> 'admin' OR funcao IS NULL")
    op.alter_column(
        "usuarios",
        "funcao",
        existing_type=sa.String(length=40),
        type_=sa.String(length=20),
        existing_nullable=False,
        server_default="usuario",
    )
    op.alter_column("usuarios", "funcao", new_column_name="role", existing_type=sa.String(length=20), existing_nullable=False)