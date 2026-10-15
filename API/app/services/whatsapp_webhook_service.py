"""Reconcile the current tenant's callback without deleting other integrations."""
import asyncio
import logging
from urllib.parse import urlencode
from weakref import WeakValueDictionary

import httpx

from app.core.config import settings
from app.tenancy.context import current_tenant, require_whatsapp_enabled
from app.tenancy.registry import secret_from_env

logger = logging.getLogger(__name__)
_locks: WeakValueDictionary[str, asyncio.Lock] = WeakValueDictionary()


async def ensure_whatsapp_webhook(client_factory, session_key: str) -> bool | None:
    tenant = current_tenant.get()
    if tenant is None:
        return None
    require_whatsapp_enabled()
    try:
        if not session_key:
            raise ValueError("Missing session token")
        callback = tenant.public_base_url.rstrip("/") + "/webhooks/webhook?" + urlencode(
            {"key": secret_from_env(tenant.webhook_secret_env)}
        )
        base = settings.quepasa_apiwpp_url.rstrip("/")
        headers = {"Accept": "application/json", "X-QUEPASA-TOKEN": session_key}
        lock = _locks.setdefault(tenant.id, asyncio.Lock())
        async with lock:
            async with client_factory() as client:
                if callback in await _get_webhooks(client, base, headers):
                    return True
                response = await client.post(
                    base + "/api/webhook", headers=headers, json={"url": callback}
                )
                response.raise_for_status()
                # Do not trust a successful HTTP status alone: confirm persistence.
                if callback not in await _get_webhooks(client, base, headers):
                    raise ValueError("Webhook was not persisted")
        return True
    except Exception as exc:
        # Provider responses and exception messages may contain callback secrets.
        logger.warning("Webhook pendente. tenant=%s erro=%s", tenant.id, type(exc).__name__)
        return False


async def _get_webhooks(client: httpx.AsyncClient, base: str, headers: dict) -> list[str]:
    response = await client.get(base + "/webhook", headers=headers)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise ValueError("Webhook query failed")
    hooks = payload.get("webhooks")
    if not isinstance(hooks, list) or any(
        not isinstance(hook, dict) or not isinstance(hook.get("url"), str)
        for hook in hooks
    ):
        raise ValueError("Unexpected webhook response")
    return [hook["url"] for hook in hooks]
