from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db_session
from app.schemas.whatsapp import WhatsAppConnectionStatusRead, WhatsAppQrCodeRead
from app.services.whatsapp_service import WhatsAppService


router = APIRouter(dependencies=[Depends(get_current_active_user)])


def get_whatsapp_service(session: AsyncSession = Depends(get_db_session)) -> WhatsAppService:
	return WhatsAppService(session)


@router.get("/status", response_model=WhatsAppConnectionStatusRead, summary="Consultar status da conexao WhatsApp")
async def get_whatsapp_status(service: WhatsAppService = Depends(get_whatsapp_service)) -> WhatsAppConnectionStatusRead:
	return WhatsAppConnectionStatusRead.model_validate(await service.get_connection_status())


@router.post("/conectar", response_model=WhatsAppQrCodeRead, summary="Gerar QR Code para conectar WhatsApp")
async def connect_whatsapp(service: WhatsAppService = Depends(get_whatsapp_service)) -> WhatsAppQrCodeRead:
	return WhatsAppQrCodeRead.model_validate(await service.create_session_qr_code())
