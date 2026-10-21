from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class MobileBatchItemCreate(BaseModel):
    source_item_id: str = Field(min_length=1, max_length=100)
    kind: str
    client_id: int | None = None
    contract_id: int | None = None
    installment_id: int | None = None
    amount_units: int | None = Field(default=None, gt=0)
    latitude: float | None = None
    longitude: float | None = None
    gps_status: str | None = None
    device_recorded_at: datetime | None = None

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, value: str) -> str:
        if value not in {"payment", "unpaid", "closed"}:
            raise ValueError("Tipo de item invalido")
        return value


class MobileBatchCreate(BaseModel):
    source_id: str = Field(min_length=1, max_length=64)
    items: list[MobileBatchItemCreate] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_distinct_items(self) -> "MobileBatchCreate":
        source_ids = [item.source_item_id for item in self.items]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Um lote nao pode conter itens repetidos")
        return self


class MobileBatchItemRead(BaseModel):
    id: int
    source_item_id: str
    kind: str
    client_id: int | None
    contract_id: int | None
    installment_id: int | None
    amount_units: int | None
    processed: bool
    blocked: bool
    block_reason: str | None


class MobileBatchRead(BaseModel):
    id: int
    source_id: str
    user_id: int
    collector_name: str
    status: str
    blocked: bool
    block_reason: str | None
    items: list[MobileBatchItemRead]


class MobileBatchUnlock(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)
