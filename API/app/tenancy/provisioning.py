"""Durable provisioning queue. Only the Ubuntu worker may execute infrastructure steps."""
import json
import time
import uuid
from pathlib import Path

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import ForeignKey, Integer, String, Text, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.core.secrets import decrypt_secret, encrypt_secret, is_encrypted_secret
from app.models.access_control import Profile, ProfilePermission
from app.models.api_config import ApiConfig
from app.models.parameter import Parametro
from app.tenancy.registry import RegistryBase, TenantRecord, registry, secret_from_env


class ProvisionJob(RegistryBase):
    __tablename__ = "tenant_provision_jobs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), unique=True)
    state: Mapped[str] = mapped_column(String(20), default="queued")
    step: Mapped[str] = mapped_column(String(40), default="queued")
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[int] = mapped_column(Integer, default=lambda: int(time.time()))
    updated_at: Mapped[int] = mapped_column(Integer, default=lambda: int(time.time()))


SCORE_FIELDS = (
    "score_valor_inicial", "score_pontos_atraso_parcela", "score_pontos_atraso_quitacao_contrato",
    "score_pontos_pagamento_em_dia", "score_pontos_quitacao_em_dia", "score_pontos_negociacao",
)
WHATSAPP_FIELDS = ("usuario_api_whatsapp", "sufixo_whatsapp", "pais_whatsapp", "msg_renovacao", "msg_negociacao", "msg_campanha")


class BootstrapInput(BaseModel):
    nome_fantasia: str = Field(default="Sua empresa", min_length=1, max_length=150)
    razao_social: str = Field(default="Sua razão social", min_length=1, max_length=150)
    usuario_api_whatsapp: str = Field(default="", max_length=100)
    token_api_whatsapp: str | None = Field(default=None, max_length=120)
    usar_token_modelo: bool = True
    sufixo_whatsapp: str = Field(default="@s.whatsapp.net", min_length=1, max_length=30)
    pais_whatsapp: int = Field(default=55, ge=1, le=999)
    msg_renovacao: str = Field(default="", max_length=10000)
    msg_negociacao: str = Field(default="", max_length=10000)
    msg_campanha: str = Field(default="", max_length=10000)

    @field_validator("nome_fantasia", "razao_social", "sufixo_whatsapp")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Preencha o campo")
        return value.strip()


def job_output(job):
    return {key: getattr(job, key) for key in ("id", "tenant_id", "state", "step", "error", "created_at", "updated_at")}


def encode_payload(data):
    return encrypt_secret(json.dumps(data, ensure_ascii=False))


def decode_payload(value):
    decoded = decrypt_secret(value)
    if not decoded or is_encrypted_secret(decoded):
        raise ValueError("Não foi possível abrir a configuração protegida")
    return json.loads(decoded)


async def read_template():
    """Explicit allowlist: no users, customers, contracts, movements or identities."""
    url = settings.sqlalchemy_database_uri
    if settings.tenant_template_code:
        source = await registry.find(company_code=settings.tenant_template_code)
        if source is None:
            raise HTTPException(503, "Empresa modelo não encontrada")
        url = secret_from_env(source.database_url_env)
    engine = create_async_engine(make_url(url).set(drivername="postgresql+asyncpg"))
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            from sqlalchemy import text
            await session.execute(text("SET TRANSACTION READ ONLY"))
            parameter = await session.scalar(select(Parametro).order_by(Parametro.parametros_id).limit(1))
            if parameter is None:
                raise HTTPException(503, "Cadastre os parâmetros na empresa modelo primeiro")
            params = {key: getattr(parameter, key) for key in SCORE_FIELDS + WHATSAPP_FIELDS}
            params.update(api_whatsapp="quepasa", regra_nono_dig_whats=parameter.regra_nono_dig_whats or [],
                          whatsapp_cobranca_dias_antes=parameter.whatsapp_cobranca_dias_antes,
                          whatsapp_cobranca_dias_depois=parameter.whatsapp_cobranca_dias_depois,
                          whatsapp_cobranca_modelo=parameter.whatsapp_cobranca_modelo)
            token = decrypt_secret(parameter.token_api_whatsapp)
            if is_encrypted_secret(token):
                raise HTTPException(503, "A chave de criptografia não abre o token do modelo")
            params["token_api_whatsapp"] = token or ""
            profiles = []
            permission_rows = (await session.execute(select(ProfilePermission.__table__))).mappings().all()
            for profile in (await session.execute(select(Profile.__table__))).mappings().all():
                profiles.append({"nome": profile.nome, "descricao": profile.descricao, "ativo": profile.ativo,
                    "permissions": [{key: p[key] for key in ("resource_key", "resource_label", "can_read", "can_create", "can_update", "can_delete")}
                        for p in permission_rows if p["perfil_id"] == profile.id]})
            apis = [{column.name: getattr(row, column.name) for column in ApiConfig.__table__.columns
                     if column.name not in {"api_id", "usuario_id"}}
                    for row in (await session.scalars(select(ApiConfig).order_by(ApiConfig.api_id))).all()]
            return {"parameters": params, "profiles": profiles, "apis": apis}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503, "Não foi possível ler os padrões da empresa modelo. Confira a configuração do servidor")
    finally:
        await engine.dispose()


def worker_available():
    if not settings.tenant_provisioning_enabled or not settings.tenancy_enabled or not settings.tenant_runtime_dir:
        return False
    path = Path(settings.tenant_runtime_dir) / "worker-heartbeat"
    try:
        return time.time() - path.stat().st_mtime < 90
    except OSError:
        return False


def new_job(tenant_id, snapshot, bootstrap):
    options = bootstrap.model_dump(exclude={"usar_token_modelo", "token_api_whatsapp"})
    params = {**snapshot["parameters"], **options}
    params["token_api_whatsapp"] = (snapshot["parameters"].get("token_api_whatsapp", "")
        if bootstrap.usar_token_modelo else (bootstrap.token_api_whatsapp or ""))
    params["token_api_whatsapp"] = encrypt_secret(params["token_api_whatsapp"])
    snapshot = {**snapshot, "parameters": params}
    return ProvisionJob(id=uuid.uuid4().hex, tenant_id=tenant_id, payload=encode_payload(snapshot), state="queued", step="queued")
