"""add cleared_at to chat thread preferences

Revision ID: 20260405_0016
Revises: 20260405_0015
Create Date: 2026-04-05 10:35:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0016"
down_revision = "20260405_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("chat_thread_preferences", sa.Column("cleared_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("chat_thread_preferences", "cleared_at")