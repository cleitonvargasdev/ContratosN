import os
import re
from pathlib import Path

from dotenv import dotenv_values
from fastapi import HTTPException
from sqlalchemy import Boolean, ForeignKey, String, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import ENV_FILE, ENV_LOCAL_FILE, settings
from app.tenancy.context import Tenant


class RegistryBase(DeclarativeBase):
    pass


class TenantRecord(RegistryBase):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    company_code: Mapped[str] = mapped_column(String(64), unique=True)
    database_url_env: Mapped[str] = mapped_column(String(128), unique=True)
    public_base_url: Mapped[str] = mapped_column(String(255))
    webhook_secret_env: Mapped[str] = mapped_column(String(128), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    automations_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    def as_tenant(self) -> Tenant:
        return Tenant(**{field: getattr(self, field) for field in Tenant.__dataclass_fields__})


class TenantDomain(RegistryBase):
    __tablename__ = "tenant_domains"
    hostname: Mapped[str] = mapped_column(String(255), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)


def secret_from_env(name: str) -> str:
    if not re.fullmatch(r"TENANT_[A-Z0-9_]+", name):
        raise HTTPException(503, "Referencia de configuracao da empresa invalida")
    managed = {}
    if settings.tenant_runtime_dir:
        secret_file = Path(settings.tenant_runtime_dir) / "secrets" / f"{name}.secret"
        if secret_file.is_file():
            managed[name] = secret_file.read_text(encoding="utf-8").strip()
    values = {**managed, **dotenv_values(ENV_FILE), **dotenv_values(ENV_LOCAL_FILE), **os.environ}
    value = values.get(name)
    if not value:
        raise HTTPException(503, "Configuracao da empresa indisponivel")
    return value


class TenantRegistry:
    def __init__(self):
        self.engine = None
        self.sessions = None

    def session_factory(self):
        if self.sessions is None:
            self.engine = create_async_engine(
                settings.database_url("postgresql+asyncpg", settings.tenant_registry_db_name),
                pool_pre_ping=True, pool_size=2, max_overflow=3,
            )
            self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        return self.sessions

    async def find(self, *, hostname=None, company_code=None, tenant_id=None) -> Tenant | None:
        query = select(TenantRecord)
        if hostname is not None:
            query = query.join(TenantDomain).where(TenantDomain.hostname == hostname)
        elif company_code is not None:
            query = query.where(TenantRecord.company_code == company_code)
        elif tenant_id is not None:
            query = query.where(TenantRecord.id == tenant_id)
        else:
            raise ValueError("Tenant lookup requires an identifier")
        async with self.session_factory()() as session:
            row = await session.scalar(query)
            return row.as_tenant() if row else None

    async def list_active(self) -> list[Tenant]:
        async with self.session_factory()() as session:
            rows = (await session.scalars(select(TenantRecord).where(TenantRecord.active.is_(True)))).all()
            return [row.as_tenant() for row in rows]

    async def dispose(self):
        if self.engine is not None:
            await self.engine.dispose()
        self.engine = self.sessions = None


registry = TenantRegistry()
