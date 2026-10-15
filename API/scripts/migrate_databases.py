"""Apply the existing business migrations to each active tenant, never to the registry."""
import asyncio

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

from app.core.config import ROOT_DIR, settings
from app.tenancy.registry import registry, secret_from_env


def migrate(url: str) -> None:
    config = Config(str(ROOT_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT_DIR / "alembic"))
    config.attributes["database_url"] = make_url(url).set(drivername="postgresql+psycopg2").render_as_string(hide_password=False)
    command.upgrade(config, "head")


async def tenant_urls() -> list[tuple[str, str]]:
    try:
        return [(tenant.id, secret_from_env(tenant.database_url_env)) for tenant in await registry.list_active()]
    finally:
        await registry.dispose()


def main():
    targets = asyncio.run(tenant_urls()) if settings.tenancy_enabled else [("legacy", settings.sqlalchemy_sync_database_uri)]
    if not targets:
        raise SystemExit("Nenhuma empresa ativa cadastrada; inicializacao interrompida.")
    identities = set()
    for tenant_id, url in targets:
        parsed = make_url(url)
        identity = (parsed.host, parsed.port or 5432, parsed.database)
        if settings.tenancy_enabled and parsed.database in {settings.db_name, settings.tenant_registry_db_name}:
            raise SystemExit("Banco de tenant aponta para origem ou registro central; corrija a configuracao.")
        if identity in identities:
            raise SystemExit("Empresas configuradas para o mesmo banco; corrija a configuracao.")
        identities.add(identity)
    for tenant_id, url in targets:
        print(f"Aplicando migracoes: {tenant_id}", flush=True)
        migrate(url)


if __name__ == "__main__":
    main()
