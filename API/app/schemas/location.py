from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator


FERIADO_NIVEIS = (1, 2, 3)


class UFBase(BaseModel):
    uf: str
    uf_nome: str
    cod_ibge: int | None = None

    @field_validator("uf", mode="before")
    @classmethod
    def normalize_uf(cls, value: object) -> str:
        normalized = str(value).strip().upper()
        if len(normalized) != 2:
            raise ValueError("UF deve ter 2 caracteres")
        return normalized

    @field_validator("uf_nome", mode="before")
    @classmethod
    def normalize_uf_nome(cls, value: object) -> str:
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("Nome da UF obrigatorio")
        return normalized


class UFCreate(UFBase):
    pass


class UFUpdate(BaseModel):
    uf: str | None = None
    uf_nome: str | None = None
    cod_ibge: int | None = None

    @field_validator("uf", mode="before")
    @classmethod
    def normalize_optional_uf(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip().upper()
        if not normalized:
            return None
        if len(normalized) != 2:
            raise ValueError("UF deve ter 2 caracteres")
        return normalized

    @field_validator("uf_nome", mode="before")
    @classmethod
    def normalize_optional_uf_nome(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class UFRead(UFBase):
    uf_id: int

    model_config = ConfigDict(from_attributes=True)


class CidadeBase(BaseModel):
    uf_id: int
    cidade: str

    @field_validator("cidade", mode="before")
    @classmethod
    def normalize_cidade(cls, value: object) -> str:
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("Cidade obrigatoria")
        return normalized


class CidadeCreate(CidadeBase):
    pass


class CidadeUpdate(BaseModel):
    uf_id: int | None = None
    cidade: str | None = None

    @field_validator("cidade", mode="before")
    @classmethod
    def normalize_optional_cidade(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class CidadeRead(BaseModel):
    cidade_id: int
    uf_id: int
    cidade: str
    uf: str | None = None
    uf_nome: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BairroBase(BaseModel):
    cidade_id: int
    bairro_nome: str

    @field_validator("bairro_nome", mode="before")
    @classmethod
    def normalize_bairro_nome(cls, value: object) -> str:
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("Bairro obrigatorio")
        return normalized


class BairroCreate(BairroBase):
    pass


class BairroUpdate(BaseModel):
    cidade_id: int | None = None
    bairro_nome: str | None = None

    @field_validator("bairro_nome", mode="before")
    @classmethod
    def normalize_optional_bairro_nome(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class BairroRead(BaseModel):
    bairro_id: int
    cidade_id: int
    bairro_nome: str
    cidade: str | None = None
    uf: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AddressLookupResponse(BaseModel):
    found: bool
    source: str | None = None
    cep: str | None = None
    endereco: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    bairro_id: int | None = None
    cidade: str | None = None
    cidade_id: int | None = None
    uf: str | None = None


class FeriadoBase(BaseModel):
    data: date
    cidade_id: int | None = None
    uf: str | None = None
    descricao: str
    nivel: int

    @field_validator("descricao", mode="before")
    @classmethod
    def normalize_descricao(cls, value: object) -> str:
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("Descricao obrigatoria")
        return normalized

    @field_validator("uf", mode="before")
    @classmethod
    def normalize_optional_uf_for_feriado(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip().upper()
        if not normalized:
            return None
        if len(normalized) != 2:
            raise ValueError("UF deve ter 2 caracteres")
        return normalized

    @field_validator("nivel", mode="before")
    @classmethod
    def normalize_nivel(cls, value: object) -> int:
        if value is None or str(value).strip() == "":
            raise ValueError("Nivel de feriado obrigatorio")
        normalized = int(value)
        if normalized not in FERIADO_NIVEIS:
            raise ValueError("Nivel de feriado invalido")
        return normalized


class FeriadoCreate(FeriadoBase):
    pass


class FeriadoUpdate(BaseModel):
    data: date | None = None
    cidade_id: int | None = None
    uf: str | None = None
    descricao: str | None = None
    nivel: int | None = None

    @field_validator("descricao", mode="before")
    @classmethod
    def normalize_optional_descricao(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @field_validator("uf", mode="before")
    @classmethod
    def normalize_optional_uf_update(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip().upper()
        return normalized or None

    @field_validator("nivel", mode="before")
    @classmethod
    def normalize_optional_nivel(cls, value: object) -> int | None:
        if value is None:
            return None
        normalized = int(value)
        if normalized not in FERIADO_NIVEIS:
            raise ValueError("Nivel de feriado invalido")
        return normalized


class FeriadoRead(BaseModel):
    feriado_id: int
    data: date
    cidade_id: int | None = None
    cidade: str | None = None
    uf: str | None = None
    descricao: str
    nivel: int

    model_config = ConfigDict(from_attributes=True)