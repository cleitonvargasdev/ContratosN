import logging
import hmac
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.services.whatsapp_chatbot_service import WhatsAppChatbotService
from app.tenancy.context import current_tenant, require_whatsapp_enabled
from app.tenancy.registry import secret_from_env


router = APIRouter()
logger = logging.getLogger(__name__)


def get_whatsapp_chatbot_service(session: AsyncSession = Depends(get_db_session)) -> WhatsAppChatbotService:
    return WhatsAppChatbotService(session)


@router.post("/webhook", summary="Receber eventos do QuePasa")
async def receive_quepasa_webhook(
    request: Request,
    payload: Any = Body(default=None),
    service: WhatsAppChatbotService = Depends(get_whatsapp_chatbot_service),
) -> dict[str, Any]:
    require_whatsapp_enabled()
    tenant = current_tenant.get()
    if tenant is not None:
        supplied = request.headers.get("X-Webhook-Secret") or request.query_params.get("key", "")
        expected = secret_from_env(tenant.webhook_secret_env)
        if not hmac.compare_digest(supplied, expected):
            raise HTTPException(401, "Webhook nao autorizado")
    logger.info("Webhook recebido. tenant=%s payload_type=%s", tenant.id if tenant else "legacy", type(payload).__name__)
    try:
        return await service.handle_webhook_event(request, payload)
    except HTTPException as exc:
        logger.exception("Falha no webhook do WhatsApp. status=%s detail=%s payload_type=%s", exc.status_code, exc.detail, type(payload).__name__)
        raise
