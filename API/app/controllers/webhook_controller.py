import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.services.whatsapp_chatbot_service import WhatsAppChatbotService


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
    try:
        return await service.handle_webhook_event(request, payload)
    except HTTPException as exc:
        logger.exception("Falha no webhook do WhatsApp. status=%s detail=%s payload_type=%s", exc.status_code, exc.detail, type(payload).__name__)
        raise