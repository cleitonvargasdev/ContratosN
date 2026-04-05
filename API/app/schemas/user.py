from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.access_control import ProfilePermissionRead, UserApiKeyInfo
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


class UserAddressFields(BaseModel):
    telefone: str | None = None
    celular: str | None = None
    flag_whatsapp: bool = False
    cep: str | None = None
    endereco: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro_id: int | None = None
    cidade_id: int | None = None
    uf: str | None = None
    cpf: str | None = None
    rg: str | None = None
    data_nascimento: date | None = None

    @field_validator("telefone", "celular", "numero", "complemento", "endereco", "rg", mode="before")
    @classmethod
    def normalize_text_fields(cls, value: object) -> str | None:
        return _strip_to_none(value)

    @field_validator("cep", "cpf", mode="before")
    @classmethod
    def normalize_digits_fields(cls, value: object) -> str | None:
        return _digits_only(value)

    @field_validator("uf", mode="before")
    @classmethod
    def normalize_uf(cls, value: object) -> str | None:
        normalized = _strip_to_none(value)
        return normalized.upper() if normalized else None


class UserBase(UserAddressFields):
    nome: str
    login: str
    email: EmailStr
    funcao: str = "Operador"
    perfil_id: int | None = None
    perfil_ids: list[int] = Field(default_factory=list)
    ativo: bool = True

    @field_validator("perfil_id", mode="before")
    @classmethod
    def normalize_profile_id(cls, value: object) -> int | None:
        if value in (None, ""):
            return None
        profile_id = int(value)
        if profile_id <= 0:
            raise ValueError("Perfil invalido")
        return profile_id

    @field_validator("perfil_ids", mode="before")
    @classmethod
    def normalize_profile_ids(cls, value: object) -> list[int]:
        if value in (None, ""):
            return []

        raw_items = value if isinstance(value, (list, tuple, set)) else [value]
        normalized: list[int] = []
        seen: set[int] = set()

        for item in raw_items:
            if item in (None, ""):
                continue

            profile_id = int(item)
            if profile_id <= 0:
                raise ValueError("Perfil invalido")
            if profile_id in seen:
                continue

            seen.add(profile_id)
            normalized.append(profile_id)

        return normalized

    def resolve_profile_ids(self) -> list[int] | None:
        if "perfil_ids" in self.model_fields_set:
            return list(self.perfil_ids)
        if "perfil_id" in self.model_fields_set:
            return [] if self.perfil_id is None else [self.perfil_id]
        return None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nome": "Maria Oliveira",
                    "login": "maria.oliveira",
                    "email": "maria.oliveira@example.com",
                    "funcao": "Operador",
                    "perfil_ids": [2],
                    "telefone": "11998887766",
                    "celular": "11997776655",
                    "flag_whatsapp": True,
                    "cep": "79002123",
                    "endereco": "Rua das Palmeiras",
                    "numero": "120",
                    "complemento": "Apto 12",
                    "bairro_id": 1,
                    "cidade_id": 1,
                    "uf": "MS",
                    "cpf": "12345678901",
                    "rg": "1234567",
                    "data_nascimento": "1990-05-20",
                    "ativo": True,
                }
            ]
        }
    )


class UserCreate(UserBase):
    senha: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "Maria Oliveira",
                "login": "maria.oliveira",
                "email": "maria.oliveira@example.com",
                "senha": "123456",
                "funcao": "Operador",
                "perfil_ids": [2],
                "telefone": "11998887766",
                "celular": "11997776655",
                "flag_whatsapp": True,
                "cep": "79002123",
                "endereco": "Rua das Palmeiras",
                "numero": "120",
                "complemento": "Apto 12",
                "bairro_id": 1,
                "cidade_id": 1,
                "uf": "MS",
                "cpf": "12345678901",
                "rg": "1234567",
                "data_nascimento": "1990-05-20",
                "ativo": True,
            }
        }
    )


