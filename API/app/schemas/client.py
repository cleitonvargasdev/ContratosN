from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.pagination import PaginatedResponse, PaginationParams


def _strip_to_none(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return str(value)
    cleaned = value.strip()
    return cleaned or None


def _digits_only(value: object) -> str | None:
    cleaned = _strip_to_none(value)
    if cleaned is None:
        return None
    digits = "".join(char for char in cleaned if char.isdigit())
    return digits or None


class ClientBase(BaseModel):
    nome: str | None = None
    rg: int | None = None
    cpf_cnpj: str | None = None
    endereco: str | None = None
    bairro_id: int | None = None
    cidade_id: int | None = None
    uf: str | None = None
    usuario_id: int | None = None
    cnpj: str | None = None
    telefone: str | None = None
    celular01: str | None = None
    celular02: str | None = None
    flag_whatsapp: bool = False
    email: EmailStr | None = None
    limite_credito: float | None = None
    debito_atual: float | None = None
    prox_vencto: datetime | None = None
    data_ultcompra: datetime | None = None
    rg_ie: str | None = None
    latitude: str | None = None
    longitude: str | None = None
    cep: str | None = None
    nro: str | None = None
    complemento: str | None = None
    ativo: bool = True
    bloqueado: bool = False
    comissao_diferente: bool = False
    percent_comissao: float | None = None
    naopagarcomissao: bool = False
    parc_atrasadas: int | None = None
    valor_atrasado: float | None = None
    valor_em_aberto: float | None = None
    parc_aberto: int | None = None
    desativado: bool = False
    data_desat: datetime | None = None
    contato_responsavel: str | None = None
    endereco_responsavel: str | None = None
    fone_responsavel: str | None = None
    cel_responsavel: str | None = None
    flag_whatsapp_responsavel: bool = False
    cep_responsavel: str | None = None
    complemento_responsavel: str | None = None
    uf_responsavel: str | None = None
    cidade_responsavel_id: int | None = None
    bairro_id_responsavel: int | None = None
    nro_responsavel: str | None = None
    nacionalidade: str | None = None
    estado_civil: str | None = None
    profissao: str | None = None
    turno_cobranca: str | None = None
    score: int | None = Field(default=1000)
    regra_juros_id: int | None = None
    media_atraso_parcelas: float | None = None
    media_atraso_contratos: float | None = None

    @field_validator(
        "nome",
        "endereco",
        "rg_ie",
        "latitude",
        "longitude",
        "nro",
        "complemento",
        "contato_responsavel",
        "endereco_responsavel",
        "complemento_responsavel",
        "nro_responsavel",
        "nacionalidade",
        "estado_civil",
        "profissao",
        "turno_cobranca",
        mode="before",
    )
    @classmethod
    def normalize_text_fields(cls, value: object) -> str | None:
        return _strip_to_none(value)

    @field_validator("telefone", "celular01", "celular02", "fone_responsavel", "cel_responsavel", mode="before")
    @classmethod
    def normalize_phone_fields(cls, value: object) -> str | None:
        return _digits_only(value)

    @field_validator("cpf_cnpj", "cnpj", "cep", "cep_responsavel", mode="before")
    @classmethod
    def normalize_digit_fields(cls, value: object) -> str | None:
        return _digits_only(value)

    @field_validator("uf", "uf_responsavel", mode="before")
    @classmethod
    def normalize_uf_fields(cls, value: object) -> str | None:
        normalized = _strip_to_none(value)
        return normalized.upper() if normalized else None

    @field_validator(
        "bairro_id",
        "cidade_id",
        "usuario_id",
        "cidade_responsavel_id",
        "bairro_id_responsavel",
        "regra_juros_id",
        "parc_atrasadas",
        "parc_aberto",
        mode="before",
    )
    @classmethod
    def normalize_int_fields(cls, value: object) -> int | None:
        if value in (None, ""):
            return None
        return int(value)

    @field_validator("rg", "score", mode="before")
    @classmethod
    def normalize_optional_int_fields(cls, value: object) -> int | None:
        if value in (None, ""):
            return None
        return int(value)

    @field_validator(
        "limite_credito",
        "debito_atual",
        "percent_comissao",
        "valor_atrasado",
        "valor_em_aberto",
        "media_atraso_parcelas",
        "media_atraso_contratos",
        mode="before",
    )
    @classmethod
    def normalize_float_fields(cls, value: object) -> float | None:
        if value in (None, ""):
            return None
        return float(value)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(ClientBase):
    pass


class ClientRead(ClientBase):
    clientes_id: int

    model_config = ConfigDict(from_attributes=True)


class ClientCobradorOptionRead(BaseModel):
    id: int
    nome: str

    model_config = ConfigDict(from_attributes=True)


class ClientListParams(PaginationParams):
    nome: str | None = None
    cpf_cnpj: str | None = None
    ativo: bool | None = None


class ClientListResponse(PaginatedResponse[ClientRead]):
    model_config = ConfigDict()