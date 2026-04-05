"""create internal chat tables

Revision ID: 20260405_0014
Revises: 20260405_0013
Create Date: 2026-04-05 02:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_0014"
down_revision = "20260405_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_threads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_a_id", sa.Integer(), nullable=False),
        sa.Column("user_b_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_a_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_b_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_a_id", "user_b_id", name="uq_chat_threads_user_pair"),
    )
    op.create_index(op.f("ix_chat_threads_id"), "chat_threads", ["id"], unique=False)
    op.create_index(op.f("ix_chat_threads_user_a_id"), "chat_threads", ["user_a_id"], unique=False)
    op.create_index(op.f("ix_chat_threads_user_b_id"), "chat_threads", ["user_b_id"], unique=False)

    op.create_table(
        "chat_thread_preferences",
        sa.Column("thread_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("muted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["thread_id"], ["chat_threads.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("thread_id", "user_id"),
    )
    op.create_index(op.f("ix_chat_thread_preferences_user_id"), "chat_thread_preferences", ["user_id"], unique=False)

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("thread_id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("recipient_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["recipient_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["thread_id"], ["chat_threads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_messages_id"), "chat_messages", ["id"], unique=False)
    op.create_index(op.f("ix_chat_messages_thread_id"), "chat_messages", ["thread_id"], unique=False)
    op.create_index(op.f("ix_chat_messages_sender_id"), "chat_messages", ["sender_id"], unique=False)
    op.create_index(op.f("ix_chat_messages_recipient_id"), "chat_messages", ["recipient_id"], unique=False)
    op.create_index(op.f("ix_chat_messages_created_at"), "chat_messages", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_chat_messages_created_at"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_recipient_id"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_sender_id"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_thread_id"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_id"), table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index(op.f("ix_chat_thread_preferences_user_id"), table_name="chat_thread_preferences")
    op.drop_table("chat_thread_preferences")

    op.drop_index(op.f("ix_chat_threads_user_b_id"), table_name="chat_threads")
    op.drop_index(op.f("ix_chat_threads_user_a_id"), table_name="chat_threads")
    op.drop_index(op.f("ix_chat_threads_id"), table_name="chat_threads")
    op.drop_table("chat_threads")