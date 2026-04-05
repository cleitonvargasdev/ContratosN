from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PermissionResourceRead(BaseModel):
    resource_key: str
    resource_label: str
    resource_group: str
    supported_actions: list[str]


class ProfilePermissionBase(BaseModel):
    resource_key: str
    resource_label: str | None = None
    can_read: bool = False
    can_create: bool = False
    can_update: bool = False
    can_delete: bool = False

    @field_validator("resource_key", mode="before")
    @classmethod
    def normalize_resource_key(cls, value: object) -> str:
        normalized = str(value).strip().lower().replace(" ", "_")
        if not normalized:
            raise ValueError("Recurso obrigatorio")
        return normalized

    @field_validator("resource_label", mode="before")
    @classmethod
    def normalize_resource_label(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class ProfilePermissionWrite(ProfilePermissionBase):
    pass


class ProfilePermissionRead(ProfilePermissionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ProfileBase(BaseModel):
    nome: str
    descricao: str | None = None
    ativo: bool = True

    @field_validator("nome", mode="before")
    @classmethod
    def normalize_nome(cls, value: object) -> str:
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("Nome do perfil obrigatorio")
        return normalized

    @field_validator("descricao", mode="before")
    @classmethod
    def normalize_descricao(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class ProfileCreate(ProfileBase):
    permissions: list[ProfilePermissionWrite] = Field(default_factory=list)


class ProfileUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    ativo: bool | None = None
    permissions: list[ProfilePermissionWrite] | None = None

    @field_validator("nome", mode="before")
    @classmethod
    def normalize_optional_nome(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @field_validator("descricao", mode="before")
    @classmethod
    def normalize_optional_descricao(cls, value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class ProfileRead(ProfileBase):
    id: int
    permissions: list[ProfilePermissionRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserApiKeyInfo(BaseModel):
    key_prefix: str
    active: bool
    created_at: datetime
    rotated_at: datetime | None = None
    last_used_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserApiKeySecret(UserApiKeyInfo):
    api_key: str
