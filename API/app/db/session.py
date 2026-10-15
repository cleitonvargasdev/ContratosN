from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.tenancy.context import current_tenant, tenant_key
from app.tenancy.registry import secret_from_env
from sqlalchemy.engine import make_url


engine = create_async_engine(settings.sqlalchemy_database_uri, future=True, echo=False)
_legacy_sessions = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
_tenant_sessions = {}


def AsyncSessionLocal() -> AsyncSession:
    key = tenant_key()
    tenant = current_tenant.get()
    if tenant is None:
        return _legacy_sessions()
    if key not in _tenant_sessions:
        url = make_url(secret_from_env(tenant.database_url_env))
        if url.get_backend_name() != "postgresql":
            raise ValueError("Tenant database must use PostgreSQL")
        if url.database in {settings.db_name, settings.tenant_registry_db_name}:
            raise ValueError("Tenant cannot use the source database or tenant registry")
        identity = (url.host, url.port or 5432, url.database)
        for factory in _tenant_sessions.values():
            other = factory.kw["bind"].url
            if identity == (other.host, other.port or 5432, other.database):
                raise ValueError("Different tenants cannot share a database")
        tenant_engine = create_async_engine(url.set(drivername="postgresql+asyncpg"), pool_pre_ping=True,
                                           pool_size=3, max_overflow=2)
        _tenant_sessions[key] = async_sessionmaker(tenant_engine, expire_on_commit=False)
    return _tenant_sessions[key](info={"tenant_id": key})


async def dispose_engines() -> None:
    for factory in _tenant_sessions.values():
        await factory.kw["bind"].dispose()
    _tenant_sessions.clear()
    await engine.dispose()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
