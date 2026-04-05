from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class ChatUserSummaryRead(BaseModel):
    id: int
    nome: str
    login: str
    online: bool = False

    model_config = ConfigDict(from_attributes=True)


class ChatMessageCreate(BaseModel):
    content: str

    @field_validator("content", mode="before")
    @classmethod
    def normalize_content(cls, value: object) -> str:
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("Mensagem obrigatoria")
        if len(normalized) > 2000:
            raise ValueError("Mensagem excede o limite de 2000 caracteres")
        return normalized


class ChatMessageRead(BaseModel):
    id: int
    thread_id: int
    sender_id: int
    recipient_id: int
    content: str
    created_at: datetime
    delivered_at: datetime | None = None
    read_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ChatConversationRead(BaseModel):
    peer: ChatUserSummaryRead
    last_message: ChatMessageRead | None = None
    unread_count: int = 0
    muted: bool = False


class ChatMuteUpdate(BaseModel):
    muted: bool


class ChatSendMessageResponse(BaseModel):
    conversation: ChatConversationRead
    message: ChatMessageRead


class ChatEventPayload(BaseModel):
    resource: str = "chat"
    event: str
    conversation: ChatConversationRead
    message: ChatMessageRead | None = None
    deleted_message_id: int | None = None


class ChatMessageDeleteResponse(BaseModel):
    conversation: ChatConversationRead
    deleted_message_id: int