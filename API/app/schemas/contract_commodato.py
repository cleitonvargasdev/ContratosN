from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip_to_none(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _normalize_money(value: object) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        normalized = value.strip()
        if "," in normalized and "." in normalized:
            normalized = normalized.replace(".", "").replace(",", ".")
        elif "," in normalized:
            normalized = normalized.replace(",", ".")
        return round(float(normalized), 2)
    return round(float(value), 2)


class ContractComodatoItemWrite(BaseModel):
    item_id: int | None = None
    produto_id: int | None = None
    quantidade: int = Field(default=1, ge=1)
    valor_unitario: float | None = None
    observacao: str | None = None

    @field_validator("valor_unitario", mode="before")
    @classmethod
    def normalize_money(cls, value: object) -> float | None:
        return _normalize_money(value)

    @field_validator("observacao", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> str | None:
        return _strip_to_none(value)


class ContractComodatoWrite(BaseModel):
    avalista_id: int | None = None
    items: list[ContractComodatoItemWrite] = Field(default_factory=list)


class ContractComodatoItemRead(BaseModel):
    item_id: int
    produto_id: int
    produto_descricao: str
    quantidade: int
    valor_unitario: float | None = None
    observacao: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ContractComodatoRead(BaseModel):
    contrato_id: int
    avalista_id: int | None = None
    avalista_nome: str | None = None
    items: list[ContractComodatoItemRead] = Field(default_factory=list)
    total_itens: int = 0
    total_quantidade: int = 0
    pode_imprimir: bool = False
