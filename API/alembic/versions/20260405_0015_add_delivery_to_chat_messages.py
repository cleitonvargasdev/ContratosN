"""add delivery to chat messages

Revision ID: 20260405_0015
Revises: 20260405_0014
Create Date: 2026-04-05 03:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0015"
down_revision = "20260405_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("chat_messages", sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("chat_messages", "delivered_at")