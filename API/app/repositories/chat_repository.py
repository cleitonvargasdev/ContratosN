from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatMessage, ChatThread, ChatThreadPreference
from app.models.user import User


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _thread_load_options() -> tuple:
        return (
            selectinload(ChatThread.user_a),
            selectinload(ChatThread.user_b),
            selectinload(ChatThread.preferences),
        )

    async def list_threads_for_user(self, user_id: int) -> Sequence[ChatThread]:
        stmt = (
            select(ChatThread)
            .options(*self._thread_load_options())
            .where(or_(ChatThread.user_a_id == user_id, ChatThread.user_b_id == user_id))
            .order_by(ChatThread.updated_at.desc(), ChatThread.id.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_thread_between_users(self, user_a_id: int, user_b_id: int) -> ChatThread | None:
        stmt = (
            select(ChatThread)
            .options(*self._thread_load_options())
            .where(ChatThread.user_a_id == user_a_id, ChatThread.user_b_id == user_b_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_thread(self, thread: ChatThread) -> ChatThread:
        self.session.add(thread)
        await self.session.commit()
        await self.session.refresh(thread)
        return await self.get_thread_by_id(thread.id) or thread

    async def get_thread_by_id(self, thread_id: int) -> ChatThread | None:
        stmt = select(ChatThread).options(*self._thread_load_options()).where(ChatThread.id == thread_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_thread(self, thread: ChatThread) -> ChatThread:
        await self.session.commit()
        await self.session.refresh(thread)
        return await self.get_thread_by_id(thread.id) or thread

    async def list_messages(self, thread_id: int, limit: int = 100, visible_after: datetime | None = None) -> Sequence[ChatMessage]:
        stmt = select(ChatMessage).where(ChatMessage.thread_id == thread_id)
        if visible_after is not None:
            stmt = stmt.where(ChatMessage.created_at > visible_after)
        stmt = stmt.order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(reversed(result.scalars().all()))

    async def get_message_by_id(self, message_id: int) -> ChatMessage | None:
        stmt = select(ChatMessage).where(ChatMessage.id == message_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_message(self, thread: ChatThread, message: ChatMessage) -> ChatMessage:
        thread.updated_at = datetime.now(timezone.utc)
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def save_message(self, message: ChatMessage) -> ChatMessage:
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def delete_message(self, message: ChatMessage) -> None:
        await self.session.delete(message)
        await self.session.commit()

    async def clear_thread_for_user(self, thread: ChatThread, user_id: int) -> ChatThread:
        preference = thread.preference_for(user_id)
        if preference is None:
            preference = ChatThreadPreference(thread_id=thread.id, user_id=user_id, muted=False)
            thread.preferences.append(preference)

        preference.cleared_at = datetime.now(timezone.utc)
        await self.session.commit()
        return await self.get_thread_by_id(thread.id) or thread

    async def get_last_messages(
        self,
        thread_ids: list[int],
        visible_after_by_thread: dict[int, datetime | None] | None = None,
    ) -> dict[int, ChatMessage]:
        if not thread_ids:
            return {}

        stmt = (
            select(ChatMessage)
            .where(ChatMessage.thread_id.in_(thread_ids))
            .order_by(ChatMessage.thread_id.asc(), ChatMessage.created_at.desc(), ChatMessage.id.desc())
        )
        result = await self.session.execute(stmt)

        messages_by_thread: dict[int, ChatMessage] = {}
        for message in result.scalars().all():
            visible_after = (visible_after_by_thread or {}).get(message.thread_id)
            if visible_after is not None and message.created_at <= visible_after:
                continue
            messages_by_thread.setdefault(message.thread_id, message)
        return messages_by_thread

    async def get_unread_counts(
        self,
        thread_ids: list[int],
        user_id: int,
        visible_after_by_thread: dict[int, datetime | None] | None = None,
    ) -> dict[int, int]:
        if not thread_ids:
            return {}

        stmt = (
            select(ChatMessage.thread_id, func.count(ChatMessage.id))
            .where(
                ChatMessage.thread_id.in_(thread_ids),
                ChatMessage.recipient_id == user_id,
                ChatMessage.read_at.is_(None),
            )
            .group_by(ChatMessage.thread_id)
        )
        result = await self.session.execute(stmt)

        counts: dict[int, int] = {}
        for thread_id, total in result.all():
            visible_after = (visible_after_by_thread or {}).get(thread_id)
            if visible_after is None:
                counts[thread_id] = int(total)
                continue

            visible_stmt = (
                select(func.count(ChatMessage.id))
                .where(
                    ChatMessage.thread_id == thread_id,
                    ChatMessage.recipient_id == user_id,
                    ChatMessage.read_at.is_(None),
                    ChatMessage.created_at > visible_after,
                )
            )
            visible_result = await self.session.execute(visible_stmt)
            counts[thread_id] = int(visible_result.scalar_one() or 0)

        return counts

    async def mark_messages_as_read(self, thread_id: int, recipient_id: int, visible_after: datetime | None = None) -> bool:
        stmt = update(ChatMessage).where(
            ChatMessage.thread_id == thread_id,
            ChatMessage.recipient_id == recipient_id,
            ChatMessage.read_at.is_(None),
        )
        if visible_after is not None:
            stmt = stmt.where(ChatMessage.created_at > visible_after)
        stmt = stmt.values(read_at=datetime.now(timezone.utc))
        result = await self.session.execute(stmt)
        await self.session.commit()
        return bool(result.rowcount)

    async def mark_messages_as_delivered(self, thread_id: int, recipient_id: int, visible_after: datetime | None = None) -> bool:
        stmt = update(ChatMessage).where(
            ChatMessage.thread_id == thread_id,
            ChatMessage.recipient_id == recipient_id,
            ChatMessage.delivered_at.is_(None),
        )
        if visible_after is not None:
            stmt = stmt.where(ChatMessage.created_at > visible_after)
        stmt = stmt.values(delivered_at=datetime.now(timezone.utc))
        result = await self.session.execute(stmt)
        await self.session.commit()
        return bool(result.rowcount)

    async def list_active_contacts(self, current_user_id: int, term: str | None = None) -> Sequence[User]:
        stmt = (
            select(User)
            .where(User.id != current_user_id, User.ativo.is_(True))
            .order_by(User.nome.asc(), User.id.asc())
        )
        if term:
            stmt = stmt.where(or_(User.nome.ilike(f"%{term}%"), User.login.ilike(f"%{term}%")))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_active_user_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id, User.ativo.is_(True))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_thread_preference(self, thread_id: int, user_id: int) -> ChatThreadPreference | None:
        stmt = select(ChatThreadPreference).where(ChatThreadPreference.thread_id == thread_id, ChatThreadPreference.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()