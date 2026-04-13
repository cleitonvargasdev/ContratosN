from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.pagination import PaginatedResponse, PaginationParams


class WhatsAppDispatchBatchRead(BaseModel):
    id: int
    parametros_id: int | None = None
    scheduled_for: datetime | None = None
    executed_at: datetime
    status: str
    source_phone: str | None = None
    total_items: int
    total_sent: int
    total_errors: int
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class WhatsAppDispatchItemRead(BaseModel):
    id: int
    batch_id: int
    conta_receber_id: int | None = None
    contratos_id: int | None = None
    cliente_id: int | None = None
    parcela_nro: int | None = None
    client_name: str | None = None
    destination_phone: str | None = None
    source_phone: str | None = None
    status: str
    amount: float | None = None
    due_at: datetime | None = None
    sent_at: datetime | None = None
    message_payload: dict[str, object]
    provider_payload: dict[str, object] | None = None
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class WhatsAppDispatchBatchListParams(PaginationParams):
    data_inicial: date | None = None
    data_final: date | None = None


class WhatsAppDispatchBatchListResponse(PaginatedResponse[WhatsAppDispatchBatchRead]):
    model_config = ConfigDict()


class WhatsAppDispatchItemListResponse(PaginatedResponse[WhatsAppDispatchItemRead]):
    model_config = ConfigDict()