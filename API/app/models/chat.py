from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class ChatThread(Base):
    __tablename__ = "chat_threads"
    __table_args__ = (UniqueConstraint("user_a_id", "user_b_id", name="uq_chat_threads_user_pair"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_a_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    user_b_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user_a: Mapped[User] = relationship("User", foreign_keys=[user_a_id], lazy="selectin")
    user_b: Mapped[User] = relationship("User", foreign_keys=[user_b_id], lazy="selectin")
    messages: Mapped[list[ChatMessage]] = relationship(
        "ChatMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ChatMessage.created_at",
    )
    preferences: Mapped[list[ChatThreadPreference]] = relationship(
        "ChatThreadPreference",
        back_populates="thread",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def peer_for(self, user_id: int) -> User:
        if self.user_a_id == user_id:
            return self.user_b
        return self.user_a

    def preference_for(self, user_id: int) -> ChatThreadPreference | None:
        return next((item for item in self.preferences if item.user_id == user_id), None)


class ChatThreadPreference(Base):
    __tablename__ = "chat_thread_preferences"

    thread_id: Mapped[int] = mapped_column(ForeignKey("chat_threads.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    muted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    thread: Mapped[ChatThread] = relationship("ChatThread", back_populates="preferences")
    user: Mapped[User] = relationship("User", lazy="selectin")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("chat_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    thread: Mapped[ChatThread] = relationship("ChatThread", back_populates="messages")
    sender: Mapped[User] = relationship("User", foreign_keys=[sender_id], lazy="selectin")
    recipient: Mapped[User] = relationship("User", foreign_keys=[recipient_id], lazy="selectin")