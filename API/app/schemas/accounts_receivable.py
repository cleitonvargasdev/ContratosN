from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.pagination import PaginatedResponse, PaginationParams


class ContractInstallmentRead(BaseModel):
    id: int
    contratos_id: int | None = None
    parcela_nro: int | None = None
    vencimento_original: datetime | None = None
    vencimentol: datetime | None = None
    valor_base: float | None = None
    valor_total: float | None = None
    valor_recebido: float | None = None
    data_recebimento: datetime | None = None
    quitado: bool | None = None
    desconto: float | None = None
    valor_juros: float | None = None
    dia_semana: str | None = None
    possui_pagamento: bool = False
    msg_whatsapp: bool = False
    dt_hora_envio: datetime | None = None
    tipo_envio: int | None = None


class AccountsReceivableListParams(PaginationParams):
    recebida: bool | None = None
    cliente_query: str | None = None
    data_vencimento_inicial: date | None = None
    data_vencimento_final: date | None = None

    @field_validator("cliente_query", mode="before")
    @classmethod
    def normalize_cliente_query(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class AccountsReceivableListItem(BaseModel):
    id: int
    contratos_id: int | None = None
    cliente_id: int | None = None
    cliente_nome: str | None = None
    cliente_cpf_cnpj: str | None = None
    parcela_nro: int | None = None
    vencimento: datetime | None = None
    valor_total: float | None = None
    valor_recebido: float | None = None
    valor_em_aberto: float = 0
    data_recebimento: datetime | None = None
    quitado: bool | None = None
    dia_semana: str | None = None


class AccountsReceivableListResponse(PaginatedResponse[AccountsReceivableListItem]):
    model_config = ConfigDict()


class ContractInstallmentGenerateItem(BaseModel):
    parcela_nro: int
    vencimento: datetime
    valor_total: float

    @field_validator("valor_total", mode="before")
    @classmethod
    def normalize_valor_total(cls, value: object) -> float:
        return float(value)


class ContractInstallmentGenerateRequest(BaseModel):
    parcelas: list[ContractInstallmentGenerateItem]


class InstallmentPaymentCreate(BaseModel):
    valor_recebido: float
    data_recebimento: datetime | None = None
    desconto: float | None = None
    juros: float | None = None

    @field_validator("valor_recebido", "desconto", "juros", mode="before")
    @classmethod
    def normalize_float_fields(cls, value: object) -> float | None:
        if value is None or value == "":
            return None
        return float(value)


class BatchInstallmentReceivePreviewRequest(BaseModel):
    valor_recebido: float
    data_recebimento: datetime | None = None

    @field_validator("valor_recebido", mode="before")
    @classmethod
    def normalize_batch_valor_recebido(cls, value: object) -> float:
        return float(value)


class InstallmentSettleRequest(BaseModel):
    data_recebimento: datetime | None = None


class InstallmentUpdateRequest(BaseModel):
    parcela_nro: int
    vencimento: datetime
    valor_base: float
    valor_juros: float | None = None
    valor_total: float | None = None

    @field_validator("valor_base", "valor_juros", "valor_total", mode="before")
    @classmethod
    def normalize_update_float_fields(cls, value: object) -> float | None:
        if value is None or value == "":
            return None
        return float(value)


class InstallmentCreateRequest(BaseModel):
    parcela_nro: int
    vencimento: datetime
    valor_base: float
    valor_juros: float | None = None
    valor_total: float | None = None

    @field_validator("valor_base", "valor_juros", "valor_total", mode="before")
    @classmethod
    def normalize_create_float_fields(cls, value: object) -> float | None:
        if value is None or value == "":
            return None
        return float(value)


class ContractReceiptRead(BaseModel):
    recebimento_id: int
    contrato_id: int | None = None
    parcela_nro: int | None = None
    valor_recebido: float | None = None
    desconto: float | None = None
    juros: float | None = None
    data_recebimento: datetime | None = None
    usuario_id: int | None = None
    usuario_nome: str | None = None


class BatchInstallmentReceivePreviewItem(BaseModel):
    installment: ContractInstallmentRead
    saldo_restante: float
    valor_recebimento: float


class BatchInstallmentReceivePreviewRead(BaseModel):
    contrato_id: int
    valor_informado: float
    valor_distribuido: float
    parcelas: list[BatchInstallmentReceivePreviewItem]


class BatchInstallmentReceiveConfirmRead(BaseModel):
    contrato_id: int
    valor_informado: float
    valor_processado: float
    parcelas_processadas: list[ContractInstallmentRead]


class InstallmentActionResult(BaseModel):
    installment: ContractInstallmentRead
    model_config = ConfigDict(from_attributes=True)


class InstallmentWhatsAppSendResponse(BaseModel):
    success: bool
    message: str
    chatid: str
    installment_id: int