import asyncio
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette.websockets import WebSocketDisconnect

from app.api.dependencies import get_current_active_user
from app.controllers.auth_controller import router as auth_router
from app.controllers.contract_controller import _create_contract_pdf_token, _validate_contract_pdf_token
from app.controllers.webhook_controller import receive_quepasa_webhook
from app.controllers.user_controller import ws_router as users_ws_router
from app.core.config import settings
from app.core.security import create_access_token, hash_api_key_value, hash_password
from app.db import session as db
from app.realtime.chat_events import ChatEventBroker
from app.realtime.user_events import UserEventBroker, user_event_broker
from app.repositories.user_repository import UserRepository
from app.tenancy.context import Tenant, current_tenant, public_base_url, tenant_key, tenant_scope
from app.tenancy.admin import AdminUser, AdminSession
from app.tenancy.events import TenantEventBroker
from app.tenancy.middleware import TenantMiddleware
from app.tenancy.registry import RegistryBase, TenantDomain, TenantRecord, TenantRegistry, registry


CV = Tenant("cv", "cv", "TENANT_CV_DATABASE_URL", "https://cv.example.test", "TENANT_CV_WEBHOOK_SECRET")
BC = Tenant("bc", "bc", "TENANT_BC_DATABASE_URL", "https://bc.example.test", "TENANT_BC_WEBHOOK_SECRET")


@pytest.fixture
def environment(monkeypatch):
    monkeypatch.setattr(settings, "tenancy_enabled", True)
    monkeypatch.setattr(settings, "tenant_api_hosts", "api.example.test")
    tenants = {"cv": CV, "bc": BC}

    async def find(*, hostname=None, company_code=None, tenant_id=None):
        key = company_code or tenant_id
        if hostname is not None:
            key = {"cv.example.test": "cv", "bc.example.test": "bc"}.get(hostname)
        return tenants.get(key)

    monkeypatch.setattr(registry, "find", find)
    monkeypatch.setattr(user_event_broker, "brokers", {})
    return tenants


@pytest.fixture
def application(environment, monkeypatch, tmp_path):
    engines = {}
    factories = {}
    for key in ("cv", "bc"):
        engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / (key + '.db')).as_posix()}")
        engines[key] = engine
        factories[key] = async_sessionmaker(engine, expire_on_commit=False)

    async def initialize():
        for key, engine in engines.items():
            async with engine.begin() as connection:
                await connection.execute(text("CREATE TABLE probe (id INTEGER PRIMARY KEY, company TEXT, value INTEGER)"))
                await connection.execute(text("INSERT INTO probe VALUES (1, :company, 0)"), {"company": key})

    asyncio.run(initialize())
    monkeypatch.setattr(db, "_tenant_sessions", factories)
    password_hash = hash_password("test-password")

    async def user_by_login(self, login):
        if login != "same-user":
            return None
        return SimpleNamespace(id=1, login=login, ativo=True, senha_hash=password_hash,
                               permissions=[SimpleNamespace(resource_key="acesso_web", can_read=True)])

    monkeypatch.setattr(UserRepository, "get_by_login", user_by_login)
    app = FastAPI()
    app.add_middleware(TenantMiddleware)
    app.include_router(auth_router, prefix="/api/v1/auth")
    app.include_router(users_ws_router, prefix="/api/v1/usuarios")

    @app.get("/probe")
    async def probe(user=Depends(get_current_active_user), session=Depends(db.get_db_session)):
        return dict((await session.execute(text("SELECT * FROM probe WHERE id=1"))).mappings().one())

    @app.post("/probe")
    async def update(user=Depends(get_current_active_user), session=Depends(db.get_db_session)):
        await session.execute(text("UPDATE probe SET value=value+1 WHERE id=1"))
        await session.commit()
        await user_event_broker.broadcast("updated", user_id=1)
        return {"tenant": tenant_key()}

    @app.get("/api/v1/contratos/publico/1/imprimir")
    async def pdf(token: str):
        _validate_contract_pdf_token(token, 1)
        return {"tenant": tenant_key()}

    yield app

    async def close():
        for engine in engines.values():
            await engine.dispose()

    asyncio.run(close())


