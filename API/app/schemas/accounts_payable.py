from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.pagination import PaginatedResponse, PaginationParams


PersonType = Literal["cliente", "fornecedor", "funcionario"]


class AccountsPayablePersonSearchItem(BaseModel):
    entity_id: int
    tipo_pessoa: PersonType
    nome: str
    cpf_cnpj: str | None = None


class AccountsPayablePaymentBase(BaseModel):
    data_pagamento: date | None = None
    valor_pago: float | None = None
    juros: float | None = 0
    acrescimos: float | None = 0
    desconto: float | None = 0
    observacao: str | None = None

    @field_validator("valor_pago", "juros", "acrescimos", "desconto", mode="before")
    @classmethod
    def normalize_float_fields(cls, value: object) -> float | None:
        if value is None or value == "":
            return None
        return float(value)

    @field_validator("observacao", mode="before")
    @classmethod
    def normalize_observacao(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class AccountsPayablePaymentCreate(AccountsPayablePaymentBase):
    pass


class AccountsPayablePaymentRead(AccountsPayablePaymentBase):
    pagamento_id: int
    usuario_id: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccountsPayableInstallmentBase(BaseModel):
    numero_parcela: int | None = Field(default=None, ge=1)
    descricao: str | None = None
    data_referencia_inicial: date | None = None
    data_referencia_final: date | None = None
    vencimento: date
    valor_original: float
    acrescimos: float | None = 0
    desconto: float | None = 0
    observacao: str | None = None

    @field_validator("descricao", "observacao", mode="before")
    @classmethod
    def normalize_string_fields(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @field_validator("valor_original", "acrescimos", "desconto", mode="before")
    @classmethod
    def normalize_numeric_fields(cls, value: object) -> float:
        if value is None or value == "":
            return 0.0
        return float(value)


class AccountsPayableInstallmentCreate(AccountsPayableInstallmentBase):
    pass


class AccountsPayableInstallmentRead(AccountsPayableInstallmentBase):
    parcela_id: int
    valor_total: float
    valor_pago: float
    saldo_pagar: float
    quitado: bool
    pagamentos: list[AccountsPayablePaymentRead] = []

    model_config = ConfigDict(from_attributes=True)


class AccountsPayableBase(BaseModel):
    descricao: str | None = None
    tipo_pessoa: PersonType
    cliente_id: int | None = None
    usuario_id: int | None = None
    fornecedor_id: int | None = None
    data_referencia_inicial: date | None = None
    data_referencia_final: date | None = None
    observacao: str | None = None

    @field_validator("descricao", "observacao", mode="before")
    @classmethod
    def normalize_string_fields(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_person_link(self) -> "AccountsPayableBase":
        linked = {
            "cliente": self.cliente_id,
            "funcionario": self.usuario_id,
            "fornecedor": self.fornecedor_id,
        }
        expected_value = linked[self.tipo_pessoa]
        if expected_value is None:
            raise ValueError("A pessoa vinculada ao tipo selecionado e obrigatoria.")
        return self


class AccountsPayableCreate(AccountsPayableBase):
    descricao: str
    parcelas: list[AccountsPayableInstallmentCreate]


class AccountsPayableUpdate(AccountsPayableBase):
    descricao: str


class AccountsPayableAddInstallmentsRequest(BaseModel):
    parcelas: list[AccountsPayableInstallmentCreate]


class AccountsPayableListParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    quitado: bool | None = None
    pessoa_query: str | None = None
    tipo_pessoa: PersonType | None = None
    data_vencimento_inicial: date | None = None
    data_vencimento_final: date | None = None
    data_referencia_inicial: date | None = None
    data_referencia_final: date | None = None

    @field_validator("pessoa_query", mode="before")
    @classmethod
    def normalize_query(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class AccountsPayableListItem(BaseModel):
    conta_pagar_id: int
    descricao: str
    tipo_pessoa: PersonType
    pessoa_id: int
    pessoa_nome: str
    pessoa_cpf_cnpj: str | None = None
    data_referencia_inicial: date | None = None
    data_referencia_final: date | None = None
    proximo_vencimento: date | None = None
    ultima_data_vencimento: date | None = None
    quantidade_parcelas: int
    quantidade_parcelas_abertas: int
    valor_total: float
    valor_pago: float
    saldo_pagar: float
    quitado: bool


class AccountsPayableListResponse(BaseModel):
    items: list[AccountsPayableListItem]
    total: int
    page: int
    page_size: int


class PaymentMovementListParams(PaginationParams):
    query: str | None = None
    quitado: bool | None = False
    data_vencimento_inicial: date | None = None
    data_vencimento_final: date | None = None


class PaymentMovementItem(BaseModel):
    parcela_id: int
    conta_pagar_id: int
    vencimento: date
    quitado: bool
    data_pagamento: date | None = None
    descricao: str
    pessoa_nome: str
    pessoa_tipo: PersonType
    documento: str | None = None
    telefone: str | None = None
    valor_total: float
    valor_pago: float
    saldo_pagar: float


class PaymentMovementListResponse(PaginatedResponse[PaymentMovementItem]):
    total_valor: float = 0
    total_pago: float = 0
    total_aberto: float = 0


class AccountsPayableRead(AccountsPayableBase):
    conta_pagar_id: int
    pessoa_id: int
    pessoa_nome: str
    pessoa_cpf_cnpj: str | None = None
    valor_total: float
    valor_pago: float
    saldo_pagar: float
    quitado: bool
    created_at: datetime
    updated_at: datetime
    parcelas: list[AccountsPayableInstallmentRead]

    model_config = ConfigDict(from_attributes=True)
