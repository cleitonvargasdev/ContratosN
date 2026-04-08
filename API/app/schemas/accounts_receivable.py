from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


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


class InstallmentActionResult(BaseModel):
    installment: ContractInstallmentRead
    model_config = ConfigDict(from_attributes=True)