class UserUpdate(UserAddressFields):
    nome: str | None = None
    login: str | None = None
    email: EmailStr | None = None
    senha: str | None = None
    funcao: str | None = None
    perfil_id: int | None = None
    perfil_ids: list[int] = Field(default_factory=list)
    ativo: bool | None = None

    @field_validator("perfil_id", mode="before")
    @classmethod
    def normalize_optional_profile_id(cls, value: object) -> int | None:
        if value in (None, ""):
            return None
        profile_id = int(value)
        if profile_id <= 0:
            raise ValueError("Perfil invalido")
        return profile_id

    @field_validator("perfil_ids", mode="before")
    @classmethod
    def normalize_optional_profile_ids(cls, value: object) -> list[int]:
        return UserBase.normalize_profile_ids(value)

    def resolve_profile_ids(self) -> list[int] | None:
        if "perfil_ids" in self.model_fields_set:
            return list(self.perfil_ids)
        if "perfil_id" in self.model_fields_set:
            return [] if self.perfil_id is None else [self.perfil_id]
        return None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "Maria Oliveira Atualizada",
                "login": "maria.oliveira.atualizada",
                "senha": "654321",
                "funcao": "Administrador",
                "perfil_ids": [1, 2],
                "telefone": "11990001122",
                "celular": "11995554433",
                "flag_whatsapp": False,
                "cep": "79002123",
                "endereco": "Rua das Palmeiras",
                "numero": "999",
                "complemento": "Casa fundos",
                "bairro_id": 1,
                "cidade_id": 1,
                "uf": "MS",
                "cpf": "12345678901",
                "rg": "9876543",
                "data_nascimento": "1990-05-20",
                "ativo": False,
            }
        }
    )


class UserRead(UserBase):
    id: int
    perfil_nome: str | None = None
    perfil_nomes: list[str] = Field(default_factory=list)
    api_key_info: UserApiKeyInfo | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "nome": "Maria Oliveira",
                "login": "maria.oliveira",
                "email": "maria.oliveira@example.com",
                "funcao": "Operador",
                "perfil_id": 2,
                "perfil_ids": [2, 5],
                "perfil_nome": "Operacional",
                "perfil_nomes": ["Operacional", "Vendedor"],
                "telefone": "11998887766",
                "celular": "11997776655",
                "flag_whatsapp": True,
                "cep": "79002123",
                "endereco": "Rua das Palmeiras",
                "numero": "120",
                "complemento": "Apto 12",
                "bairro_id": 1,
                "cidade_id": 1,
                "uf": "MS",
                "cpf": "12345678901",
                "rg": "1234567",
                "data_nascimento": "1990-05-20",
                "ativo": True,
                "api_key_info": {
                    "key_prefix": "ctr_abcdef12",
                    "active": True,
                    "created_at": "2026-04-01T10:00:00Z",
                    "rotated_at": None,
                    "last_used_at": None
                },
                "created_at": "2026-04-01T10:00:00Z",
                "updated_at": "2026-04-01T10:00:00Z",
            }
        },
    )


class AuthenticatedUserRead(UserRead):
    permissions: list[ProfilePermissionRead] = Field(default_factory=list)


class UserListParams(PaginationParams):
    nome: str | None = None
    email: EmailStr | None = None
    ativo: bool | None = None


class UserListResponse(PaginatedResponse[UserRead]):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": 1,
                        "nome": "Ana Souza",
                        "login": "ana.souza",
                        "email": "ana.souza@example.com",
                        "funcao": "Administrador",
                        "perfil_id": 1,
                        "perfil_ids": [1],
                        "perfil_nome": "Administrador",
                        "perfil_nomes": ["Administrador"],
                        "telefone": "11990000001",
                        "celular": "11990000001",
                        "flag_whatsapp": True,
                        "cep": "79002123",
                        "endereco": "Rua Afonso Pena",
                        "numero": "1200",
                        "complemento": None,
                        "bairro_id": 1,
                        "cidade_id": 1,
                        "uf": "MS",
                        "cpf": "12345678901",
                        "rg": "1234567",
                        "data_nascimento": "1990-05-20",
                        "ativo": True,
                        "created_at": "2026-04-01T10:00:00Z",
                        "updated_at": "2026-04-01T10:00:00Z",
                    }
                ],
                "total": 10,
                "page": 1,
                "page_size": 10,
            }
        }
    )
