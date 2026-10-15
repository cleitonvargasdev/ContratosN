import asyncio
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.tenancy.admin import AdminSession, AdminUser, router, session_dependency
from app.tenancy.middleware import TenantMiddleware
from app.tenancy.registry import RegistryBase, registry
from scripts.init_tenant_admin import seed_admin


@pytest.fixture
def panel(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'registry.db').as_posix()}")
    factory = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(registry, "engine", engine)
    monkeypatch.setattr(registry, "sessions", factory)
    monkeypatch.setattr(settings, "tenancy_enabled", True)

    async def init():
        async with engine.begin() as conn:
            await conn.run_sync(RegistryBase.metadata.create_all)
        async with factory() as session:
            session.add(AdminUser(nome="Administrador", login="ADMIN", senha_hash=hash_password("Admin"), ativo=True))
            await session.commit()

    asyncio.run(init())
    app = FastAPI()
    app.add_middleware(TenantMiddleware)
    app.include_router(router)

    async def db():
        async with factory() as session:
            yield session

    app.dependency_overrides[session_dependency] = db
    with TestClient(app) as client:
        yield client, factory
    asyncio.run(engine.dispose())


def authenticate(client, login="ADMIN", senha="Admin"):
    result = client.post("/api/platform/auth/login", json={"login": login, "senha": senha})
    assert result.status_code == 200, result.text
    return {"Authorization": "Bearer " + result.json()["access_token"]}


def tenant_payload(code="cv"):
    return {"code": code, "domains": [f"{code}.example.test"], "public_base_url": f"https://{code}.example.test",
            "database_url_env": f"TENANT_{code.upper()}_DATABASE_URL",
            "webhook_secret_env": f"TENANT_{code.upper()}_WEBHOOK_SECRET", "active": True}


