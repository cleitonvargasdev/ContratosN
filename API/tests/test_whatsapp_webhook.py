import asyncio
import json
from dataclasses import replace
from unittest.mock import AsyncMock

import httpx
import pytest

from app.core.config import settings
from app.services.whatsapp_service import WhatsAppService
from app.services.whatsapp_webhook_service import ensure_whatsapp_webhook
from app.tenancy.context import Tenant, tenant_scope


CV = Tenant("cv", "cv", "TENANT_CV_DATABASE_URL", "https://cv.example.test",
            "TENANT_CV_WEBHOOK_SECRET", whatsapp_enabled=True)
BC = replace(CV, id="bc", company_code="bc", public_base_url="https://bc.example.test",
             webhook_secret_env="TENANT_BC_WEBHOOK_SECRET")


@pytest.fixture(autouse=True)
def environment(monkeypatch):
    monkeypatch.setenv("TENANT_CV_WEBHOOK_SECRET", "cv-secret")
    monkeypatch.setenv("TENANT_BC_WEBHOOK_SECRET", "bc-secret")
    monkeypatch.setattr(settings, "quepasa_apiwpp_url", "https://provider.example.test")


def factory(handler):
    return lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler))


def test_missing_webhook_is_registered_once_and_other_hooks_preserved():
    hooks = [{"url": "https://other.example.test/integration"}]
    posts = []

    def handler(request):
        assert request.headers["X-QUEPASA-TOKEN"] == "cv-token"
        if request.method == "GET":
            assert request.url.path == "/webhook"
            return httpx.Response(200, json={"success": True, "webhooks": hooks})
        assert request.method == "POST" and request.url.path == "/api/webhook"
        body = json.loads(request.content)
        posts.append(body)
        hooks.append(body)
        return httpx.Response(200, json={"success": True})

    async def run():
        with tenant_scope(CV):
            results = await asyncio.gather(*[
                ensure_whatsapp_webhook(factory(handler), "cv-token") for _ in range(3)
            ])
        assert results == [True, True, True]

    asyncio.run(run())
    assert posts == [{"url": "https://cv.example.test/webhooks/webhook?key=cv-secret"}]
    assert len(hooks) == 2


def test_existing_callback_does_not_write():
    def handler(request):
        assert request.method == "GET"
        return httpx.Response(200, json={"success": True, "webhooks": [
            {"url": "https://cv.example.test/webhooks/webhook?key=cv-secret", "success": "date"}
        ]})

    with tenant_scope(CV):
        assert asyncio.run(ensure_whatsapp_webhook(factory(handler), "cv-token")) is True


@pytest.mark.parametrize("code,payload", [
    (401, {"error": "secret-must-not-leak"}),
    (500, {}),
    (200, {"success": False, "webhooks": []}),
    (200, {"success": True}),
    (200, {"success": True, "webhooks": [None]}),
    (200, []),
])
def test_failed_or_unknown_query_never_registers(code, payload, caplog):
    def handler(request):
        assert request.method == "GET"
        return httpx.Response(code, json=payload)

    with tenant_scope(CV):
        assert asyncio.run(ensure_whatsapp_webhook(factory(handler), "cv-token")) is False
    assert "secret-must-not-leak" not in caplog.text
    assert "cv-token" not in caplog.text
    assert "cv-secret" not in caplog.text


def test_post_success_without_persisted_callback_is_not_ready():
    def handler(request):
        return httpx.Response(200, json={"success": True, "webhooks": []})

    with tenant_scope(CV):
        assert asyncio.run(ensure_whatsapp_webhook(factory(handler), "cv-token")) is False


@pytest.mark.parametrize("failure", ["timeout", "post_error"])
def test_provider_failure_is_pending_without_leaking_secrets(failure, caplog):
    def handler(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("secret-must-not-leak", request=request)
        if request.method == "POST":
            return httpx.Response(500, text="secret-must-not-leak")
        return httpx.Response(200, json={"success": True, "webhooks": []})

    with tenant_scope(CV):
        assert asyncio.run(ensure_whatsapp_webhook(factory(handler), "cv-token")) is False
    assert "secret-must-not-leak" not in caplog.text


def test_tenants_use_their_own_token_domain_and_secret():
    stored = {}

    def handler(request):
        token = request.headers["X-QUEPASA-TOKEN"]
        if request.method == "POST":
            stored[token] = json.loads(request.content)
        return httpx.Response(200, json={"success": True, "webhooks":
                                        [stored[token]] if token in stored else []})

    async def run():
        for tenant in (CV, BC):
            with tenant_scope(tenant):
                assert await ensure_whatsapp_webhook(factory(handler), tenant.id + "-token")

    asyncio.run(run())
    assert stored == {
        "cv-token": {"url": "https://cv.example.test/webhooks/webhook?key=cv-secret"},
        "bc-token": {"url": "https://bc.example.test/webhooks/webhook?key=bc-secret"},
    }


def test_legacy_does_not_contact_provider():
    with tenant_scope(None):
        assert asyncio.run(ensure_whatsapp_webhook(None, "token")) is None


def test_disabled_tenant_cannot_register():
    from fastapi import HTTPException
    with tenant_scope(replace(CV, whatsapp_enabled=False)), pytest.raises(HTTPException):
        asyncio.run(ensure_whatsapp_webhook(None, "token"))


@pytest.mark.parametrize("connected", [True, False])
def test_status_reconciles_only_connected_sessions_and_reports_pending(monkeypatch, connected):
    service = WhatsAppService.__new__(WhatsAppService)
    service._get_whatsapp_config = AsyncMock(return_value={
        "session_key": "cv-token", "expected_phone": None, "expected_phones": [],
        "country_code": "55", "ninth_digit_rules": [],
    })
    service._get_api_health_status = AsyncMock(return_value={
        "available": True, "status": "online", "message": "online",
    })
    service._get_info_payload = AsyncMock(return_value={"connected": connected})
    reconcile = AsyncMock(return_value=False)
    monkeypatch.setattr("app.services.whatsapp_service.ensure_whatsapp_webhook", reconcile)
    with tenant_scope(CV):
        result = asyncio.run(service.get_connection_status())
    assert result["connected"] is connected
    if connected:
        reconcile.assert_awaited_once()
        assert result["webhook_ready"] is False
        assert "Atualizar status" in result["message"]
    else:
        reconcile.assert_not_awaited()
        assert result["webhook_ready"] is None
