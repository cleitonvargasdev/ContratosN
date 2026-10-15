from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

from fastapi import HTTPException

from app.core.config import settings


@dataclass(frozen=True)
class Tenant:
    id: str
    company_code: str
    database_url_env: str
    public_base_url: str
    webhook_secret_env: str
    active: bool = True
    automations_enabled: bool = False
    whatsapp_enabled: bool = False


current_tenant: ContextVar[Tenant | None] = ContextVar("current_tenant", default=None)


def tenant_key() -> str:
    tenant = current_tenant.get()
    if tenant is not None:
        return tenant.id
    if settings.tenancy_enabled:
        raise HTTPException(403, "Empresa nao identificada")
    return "__legacy__"


@contextmanager
def tenant_scope(tenant: Tenant | None):
    token = current_tenant.set(tenant)
    try:
        yield
    finally:
        current_tenant.reset(token)


def validate_token_tenant(payload: dict) -> None:
    expected = tenant_key()
    if expected == "__legacy__":
        if payload.get("tenant_id") is not None:
            raise HTTPException(401, "Token de empresa invalido neste ambiente")
    elif payload.get("tenant_id") != expected:
        raise HTTPException(401, "Token nao pertence a esta empresa")


def public_base_url(fallback: str) -> str:
    tenant_key()  # Fail closed if multi-tenant context is missing.
    tenant = current_tenant.get()
    return (tenant.public_base_url if tenant else settings.public_api_base_url or fallback).rstrip("/")


def require_whatsapp_enabled() -> None:
    tenant_key()
    tenant = current_tenant.get()
    if tenant is not None and not tenant.whatsapp_enabled:
        raise HTTPException(403, "WhatsApp ainda nao habilitado para esta empresa")