def login(client, company=None):
    body = {"username": "same-user", "password": "test-password"}
    if company:
        body["company_code"] = company
    response = client.post("/api/v1/auth/login", data=body)
    assert response.status_code == 200, response.text
    return response.json()


def authorization(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_same_ids_read_and_write_only_the_selected_database(application):
    cv = TestClient(application, base_url=CV.public_base_url)
    bc = TestClient(application, base_url=BC.public_base_url)
    cv_tokens, bc_tokens = login(cv), login(bc)
    assert cv.post("/probe", headers=authorization(cv_tokens)).status_code == 200
    assert cv.get("/probe", headers=authorization(cv_tokens)).json() == {"id": 1, "company": "cv", "value": 1}
    assert bc.get("/probe", headers=authorization(bc_tokens)).json() == {"id": 1, "company": "bc", "value": 0}
    assert bc.get("/probe", headers=authorization(cv_tokens)).status_code == 401
    claims = jwt.decode(cv_tokens["access_token"], settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert claims["tenant_id"] == "cv"
    assert current_tenant.get() is None


def test_refresh_mobile_and_unknown_hosts(application, environment):
    cv = TestClient(application, base_url=CV.public_base_url)
    bc = TestClient(application, base_url=BC.public_base_url)
    mobile = TestClient(application, base_url="https://api.example.test")
    unknown = TestClient(application, base_url="https://unknown.example.test")
    tokens = login(mobile, "cv")
    assert mobile.get("/probe", headers=authorization(tokens)).json()["company"] == "cv"
    assert mobile.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 200
    assert cv.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 200
    assert bc.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
    assert unknown.get("/probe", headers={**authorization(tokens), "X-Forwarded-Host": "cv.example.test"}).status_code == 404
    assert cv.post("/api/v1/auth/login", data={"company_code": "bc", "username": "same-user", "password": "test-password"}).status_code == 403
    environment["cv"] = replace(CV, active=False)
    assert cv.get("/probe", headers=authorization(tokens)).status_code == 403
    assert mobile.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 403


def test_legacy_and_expired_tokens_rejected(application):
    client = TestClient(application, base_url=CV.public_base_url)
    old = jwt.encode({"sub": "same-user", "token_type": "access"}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    assert client.get("/probe", headers={"Authorization": f"Bearer {old}"}).status_code == 401
    with tenant_scope(CV):
        expired = create_access_token({"sub": "same-user", "token_type": "access"}, settings.jwt_secret_key, settings.jwt_algorithm, -1)
    assert client.get("/probe", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_public_pdf_token_cannot_cross_tenants(application):
    with tenant_scope(CV):
        token = _create_contract_pdf_token(1)
        assert public_base_url("https://wrong.example.test") == CV.public_base_url
    path = f"/api/v1/contratos/publico/1/imprimir?token={token}"
    assert TestClient(application, base_url=CV.public_base_url).get(path).status_code == 200
    assert TestClient(application, base_url=BC.public_base_url).get(path).status_code == 401
    assert TestClient(application, base_url="https://api.example.test").get(path).status_code == 200


def test_websocket_rejects_foreign_token_and_receives_own_events(application):
    client = TestClient(application, base_url=CV.public_base_url)
    tokens = login(client)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"wss://bc.example.test/api/v1/usuarios/ws?token={tokens['access_token']}"):
            pass
    with client.websocket_connect(f"wss://cv.example.test/api/v1/usuarios/ws?token={tokens['access_token']}") as socket:
        assert socket.receive_json()["event"] == "connected"
        assert client.post("/probe", headers=authorization(tokens)).status_code == 200
        assert socket.receive_json()["event"] == "updated"


def test_keys_are_tenant_scoped_and_missing_context_fails(environment, monkeypatch):
    with tenant_scope(CV):
        cv_hash = hash_api_key_value("copied-key", "secret")
    with tenant_scope(BC):
        bc_hash = hash_api_key_value("copied-key", "secret")
    assert cv_hash != bc_hash
    with pytest.raises(Exception, match="Empresa nao identificada"):
        db.AsyncSessionLocal()
    monkeypatch.setattr(settings, "tenancy_enabled", False)
    assert hash_api_key_value("copied-key", "secret") not in {cv_hash, bc_hash}


def test_brokers_never_deliver_between_tenants(environment):
    class Socket:
        def __init__(self):
            self.messages = []
        async def accept(self):
            pass
        async def send_json(self, value):
            self.messages.append(value)

    async def run():
        chat, users = TenantEventBroker(ChatEventBroker), TenantEventBroker(UserEventBroker)
        cv_socket, bc_socket = Socket(), Socket()
        with tenant_scope(CV):
            await chat.connect(1, cv_socket)
            await users.connect(cv_socket)
        with tenant_scope(BC):
            assert not chat.is_user_online(1)
            await chat.connect(1, bc_socket)
            await users.connect(bc_socket)
        cv_socket.messages.clear()
        bc_socket.messages.clear()
        with tenant_scope(CV):
            await chat.send_to_user(1, {"event": "private"})
            await users.broadcast("updated")
        assert len(cv_socket.messages) == 2
        assert bc_socket.messages == []

    asyncio.run(run())


def test_webhook_requires_tenant_secret_and_enable_flag(environment, monkeypatch):
    monkeypatch.setenv("TENANT_CV_WEBHOOK_SECRET", "cv-secret-" * 8)
    service = SimpleNamespace(handle_webhook_event=AsyncMock(return_value={"success": True}))

    def request(secret):
        return Request({"type": "http", "method": "POST", "path": "/webhooks/webhook", "query_string": b"",
                        "headers": [(b"x-webhook-secret", secret.encode())]})

    async def run():
        with tenant_scope(CV):
            with pytest.raises(Exception, match="WhatsApp ainda nao habilitado"):
                await receive_quepasa_webhook(request("cv-secret-" * 8), {}, service)
        with tenant_scope(replace(CV, whatsapp_enabled=True)):
            with pytest.raises(Exception, match="Webhook nao autorizado"):
                await receive_quepasa_webhook(request("other-company-secret"), {}, service)
            await receive_quepasa_webhook(request("cv-secret-" * 8), {}, service)
        assert service.handle_webhook_event.await_count == 1

    asyncio.run(run())


def test_registry_uses_separate_metadata_and_preserves_inactive_status(tmp_path):
    async def run():
        instance = TenantRegistry()
        instance.engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'registry.db').as_posix()}")
        instance.sessions = async_sessionmaker(instance.engine, expire_on_commit=False)
        try:
            async with instance.engine.begin() as connection:
                await connection.run_sync(RegistryBase.metadata.create_all)
            async with instance.sessions() as session:
                session.add(TenantRecord(**{**CV.__dict__, "active": False}))
                await session.flush()
                session.add(TenantDomain(hostname="cv.example.test", tenant_id="cv"))
                await session.commit()
            assert (await instance.find(hostname="cv.example.test")).active is False
            assert (await instance.find(company_code="cv")).id == "cv"
            assert await instance.find(hostname="unknown.test") is None
            assert await instance.list_active() == []
            assert set(RegistryBase.metadata.tables) == {"tenants", "tenant_domains", "cad_usuario", "tenant_admin_sessions", "tenant_provision_jobs"}
        finally:
            await instance.dispose()
    asyncio.run(run())


def test_concurrent_requests_keep_their_own_context(environment):
    async def inspect(tenant):
        with tenant_scope(tenant):
            await asyncio.sleep(0)
            return tenant_key(), public_base_url("ignored")

    async def run():
        return await asyncio.gather(inspect(CV), inspect(BC))

    assert asyncio.run(run()) == [("cv", CV.public_base_url), ("bc", BC.public_base_url)]
    assert current_tenant.get() is None


def test_scheduler_isolates_failures_and_skips_disabled_automations(application, monkeypatch):
    from app.main import _run_for_tenants

    disabled = replace(CV, id="disabled", automations_enabled=False)
    monkeypatch.setattr(registry, "list_active", AsyncMock(return_value=[disabled, replace(CV, automations_enabled=True), replace(BC, automations_enabled=True)]))
    seen = []

    async def action(session):
        seen.append(tenant_key())
        if tenant_key() == "cv":
            raise RuntimeError("One company's failure must not stop the next company")
        assert (await session.execute(text("SELECT company FROM probe"))).scalar_one() == "bc"

    asyncio.run(_run_for_tenants(action, automation=True))
    assert seen == ["cv", "bc"]
    assert current_tenant.get() is None
