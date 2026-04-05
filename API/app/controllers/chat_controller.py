from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_user_from_access_token
from app.db.session import AsyncSessionLocal, get_db_session
from app.models.user import User
from app.realtime.chat_events import chat_event_broker
from app.schemas.chat import (
    ChatConversationRead,
    ChatMessageCreate,
    ChatMessageDeleteResponse,
    ChatMessageRead,
    ChatMuteUpdate,
    ChatSendMessageResponse,
    ChatUserSummaryRead,
)
from app.services.chat_service import ChatService


router = APIRouter(dependencies=[Depends(get_current_active_user)])
ws_router = APIRouter()


def get_chat_service(session: AsyncSession = Depends(get_db_session)) -> ChatService:
    return ChatService(session)


@router.get("/contatos", response_model=list[ChatUserSummaryRead], summary="Listar contatos do chat")
async def list_contacts(
    term: Annotated[str | None, Query(description="Filtro por nome ou login.")] = None,
    current_user: User = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service),
) -> list[ChatUserSummaryRead]:
    return await service.list_contacts(current_user, term)


@router.get("/conversas", response_model=list[ChatConversationRead], summary="Listar conversas")
async def list_conversations(
    current_user: User = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service),
) -> list[ChatConversationRead]:
    return await service.list_conversations(current_user)


@router.get("/conversas/{peer_user_id}/mensagens", response_model=list[ChatMessageRead], summary="Listar mensagens")
async def list_messages(
    peer_user_id: int,
    limit: Annotated[int, Query(ge=1, le=200, description="Quantidade maxima de mensagens.")] = 100,
    current_user: User = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service),
) -> list[ChatMessageRead]:
    return await service.list_messages(current_user, peer_user_id, limit)


@router.post(
    "/conversas/{peer_user_id}/mensagens",
    response_model=ChatSendMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar mensagem",
)
async def send_message(
    peer_user_id: int,
    payload: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatSendMessageResponse:
    return await service.send_message(current_user, peer_user_id, payload)


@router.put("/conversas/{peer_user_id}/silenciar", response_model=ChatConversationRead, summary="Silenciar conversa")
async def set_conversation_muted(
    peer_user_id: int,
    payload: ChatMuteUpdate,
    current_user: User = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatConversationRead:
    return await service.set_muted(current_user, peer_user_id, payload)


@router.post("/conversas/{peer_user_id}/lidas", response_model=ChatConversationRead, summary="Marcar conversa como lida")
async def mark_conversation_as_read(
    peer_user_id: int,
    current_user: User = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatConversationRead:
    conversation = await service.mark_conversation_as_read(current_user, peer_user_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversa nao encontrada")
    return conversation


@router.delete("/conversas/{peer_user_id}/mensagens/{message_id}", response_model=ChatMessageDeleteResponse, summary="Apagar mensagem")
async def delete_message(
    peer_user_id: int,
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatMessageDeleteResponse:
    return await service.delete_message(current_user, peer_user_id, message_id)


@router.delete("/conversas/{peer_user_id}", response_model=ChatConversationRead, summary="Limpar conversa")
async def clear_conversation(
    peer_user_id: int,
    current_user: User = Depends(get_current_active_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatConversationRead:
    return await service.clear_conversation(current_user, peer_user_id)


@ws_router.websocket("/ws")
async def chat_websocket(websocket: WebSocket, token: str = Query(...)) -> None:
    async with AsyncSessionLocal() as session:
        try:
            user = await get_user_from_access_token(token, session)
        except HTTPException:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await chat_event_broker.connect(user.id, websocket)

    try:
        await websocket.send_json({"resource": "chat", "event": "connected"})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await chat_event_broker.disconnect(user.id, websocket)