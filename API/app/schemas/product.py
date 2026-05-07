from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.pagination import PaginatedResponse, PaginationParams


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
        if ',' in normalized and '.' in normalized:
            normalized = normalized.replace('.', '').replace(',', '.')
        elif ',' in normalized:
            normalized = normalized.replace(',', '.')
        return round(float(normalized), 2)
    return round(float(value), 2)


class BrandBase(BaseModel):
    descricao: str | None = None

    @field_validator("descricao", mode="before")
    @classmethod
    def normalize_descricao(cls, value: object) -> str | None:
        return _strip_to_none(value)


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BrandBase):
    pass


class BrandRead(BrandBase):
    marca_id: int

    model_config = ConfigDict(from_attributes=True)


class BrandOptionRead(BaseModel):
    marca_id: int
    descricao: str

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    descricao: str | None = None
    valor_compra: float | None = None
    valor_venda: float | None = None
    marca_id: int | None = None
    garantia: int | None = None
    ativo: bool = True
    estoque: int | None = None
    modelo: str | None = None
    cor: str | None = None

    @field_validator("descricao", "modelo", "cor", mode="before")
    @classmethod
    def normalize_text_fields(cls, value: object) -> str | None:
        return _strip_to_none(value)

    @field_validator("valor_compra", "valor_venda", mode="before")
    @classmethod
    def normalize_float_fields(cls, value: object) -> float | None:
        return _normalize_money(value)

    @field_validator("marca_id", "garantia", "estoque", mode="before")
    @classmethod
    def normalize_int_fields(cls, value: object) -> int | None:
        if value in (None, ""):
            return None
        return int(value)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    ativo: bool | None = None


class ProductRead(ProductBase):
    produto_id: int
    marca_descricao: str | None = None
    marca: BrandRead | None = None

    model_config = ConfigDict(from_attributes=True)


class BrandListParams(PaginationParams):
    descricao: str | None = None


class ProductListParams(PaginationParams):
    descricao: str | None = None
    marca_id: int | None = None
    ativo: bool | None = None


class BrandListResponse(PaginatedResponse[BrandRead]):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [{"marca_id": 1, "descricao": "Samsung"}],
                "total": 1,
                "page": 1,
                "page_size": 10,
            }
        }
    )


class ProductListResponse(PaginatedResponse[ProductRead]):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "produto_id": 1,
                        "descricao": "Smartphone Galaxy A55",
                        "valor_compra": 1200.0,
                        "valor_venda": 1599.9,
                        "marca_id": 1,
                        "marca_descricao": "Samsung",
                        "garantia": 365,
                        "ativo": True,
                        "estoque": 5,
                        "modelo": "A55",
                        "cor": "Preto",
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 10,
            }
        }
    )