"""Administrative CLI. No public tenant provisioning endpoint is exposed."""
import argparse
import asyncio
import re
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.tenancy.registry import RegistryBase, TenantDomain, TenantRecord, registry, secret_from_env


async def run(args):
    registry.session_factory()
    try:
        if args.action == "init":
            async with registry.engine.begin() as connection:
                await connection.run_sync(RegistryBase.metadata.create_all)
            print("Tabelas do registro central criadas.")
            return
        async with registry.session_factory()() as session:
            if args.action == "list":
                rows = (await session.scalars(select(TenantRecord).order_by(TenantRecord.id))).all()
                for row in rows:
                    print(f"{row.id}: {row.public_base_url} active={row.active} automations={row.automations_enabled} whatsapp={row.whatsapp_enabled}")
                return
            if args.action == "register":
                if not re.fullmatch(r"[a-z][a-z0-9_-]{0,62}", args.code):
                    raise ValueError("Codigo invalido")
                if await session.get(TenantRecord, args.code):
                    raise ValueError("Empresa ja existe; cadastro nao foi sobrescrito")
                hostname = args.domain.lower().rstrip(".")
                if not re.fullmatch(r"[a-z0-9]+(?:[.-][a-z0-9]+)*", hostname):
                    raise ValueError("Dominio invalido")
                url = make_url(secret_from_env(args.database_env))
                if url.get_backend_name() != "postgresql" or not url.database:
                    raise ValueError("A conexao deve indicar um banco PostgreSQL")
                if url.database in {settings.db_name, settings.tenant_registry_db_name}:
                    raise ValueError("Tenant nao pode usar o banco de origem nem o registro central")
                for row in (await session.scalars(select(TenantRecord))).all():
                    other = make_url(secret_from_env(row.database_url_env))
                    if (url.host, url.port or 5432, url.database) == (other.host, other.port or 5432, other.database):
                        raise ValueError("Banco ja utilizado por outra empresa")
                if len(secret_from_env(args.webhook_env)) < 32:
                    raise ValueError("Segredo do webhook deve ter pelo menos 32 caracteres")
                base_url = args.public_url or f"https://{hostname}"
                parsed = urlparse(base_url)
                if parsed.scheme not in {"http", "https"} or parsed.hostname != hostname or parsed.path not in {"", "/"} or parsed.query or parsed.fragment or parsed.username:
                    raise ValueError("URL publica deve corresponder ao dominio cadastrado")
                session.add(TenantRecord(id=args.code, company_code=args.code, database_url_env=args.database_env,
                                        public_base_url=base_url.rstrip("/"), webhook_secret_env=args.webhook_env,
                                        active=True, automations_enabled=False, whatsapp_enabled=False))
                await session.flush()
                session.add(TenantDomain(hostname=hostname, tenant_id=args.code))
            else:
                row = await session.get(TenantRecord, args.code)
                if row is None:
                    raise ValueError("Empresa nao encontrada")
                setattr(row, args.field, args.value == "on")
            await session.commit()
            print("Cadastro atualizado. Reinicie a API apos alteracoes administrativas para encerrar conexoes antigas.")
    finally:
        await registry.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("init")
    commands.add_parser("list")
    register = commands.add_parser("register")
    register.add_argument("--code", required=True)
    register.add_argument("--domain", required=True)
    register.add_argument("--database-env", required=True)
    register.add_argument("--webhook-env", required=True)
    register.add_argument("--public-url")
    update = commands.add_parser("set")
    update.add_argument("code")
    update.add_argument("field", choices=["active", "automations_enabled", "whatsapp_enabled"])
    update.add_argument("value", choices=["on", "off"])
    args = parser.parse_args()
    try:
        asyncio.run(run(args))
    except Exception as exc:
        # Never print a driver exception containing a connection URL/password.
        print(f"Operacao interrompida ({type(exc).__name__}). Confira cadastro, conectividade e variaveis de ambiente.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
