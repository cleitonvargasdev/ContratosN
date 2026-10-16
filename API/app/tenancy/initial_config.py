"""Versioned initial data, owned by the platform rather than a business database."""
import json
import time
from pathlib import Path
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, create_model, model_validator
from sqlalchemy import Integer, Text, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.access_control_catalog import RESOURCE_CATALOG
from app.models.api_config import ApiConfig
from app.schemas.parameter import ParameterNinthDigitRule
from app.tenancy.provisioning import BootstrapInput, decode_payload, encode_payload
from app.tenancy.registry import RegistryBase, registry


class InitialConfig(RegistryBase):
    __tablename__ = "tenant_bootstrap_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Parameters(BootstrapInput):
    model_config = ConfigDict(extra="forbid")
    api_whatsapp: Literal["quepasa"] = "quepasa"
    score_valor_inicial: int = Field(default=1000, ge=-2147483648, le=2147483647)
    score_pontos_atraso_parcela: int = Field(default=15, ge=-2147483648, le=2147483647)
    score_pontos_atraso_quitacao_contrato: int = Field(default=30, ge=-2147483648, le=2147483647)
    score_pontos_pagamento_em_dia: int = Field(default=5, ge=-2147483648, le=2147483647)
    score_pontos_quitacao_em_dia: int = Field(default=20, ge=-2147483648, le=2147483647)
    score_pontos_negociacao: int = Field(default=0, ge=-2147483648, le=2147483647)
    whatsapp_cobranca_dias_antes: int = Field(default=1, ge=0, le=365)
    whatsapp_cobranca_dias_depois: int = Field(default=1, ge=0, le=365)
    whatsapp_cobranca_modelo: str | None = Field(default=None, max_length=500)
    regra_nono_dig_whats: list[ParameterNinthDigitRule] = Field(default_factory=list, max_length=100)


class Permission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resource_key: str = Field(min_length=1, max_length=120)
    resource_label: str | None = Field(default=None, max_length=160)
    can_read: bool = False
    can_create: bool = False
    can_update: bool = False
    can_delete: bool = False

    @model_validator(mode="after")
    def known_resource(self):
        resource = next((r for r in RESOURCE_CATALOG if r.resource_key == self.resource_key), None)
        if resource is None:
            raise ValueError("Recurso de permissão desconhecido")
        for action in ("read", "create", "update", "delete"):
            if getattr(self, f"can_{action}") and action not in resource.supported_actions:
                raise ValueError("Ação não disponível para este recurso")
        return self


class ProfileDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    nome: str = Field(min_length=1, max_length=80)
    descricao: str | None = Field(default=None, max_length=255)
    ativo: bool = True
    permissions: list[Permission] = Field(default_factory=list, max_length=500)

    @model_validator(mode="after")
    def unique_permissions(self):
        keys = [p.resource_key for p in self.permissions]
        if len(keys) != len(set(keys)):
            raise ValueError("Permissão duplicada no perfil")
        if self.nome == "Administrador" and not self.ativo:
            raise ValueError("O perfil Administrador precisa estar ativo")
        return self


ApiDefinition = create_model("ApiDefinition", __config__=ConfigDict(extra="forbid"), **{
    column.name: (str | None, Field(default=None, max_length=getattr(column.type, "length", None) or 100000))
    for column in ApiConfig.__table__.columns if column.name not in {"api_id", "usuario_id"}
})


class ConfigData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    parameters: Parameters
    profiles: list[ProfileDefinition] = Field(max_length=100)
    apis: list[ApiDefinition] = Field(max_length=100)

    @model_validator(mode="after")
    def unique_profiles(self):
        names = [p.nome for p in self.profiles]
        if len(names) != len(set(names)):
            raise ValueError("Nome de perfil duplicado")
        return self

    def snapshot(self):
        value = self.model_dump()
        value["parameters"].pop("usar_token_modelo", None)
        return value


class ConfigUpdate(ConfigData):
    version: int = Field(ge=1)

    def snapshot(self):
        value = super().snapshot()
        value.pop("version", None)
        return value


def bundled_config():
    document = json.loads(Path(__file__).with_name("initial_config.json").read_text(encoding="utf-8"))
    if document["format"] != 1:
        raise ValueError("Formato de configuração inicial incompatível")
    return ConfigData.model_validate(decode_payload(document["payload"])).snapshot()


async def ensure_config(db):
    # Serialize first insert and concurrent edits across API processes.
    if db.bind.dialect.name == "postgresql":
        await db.execute(text("SELECT pg_advisory_xact_lock(72419632)"))
    row = await db.get(InitialConfig, 1, populate_existing=True)
    if row is None:
        row = InitialConfig(id=1, version=1, payload=encode_payload(bundled_config()),
                            updated_at=int(time.time()), updated_by=None)
        db.add(row)
        await db.flush()
    return row


async def initialize_config():
    factory = registry.session_factory()
    async with registry.engine.begin() as connection:
        await connection.run_sync(lambda conn: InitialConfig.__table__.create(conn, checkfirst=True))
    async with factory() as db:
        await ensure_config(db)
        await db.commit()


async def read_initial_config():
    async with registry.session_factory()() as db:
        row = await ensure_config(db)
        snapshot = decode_payload(row.payload)
        snapshot["config_version"] = row.version
        await db.commit()
        return snapshot


def config_output(row):
    result = decode_payload(row.payload)
    result["has_token"] = bool(result["parameters"].get("token_api_whatsapp"))
    result["parameters"]["token_api_whatsapp"] = None
    return {**result, "version": row.version, "updated_at": row.updated_at, "updated_by": row.updated_by,
            "resources": [{"key": r.resource_key, "label": r.resource_label,
                           "actions": list(r.supported_actions)} for r in RESOURCE_CATALOG]}


async def save_config(db, data, admin):
    row = await ensure_config(db)
    if row.version != data.version:
        raise HTTPException(409, "A configuração foi alterada por outro usuário. Recarregue antes de salvar")
    snapshot = data.snapshot()
    if snapshot["parameters"]["token_api_whatsapp"] is None:
        snapshot["parameters"]["token_api_whatsapp"] = decode_payload(row.payload)["parameters"].get("token_api_whatsapp", "")
    row.payload = encode_payload(snapshot)
    row.version += 1
    row.updated_at, row.updated_by = int(time.time()), admin.login
    await db.commit()
    return config_output(row)
