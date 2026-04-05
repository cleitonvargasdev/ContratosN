"""add login and password to usuarios

Revision ID: 20260401_0002
Revises: 20260401_0001
Create Date: 2026-04-01 00:30:00

"""

from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext


revision = "20260401_0002"
down_revision = "20260401_0001"
branch_labels = None
depends_on = None


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("login", sa.String(length=80), nullable=True))
    op.add_column("usuarios", sa.Column("senha_hash", sa.String(length=255), nullable=True))

    default_password_hash = pwd_context.hash("123456")
    op.execute("UPDATE usuarios SET login = split_part(email, '@', 1) WHERE login IS NULL")
    op.execute(sa.text("UPDATE usuarios SET senha_hash = :password_hash WHERE senha_hash IS NULL").bindparams(password_hash=default_password_hash))

    op.alter_column("usuarios", "login", nullable=False)
    op.alter_column("usuarios", "senha_hash", nullable=False)
    op.create_index(op.f("ix_usuarios_login"), "usuarios", ["login"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_usuarios_login"), table_name="usuarios")
    op.drop_column("usuarios", "senha_hash")
    op.drop_column("usuarios", "login")