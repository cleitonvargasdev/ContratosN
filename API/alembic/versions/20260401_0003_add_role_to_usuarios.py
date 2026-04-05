"""add role to usuarios

Revision ID: 20260401_0003
Revises: 20260401_0002
Create Date: 2026-04-01 01:00:00

"""

from alembic import op
import sqlalchemy as sa


revision = "20260401_0003"
down_revision = "20260401_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("role", sa.String(length=20), nullable=True))
    op.execute("UPDATE usuarios SET role = 'usuario' WHERE role IS NULL")
    op.execute("UPDATE usuarios SET role = 'admin' WHERE login = 'ana.souza'")
    op.alter_column("usuarios", "role", nullable=False)


def downgrade() -> None:
    op.drop_column("usuarios", "role")