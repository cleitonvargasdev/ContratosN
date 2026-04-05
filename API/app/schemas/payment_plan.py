from pydantic import BaseModel, ConfigDict, field_validator


class PaymentPlanBase(BaseModel):
    descricao: str | None = None
    qtde_dias: int | None = None
    percent_juros: float | None = None
    valor_parcela: float | None = None
    valor_base: float | None = None
    valor_final: float | None = None

    @field_validator("descricao", mode="before")
    @classmethod
    def normalize_descricao(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @field_validator("qtde_dias", mode="before")
    @classmethod
    def normalize_qtde_dias(cls, value: object) -> int | None:
        if value is None or value == "":
            return None
        return int(value)

    @field_validator("percent_juros", "valor_parcela", "valor_base", "valor_final", mode="before")
    @classmethod
    def normalize_float_fields(cls, value: object) -> float | None:
        if value is None or value == "":
            return None
        return float(value)


class PaymentPlanCreate(PaymentPlanBase):
    pass


class PaymentPlanUpdate(PaymentPlanBase):
    pass


class PaymentPlanRead(PaymentPlanBase):
    plano_id: int

    model_config = ConfigDict(from_attributes=True)