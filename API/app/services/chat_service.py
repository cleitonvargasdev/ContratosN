from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage, ChatThread, ChatThreadPreference
from app.models.user import User
from app.repositories.chat_repository import ChatRepository
from app.realtime.chat_events import chat_event_broker
from app.schemas.chat import (
    ChatConversationRead,
    ChatEventPayload,
    ChatMessageCreate,
    ChatMessageDeleteResponse,
    ChatMessageRead,
    ChatMuteUpdate,
    ChatSendMessageResponse,
    ChatUserSummaryRead,
)


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = ChatRepository(session)

    async def list_contacts(self, current_user: User, term: str | None = None) -> list[ChatUserSummaryRead]:
        contacts = await self.repository.list_active_contacts(current_user.id, term)
        return [self._build_user_summary(contact) for contact in contacts]

    async def list_conversations(self, current_user: User) -> list[ChatConversationRead]:
        threads = list(await self.repository.list_threads_for_user(current_user.id))
        thread_ids = [thread.id for thread in threads]
        visible_after_by_thread = self._visible_after_by_thread(threads, current_user.id)
        last_messages = await self.repository.get_last_messages(thread_ids, visible_after_by_thread)
        unread_counts = await self.repository.get_unread_counts(thread_ids, current_user.id, visible_after_by_thread)

        return [
            self._build_conversation(
                thread=thread,
                current_user_id=current_user.id,
                last_message=last_messages.get(thread.id),
                unread_count=unread_counts.get(thread.id, 0),
            )
            for thread in threads
        ]

    async def list_messages(self, current_user: User, peer_user_id: int, limit: int = 100) -> list[ChatMessageRead]:
        peer = await self._get_peer_or_404(current_user.id, peer_user_id)
        thread = await self._get_thread_between(current_user.id, peer.id)
        if thread is None:
            return []

        visible_after = self._visible_after(thread, current_user.id)
        delivered = await self.repository.mark_messages_as_delivered(thread.id, current_user.id, visible_after)
        if delivered:
            refreshed_thread = await self.repository.get_thread_by_id(thread.id)
            if refreshed_thread is not None:
                peer_conversation = await self._build_conversation_for_user(refreshed_thread, peer.id)
                await chat_event_broker.send_to_user(
                    peer.id,
                    ChatEventPayload(event="delivered", conversation=peer_conversation).model_dump(mode="json"),
                )
        messages = await self.repository.list_messages(thread.id, limit=limit, visible_after=visible_after)
        return [ChatMessageRead.model_validate(message) for message in messages]

    async def send_message(self, current_user: User, peer_user_id: int, payload: ChatMessageCreate) -> ChatSendMessageResponse:
        peer = await self._get_peer_or_404(current_user.id, peer_user_id)
        thread = await self._get_or_create_thread(current_user.id, peer.id)

        message = ChatMessage(thread_id=thread.id, sender_id=current_user.id, recipient_id=peer.id, content=payload.content)
        saved_message = await self.repository.create_message(thread, message)
        refreshed_thread = await self.repository.get_thread_by_id(thread.id)
        if refreshed_thread is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao atualizar a conversa")

        sender_conversation = await self._build_conversation_for_user(refreshed_thread, current_user.id)
        recipient_conversation = await self._build_conversation_for_user(refreshed_thread, peer.id)
        message_read = ChatMessageRead.model_validate(saved_message)

        recipient_delivered = await chat_event_broker.send_to_user(
            peer.id,
            ChatEventPayload(event="message", conversation=recipient_conversation, message=message_read).model_dump(mode="json"),
        )

        if recipient_delivered and saved_message.delivered_at is None:
            from datetime import datetime, timezone
            saved_message.delivered_at = datetime.now(timezone.utc)
            saved_message = await self.repository.save_message(saved_message)
            message_read = ChatMessageRead.model_validate(saved_message)
            sender_conversation = await self._build_conversation_for_user(refreshed_thread, current_user.id)
            recipient_conversation = await self._build_conversation_for_user(refreshed_thread, peer.id)

        await chat_event_broker.send_to_user(
            current_user.id,
            ChatEventPayload(event="message", conversation=sender_conversation, message=message_read).model_dump(mode="json"),
        )

        return ChatSendMessageResponse(conversation=sender_conversation, message=message_read)

    async def set_muted(self, current_user: User, peer_user_id: int, payload: ChatMuteUpdate) -> ChatConversationRead:
        peer = await self._get_peer_or_404(current_user.id, peer_user_id)
        thread = await self._get_or_create_thread(current_user.id, peer.id)

        preference = thread.preference_for(current_user.id)
        if preference is None:
            preference = ChatThreadPreference(thread_id=thread.id, user_id=current_user.id, muted=payload.muted)
            thread.preferences.append(preference)
        else:
            preference.muted = payload.muted

        saved_thread = await self.repository.save_thread(thread)
        return await self._build_conversation_for_user(saved_thread, current_user.id)

    async def mark_conversation_as_read(self, current_user: User, peer_user_id: int) -> ChatConversationRead | None:
        peer = await self._get_peer_or_404(current_user.id, peer_user_id)
        thread = await self._get_thread_between(current_user.id, peer.id)
        if thread is None:
            return None

        visible_after = self._visible_after(thread, current_user.id)
        await self.repository.mark_messages_as_delivered(thread.id, current_user.id, visible_after)
        changed = await self.repository.mark_messages_as_read(thread.id, current_user.id, visible_after)
        refreshed_thread = await self.repository.get_thread_by_id(thread.id)
        if refreshed_thread is None:
            return None

        current_conversation = await self._build_conversation_for_user(refreshed_thread, current_user.id)
        peer_conversation = await self._build_conversation_for_user(refreshed_thread, peer.id)
        if changed:
            await chat_event_broker.send_to_user(
                current_user.id,
                ChatEventPayload(event="read", conversation=current_conversation).model_dump(mode="json"),
            )
            await chat_event_broker.send_to_user(
                peer.id,
                ChatEventPayload(event="read", conversation=peer_conversation).model_dump(mode="json"),
            )
        return current_conversation

    async def delete_message(self, current_user: User, peer_user_id: int, message_id: int) -> ChatMessageDeleteResponse:
        peer = await self._get_peer_or_404(current_user.id, peer_user_id)
        thread = await self._get_thread_between(current_user.id, peer.id)
        if thread is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversa nao encontrada")

        message = await self.repository.get_message_by_id(message_id)
        if message is None or message.thread_id != thread.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensagem nao encontrada")
        if message.sender_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o remetente pode apagar a mensagem")

        await self.repository.delete_message(message)
        refreshed_thread = await self.repository.get_thread_by_id(thread.id)
        if refreshed_thread is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Falha ao atualizar a conversa")

        sender_conversation = await self._build_conversation_for_user(refreshed_thread, current_user.id)
        recipient_conversation = await self._build_conversation_for_user(refreshed_thread, peer.id)

        await chat_event_broker.send_to_user(
            current_user.id,
            ChatEventPayload(event="deleted", conversation=sender_conversation, deleted_message_id=message_id).model_dump(mode="json"),
        )
        await chat_event_broker.send_to_user(
            peer.id,
            ChatEventPayload(event="deleted", conversation=recipient_conversation, deleted_message_id=message_id).model_dump(mode="json"),
        )

        return ChatMessageDeleteResponse(conversation=sender_conversation, deleted_message_id=message_id)

    async def clear_conversation(self, current_user: User, peer_user_id: int) -> ChatConversationRead:
        peer = await self._get_peer_or_404(current_user.id, peer_user_id)
        thread = await self._get_thread_between(current_user.id, peer.id)
        if thread is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversa nao encontrada")

        refreshed_thread = await self.repository.clear_thread_for_user(thread, current_user.id)
        sender_conversation = await self._build_conversation_for_user(refreshed_thread, current_user.id)
        await chat_event_broker.send_to_user(
            current_user.id,
            ChatEventPayload(event="cleared", conversation=sender_conversation).model_dump(mode="json"),
        )
        return sender_conversation

    async def _get_peer_or_404(self, current_user_id: int, peer_user_id: int) -> User:
        if current_user_id == peer_user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nao e permitido conversar com o proprio usuario")

        peer = await self.repository.get_active_user_by_id(peer_user_id)
        if peer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario de destino nao encontrado")
        return peer

    async def _get_or_create_thread(self, current_user_id: int, peer_user_id: int) -> ChatThread:
        user_a_id, user_b_id = sorted((current_user_id, peer_user_id))
        thread = await self.repository.get_thread_between_users(user_a_id, user_b_id)
        if thread is not None:
            return thread

        thread = ChatThread(user_a_id=user_a_id, user_b_id=user_b_id)
        thread.preferences = [
            ChatThreadPreference(user_id=user_a_id, muted=False),
            ChatThreadPreference(user_id=user_b_id, muted=False),
        ]
        return await self.repository.create_thread(thread)

    async def _get_thread_between(self, current_user_id: int, peer_user_id: int) -> ChatThread | None:
        user_a_id, user_b_id = sorted((current_user_id, peer_user_id))
        return await self.repository.get_thread_between_users(user_a_id, user_b_id)

    async def _build_conversation_for_user(self, thread: ChatThread, user_id: int) -> ChatConversationRead:
        visible_after_by_thread = self._visible_after_by_thread([thread], user_id)
        last_messages = await self.repository.get_last_messages([thread.id], visible_after_by_thread)
        unread_counts = await self.repository.get_unread_counts([thread.id], user_id, visible_after_by_thread)
        return self._build_conversation(thread, user_id, last_messages.get(thread.id), unread_counts.get(thread.id, 0))

    @staticmethod
    def _visible_after(thread: ChatThread, user_id: int):
        preference = thread.preference_for(user_id)
        return preference.cleared_at if preference is not None else None

    @staticmethod
    def _visible_after_by_thread(threads: list[ChatThread], user_id: int) -> dict[int, object]:
        return {
            thread.id: (thread.preference_for(user_id).cleared_at if thread.preference_for(user_id) is not None else None)
            for thread in threads
        }

    @staticmethod
    def _build_conversation(
        thread: ChatThread,
        current_user_id: int,
        last_message: ChatMessage | None,
        unread_count: int,
    ) -> ChatConversationRead:
        peer = thread.peer_for(current_user_id)
        preference = thread.preference_for(current_user_id)
        return ChatConversationRead(
            peer=ChatService._build_user_summary(peer),
            last_message=ChatMessageRead.model_validate(last_message) if last_message is not None else None,
            unread_count=unread_count,
            muted=preference.muted if preference is not None else False,
        )

    @staticmethod
    def _build_user_summary(user: User) -> ChatUserSummaryRead:
        return ChatUserSummaryRead(
            id=user.id,
            nome=user.nome,
            login=user.login,
            online=chat_event_broker.is_user_online(user.id),
        )