def test_identity_isolation_and_logout(panel):
    client, factory = panel
    assert client.get("/api/platform/tenants").status_code == 401
    business_token = jwt.encode({"sub": "1", "tenant_id": "cv", "exp": int(time.time()) + 3600}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    assert client.get("/api/platform/usuarios", headers={"Authorization": "Bearer " + business_token}).status_code == 401
    headers = authenticate(client, "admin")
    assert client.get("/api/platform/auth/me", headers=headers).json()["login"] == "ADMIN"
    assert client.get("/api/platform/tenants", headers=headers).json() == []
    assert client.get("/api/platform/usuarios", headers=headers).json() == [{"id": 1, "nome": "Administrador", "login": "ADMIN", "ativo": True}]
    assert client.post("/api/platform/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/platform/auth/me", headers=headers).status_code == 401


def test_users_password_revocation_and_disable(panel):
    client, _ = panel
    admin = authenticate(client)
    new_user = {"nome": "Operador", "login": "gestor", "senha": "Segredo123", "ativo": True}
    response = client.post("/api/platform/usuarios", json=new_user, headers=admin)
    assert response.status_code == 201
    uid = response.json()["id"]
    assert response.json()["login"] == "GESTOR"
    assert "senha_hash" not in response.json()
    assert client.post("/api/platform/usuarios", json=new_user, headers=admin).status_code == 409
    operator = authenticate(client, "GESTOR", "Segredo123")
    assert client.put(f"/api/platform/usuarios/{uid}", json={"nome": "Operador", "ativo": True, "senha": "OutraSenha"}, headers=admin).status_code == 200
    assert client.get("/api/platform/auth/me", headers=operator).status_code == 401
    operator = authenticate(client, "gestor", "OutraSenha")
    assert client.put(f"/api/platform/usuarios/{uid}", json={"nome": "Operador", "ativo": False}, headers=admin).status_code == 200
    assert client.get("/api/platform/auth/me", headers=operator).status_code == 401
    assert client.post("/api/platform/auth/login", json={"login": "gestor", "senha": "OutraSenha"}).status_code == 401
    assert client.put("/api/platform/usuarios/1", json={"nome": "Admin", "ativo": False}, headers=admin).status_code == 422


def test_tenant_registration_update_and_uniqueness(panel, monkeypatch):
    client, _ = panel
    headers = authenticate(client)
    monkeypatch.setenv("TENANT_CV_DATABASE_URL", "postgresql://user:secret@localhost/cv_test")
    monkeypatch.setenv("TENANT_CV_WEBHOOK_SECRET", "x" * 32)
    data = tenant_payload()
    data["domains"].append("alias.example.test")
    response = client.post("/api/platform/tenants", json=data, headers=headers)
    assert response.status_code == 201, response.text
    assert "secret@" not in response.text
    assert response.json()["automations_enabled"] is False
    assert client.get("/api/platform/tenants", headers=headers).json()[0]["domains"] == ["alias.example.test", "cv.example.test"]
    # Same database under another environment name must still be rejected.
    monkeypatch.setenv("TENANT_BC_DATABASE_URL", "postgresql://other:password@localhost:5432/cv_test")
    monkeypatch.setenv("TENANT_BC_WEBHOOK_SECRET", "y" * 32)
    assert client.post("/api/platform/tenants", json=tenant_payload("bc"), headers=headers).status_code == 409
    monkeypatch.setenv("TENANT_BC_DATABASE_URL", "postgresql://other:password@localhost/bc_test")
    bc = tenant_payload("bc")
    bc["domains"] = ["cv.example.test"]
    bc["public_base_url"] = "https://cv.example.test"
    assert client.post("/api/platform/tenants", json=bc, headers=headers).status_code == 409
    assert len(client.get("/api/platform/tenants", headers=headers).json()) == 1
    data.update(active=False, whatsapp_enabled=True)
    assert client.put("/api/platform/tenants/cv", json=data, headers=headers).status_code == 200
    assert client.get("/api/platform/tenants", headers=headers).json()[0]["active"] is False
    data["database_url_env"] = "TENANT_BC_DATABASE_URL"
    assert client.put("/api/platform/tenants/cv", json=data, headers=headers).status_code == 422


def test_invalid_tenants_and_no_secrets_in_errors(panel, monkeypatch):
    client, _ = panel
    headers = authenticate(client)
    data = tenant_payload()
    monkeypatch.setenv("TENANT_CV_DATABASE_URL", "postgresql://u:secret@localhost/" + settings.tenant_registry_db_name)
    monkeypatch.setenv("TENANT_CV_WEBHOOK_SECRET", "x" * 32)
    result = client.post("/api/platform/tenants", json=data, headers=headers)
    assert result.status_code == 422
    assert "secret@" not in result.text
    data["public_base_url"] = "https://unregistered.example.test"
    assert client.post("/api/platform/tenants", json=data, headers=headers).status_code == 422
    data = tenant_payload()
    data["domains"] = ["https://cv.example.test"]
    assert client.post("/api/platform/tenants", json=data, headers=headers).status_code == 422


def test_lockout_and_expired_session(panel):
    client, factory = panel
    headers = authenticate(client)

    async def expire():
        async with factory() as session:
            row = await session.scalar(select(AdminSession))
            assert row.token_hash not in headers["Authorization"]
            row.expires_at = 1
            await session.commit()
    asyncio.run(expire())
    assert client.get("/api/platform/auth/me", headers=headers).status_code == 401
    for _ in range(5):
        assert client.post("/api/platform/auth/login", json={"login": "ADMIN", "senha": "wrong"}).status_code == 401
    assert client.post("/api/platform/auth/login", json={"login": "ADMIN", "senha": "Admin"}).status_code == 429


def test_bootstrap_is_idempotent_and_preserves_password(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'seed.db').as_posix()}")
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def noop():
        pass

    monkeypatch.setattr(registry, "engine", engine)
    monkeypatch.setattr(registry, "sessions", factory)
    monkeypatch.setattr(registry, "dispose", noop)

    async def check():
        await seed_admin()
        async with factory() as session:
            admin = await session.scalar(select(AdminUser))
            assert admin.login == "ADMIN"
            assert admin.senha_hash != "Admin"
            admin.senha_hash = hash_password("changed")
            await session.commit()
            changed_hash = admin.senha_hash
        await seed_admin()
        async with factory() as session:
            rows = (await session.scalars(select(AdminUser))).all()
            assert len(rows) == 1
            assert rows[0].senha_hash == changed_hash
        await engine.dispose()
    asyncio.run(check())
