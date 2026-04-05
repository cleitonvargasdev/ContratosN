"""add acesso web permission

Revision ID: 20260404_0011
Revises: 20260404_0010
Create Date: 2026-04-04 22:05:00.000000
"""

from alembic import op


revision = "20260404_0011"
down_revision = "20260404_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO perfil_permissoes (perfil_id, resource_key, resource_label, can_read, can_create, can_update, can_delete)
        SELECT p.id, 'acesso_web', 'Acesso Web', true, false, false, false
        FROM perfis p
        WHERE NOT EXISTS (
            SELECT 1 FROM perfil_permissoes existing
            WHERE existing.perfil_id = p.id AND existing.resource_key = 'acesso_web'
        )
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM perfil_permissoes WHERE resource_key = 'acesso_web'")