from pydantic import BaseModel, ConfigDict, field_validator


class SupplierBase(BaseModel):
    nome: str | None = None
    cpf_cnpj: str | None = None
    telefone: str | None = None
    email: str | None = None
    cep: str | None = None
    endereco: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    uf: str | None = None
    ativo: bool = True
    observacao: str | None = None

    @field_validator(
        "nome",
        "cpf_cnpj",
        "telefone",
        "email",
        "cep",
        "endereco",
        "numero",
        "complemento",
        "bairro",
        "cidade",
        "uf",
        "observacao",
        mode="before",
    )
    @classmethod
    def normalize_string_fields(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @field_validator("cpf_cnpj", "telefone", "cep", mode="after")
    @classmethod
    def normalize_digit_fields(cls, value: str | None) -> str | None:
        if value is None:
            return None
        digits = "".join(character for character in value if character.isdigit())
        return digits or None

    @field_validator("uf", mode="after")
    @classmethod
    def normalize_uf_field(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.upper()
        return normalized[:2] or None


class SupplierCreate(SupplierBase):
    nome: str


class SupplierUpdate(SupplierBase):
    pass


class SupplierRead(SupplierBase):
    fornecedor_id: int

    model_config = ConfigDict(from_attributes=True)


class SupplierListResponse(BaseModel):
    items: list[SupplierRead]
    total: int
    page: int
    page_size: int