from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db_session, get_pagination_params
from app.schemas.pagination import PaginationParams
from app.schemas.whatsapp import WhatsAppConnectionStatusRead, WhatsAppQrCodeRead
from app.schemas.whatsapp_dispatch import (
	WhatsAppDispatchBatchListParams,
	WhatsAppDispatchBatchListResponse,
	WhatsAppDispatchItemListResponse,
)
from app.services.whatsapp_dispatch_service import WhatsAppDispatchService
from app.services.whatsapp_service import WhatsAppService


router = APIRouter(dependencies=[Depends(get_current_active_user)])


def get_whatsapp_service(session: AsyncSession = Depends(get_db_session)) -> WhatsAppService:
	return WhatsAppService(session)


def get_whatsapp_dispatch_service(session: AsyncSession = Depends(get_db_session)) -> WhatsAppDispatchService:
	return WhatsAppDispatchService(session)


@router.get("/status", response_model=WhatsAppConnectionStatusRead, summary="Consultar status da conexao WhatsApp")
async def get_whatsapp_status(service: WhatsAppService = Depends(get_whatsapp_service)) -> WhatsAppConnectionStatusRead:
	return WhatsAppConnectionStatusRead.model_validate(await service.get_connection_status())


@router.post("/conectar", response_model=WhatsAppQrCodeRead, summary="Gerar QR Code para conectar WhatsApp")
async def connect_whatsapp(service: WhatsAppService = Depends(get_whatsapp_service)) -> WhatsAppQrCodeRead:
	return WhatsAppQrCodeRead.model_validate(await service.create_session_qr_code())


@router.get("/envios", response_model=WhatsAppDispatchBatchListResponse, summary="Listar lotes de envios WhatsApp")
async def list_whatsapp_dispatch_batches(
	pagination: PaginationParams = Depends(get_pagination_params),
	data_inicial: date | None = Query(default=None, description="Filtra a data inicial da execução."),
	data_final: date | None = Query(default=None, description="Filtra a data final da execução."),
	service: WhatsAppDispatchService = Depends(get_whatsapp_dispatch_service),
) -> WhatsAppDispatchBatchListResponse:
	params = WhatsAppDispatchBatchListParams(
		page=pagination.page,
		page_size=pagination.page_size,
		data_inicial=data_inicial,
		data_final=data_final,
	)
	return await service.list_batches(params)


@router.get("/envios/{batch_id}/itens", response_model=WhatsAppDispatchItemListResponse, summary="Listar itens de um lote WhatsApp")
async def list_whatsapp_dispatch_items(
	batch_id: int,
	pagination: PaginationParams = Depends(get_pagination_params),
	service: WhatsAppDispatchService = Depends(get_whatsapp_dispatch_service),
) -> WhatsAppDispatchItemListResponse:
	return await service.list_batch_items(batch_id, pagination.page, pagination.page_size)


@router.delete("/envios/{batch_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir lote de envio WhatsApp")
async def delete_whatsapp_dispatch_batch(
	batch_id: int,
	service: WhatsAppDispatchService = Depends(get_whatsapp_dispatch_service),
) -> Response:
	deleted = await service.delete_batch(batch_id)
	if not deleted:
		return Response(status_code=status.HTTP_404_NOT_FOUND)
	return Response(status_code=status.HTTP_204_NO_CONTENT)
