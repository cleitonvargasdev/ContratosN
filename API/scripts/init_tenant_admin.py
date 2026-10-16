"""Create the registry and initial platform administrator; never reset existing users."""
import asyncio

from sqlalchemy import create_engine, select, text

from app.core.config import settings
from app.core.security import hash_password
from app.tenancy.admin import AdminUser
from app.tenancy.registry import RegistryBase, registry
from app.tenancy.initial_config import ensure_config


async def seed_admin():
    registry.session_factory()
    try:
        async with registry.engine.begin() as connection:
            await connection.run_sync(RegistryBase.metadata.create_all)
        async with registry.session_factory()() as session:
            await ensure_config(session)
            await session.commit()
            if await session.scalar(select(AdminUser.id).limit(1)) is None:
                session.add(AdminUser(nome="Administrador", login="ADMIN", senha_hash=hash_password("Admin"), ativo=True))
                await session.commit()
                print("Usuário inicial ADMIN criado em cad_usuario.")
            else:
                print("Usuários já cadastrados; senhas preservadas.")
    finally:
        await registry.dispose()


def main():
    if settings.tenant_registry_db_name == settings.db_name:
        raise SystemExit("O banco de registro deve ser diferente do banco de negócio.")
    engine = create_engine(settings.admin_database_uri, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            name = settings.tenant_registry_db_name
            if not connection.scalar(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": name}):
                connection.exec_driver_sql("CREATE DATABASE " + engine.dialect.identifier_preparer.quote_identifier(name))
                print("Banco de registro criado.")
    finally:
        engine.dispose()
    asyncio.run(seed_admin())


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Inicialização interrompida ({type(exc).__name__}). Verifique a conexão e a permissão de criar banco.")
        raise SystemExit(1)
