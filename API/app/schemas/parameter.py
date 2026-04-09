from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class ParameterScheduleEntry(BaseModel):
    dias_semana: list[int] = Field(default_factory=list)
    horario: str

    @field_validator("dias_semana", mode="before")
    @classmethod
    def normalize_weekdays(cls, value: object) -> list[int]:
        if value in (None, ""):
            return []
        items = [int(item) for item in value]
        return sorted({item for item in items if 0 <= item <= 6})

    @field_validator("horario", mode="before")
    @classmethod
    def normalize_schedule_time(cls, value: object) -> str:
        normalized = _strip_to_none(value)
        if normalized is None:
            raise ValueError("Horario do agendamento e obrigatorio")
        parts = normalized.split(":")
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            raise ValueError("Horario do agendamento invalido")
        hour = int(parts[0])
        minute = int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Horario do agendamento invalido")
        return f"{hour:02d}:{minute:02d}"


class ParameterBase(BaseModel):
    nome_fantasia: str | None = None
    razao_social: str | None = None
    endereco: str | None = None
    bairrosid: int | None = None
    cep: str | None = None
    nro: int | None = None
    cnpj: str | None = None
    uf: str | None = None
    cidade_id: int | None = None
    telefone1: str | None = None
    telefone2: str | None = None
    e_mail: str | None = None
    responsavel: str | None = None
    complemento: str | None = None
    emitir_sons: bool = True
    score_valor_inicial: int = Field(default=1000)
    score_pontos_atraso_parcela: int = Field(default=15)
    score_pontos_atraso_quitacao_contrato: int = Field(default=30)
    score_pontos_pagamento_em_dia: int = Field(default=5)
    score_pontos_quitacao_em_dia: int = Field(default=20)
    score_atualizacao_automatica: bool = False
    score_agendamentos: list[ParameterScheduleEntry] = Field(default_factory=list)
    score_atualizacao_ultima_execucao: datetime | None = None
    score_atualizacao_proxima_execucao: datetime | None = None
    score_ultima_execucao_sucesso: bool | None = None
    score_ultimo_erro: str | None = None
    whatsapp_cobranca_automatica: bool = False
    whatsapp_agendamentos: list[ParameterScheduleEntry] = Field(default_factory=list)
    whatsapp_cobranca_ultima_execucao: datetime | None = None
    whatsapp_cobranca_proxima_execucao: datetime | None = None
    whatsapp_ultima_execucao_sucesso: bool | None = None
    whatsapp_ultimo_erro: str | None = None
    whatsapp_cobranca_dias_antes: int = Field(default=1)
    whatsapp_cobranca_dias_depois: int = Field(default=1)
    whatsapp_cobranca_modelo: str | None = None

    @field_validator(
        "nome_fantasia",
        "razao_social",
        "endereco",
        "responsavel",
        "complemento",
        "score_ultimo_erro",
        "whatsapp_ultimo_erro",
        "whatsapp_cobranca_modelo",
        mode="before",
    )
    @classmethod
    def normalize_text_fields(cls, value: object) -> str | None:
        return _strip_to_none(value)

    @field_validator("telefone1", "telefone2", mode="before")
    @classmethod
    def normalize_phone_fields(cls, value: object) -> str | None:
        return _digits_only(value)

    @field_validator("cep", "cnpj", mode="before")
    @classmethod
    def normalize_digit_fields(cls, value: object) -> str | None:
        return _digits_only(value)

    @field_validator("uf", mode="before")
    @classmethod
    def normalize_uf(cls, value: object) -> str | None:
        normalized = _strip_to_none(value)
        return normalized.upper() if normalized else None

    @field_validator(
        "bairrosid",
        "nro",
        "cidade_id",
        "score_valor_inicial",
        "score_pontos_atraso_parcela",
        "score_pontos_atraso_quitacao_contrato",
        "score_pontos_pagamento_em_dia",
        "score_pontos_quitacao_em_dia",
        "whatsapp_cobranca_dias_antes",
        "whatsapp_cobranca_dias_depois",
        mode="before",
    )
    @classmethod
    def normalize_int_fields(cls, value: object) -> int | None:
        if value in (None, ""):
            return None
        return int(value)


class ParameterUpdate(ParameterBase):
    pass


class ParameterRead(ParameterBase):
    parametros_id: int

    model_config = ConfigDict(from_attributes=True)


class ParameterAutomationRunResponse(BaseModel):
    executado_em: datetime
    clientes_recalculados: int
    cobrancas_whatsapp_preparadas: int
    parametros: ParameterRead