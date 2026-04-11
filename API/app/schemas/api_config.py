from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.pagination import PaginatedResponse, PaginationParams


def _strip_to_none(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return str(value)
    cleaned = value.strip()
    return cleaned or None


class ApiConfigBase(BaseModel):
    usuario_id: int | None = None
    nome_api: str | None = None
    funcionalidade: str | None = None
    url: str | None = None
    key1: str | None = None
    value1: str | None = None
    key2: str | None = None
    value2: str | None = None
    key3: str | None = None
    value3: str | None = None
    key4: str | None = None
    value4: str | None = None
    key5: str | None = None
    value5: str | None = None
    body: str | None = None

    @field_validator(
        "nome_api",
        "funcionalidade",
        "url",
        "key1",
        "value1",
        "key2",
        "value2",
        "key3",
        "value3",
        "key4",
        "value4",
        "key5",
        "value5",
        "body",
        mode="before",
    )
    @classmethod
    def normalize_text_fields(cls, value: object) -> str | None:
        return _strip_to_none(value)

    @field_validator("usuario_id", mode="before")
    @classmethod
    def normalize_user_id(cls, value: object) -> int | None:
        if value in (None, ""):
            return None
        return int(value)


class ApiConfigCreate(ApiConfigBase):
    pass


class ApiConfigUpdate(ApiConfigBase):
    pass


class ApiConfigRead(ApiConfigBase):
    api_id: int
    usuario_nome: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ApiConfigListParams(PaginationParams):
    nome_api: str | None = None
    usuario_id: int | None = None


class ApiConfigListResponse(PaginatedResponse[ApiConfigRead]):
    model_config = ConfigDict()