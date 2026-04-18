from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db_session, get_pagination_params, require_permission
from app.models.user import User
from app.schemas.negotiation import (
    NegotiationCreateRequest,
    NegotiationListParams,
    NegotiationListResponse,
    NegotiationRead,
    OpenContractForNegotiation,
)
from app.schemas.pagination import PaginationParams
from app.services.negotiation_report_service import NegotiationReportService
from app.services.negotiation_service import NegotiationService


router = APIRouter(dependencies=[Depends(get_current_active_user)])


def get_negotiation_service(session: AsyncSession = Depends(get_db_session)) -> NegotiationService:
    return NegotiationService(session)


def get_negotiation_report_service(session: AsyncSession = Depends(get_db_session)) -> NegotiationReportService:
    return NegotiationReportService(session)


@router.get("/", response_model=NegotiationListResponse, summary="Listar negociacoes")
async def list_negotiations(
    pagination: PaginationParams = Depends(get_pagination_params),
    cliente_nome: Annotated[str | None, Query(description="Filtra pelo nome do cliente.")] = None,
    contrato_gerado_id: Annotated[int | None, Query(description="Filtra pelo ID do contrato gerado.")] = None,
    _: User = Depends(require_permission("contratos", "read")),
    service: NegotiationService = Depends(get_negotiation_service),
) -> NegotiationListResponse:
    params = NegotiationListParams(
        page=pagination.page,
        page_size=pagination.page_size,
        cliente_nome=cliente_nome,
        contrato_gerado_id=contrato_gerado_id,
    )
    return await service.list_negotiations(params)


@router.get("/contratos-abertos/{cliente_id}", response_model=list[OpenContractForNegotiation], summary="Listar contratos abertos do cliente")
async def list_open_contracts(
    cliente_id: int,
    _: User = Depends(require_permission("contratos", "read")),
    service: NegotiationService = Depends(get_negotiation_service),
) -> list[OpenContractForNegotiation]:
    return await service.list_open_contracts(cliente_id)


@router.get("/{negotiation_id}", response_model=NegotiationRead, summary="Buscar negociacao por ID")
async def get_negotiation(
    negotiation_id: int,
    _: User = Depends(require_permission("contratos", "read")),
    service: NegotiationService = Depends(get_negotiation_service),
) -> NegotiationRead:
    result = await service.get_negotiation(negotiation_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negociacao nao encontrada")
    return result


@router.get("/{negotiation_id}/imprimir", summary="Imprimir negociacao")
async def print_negotiation(
    negotiation_id: int,
    _: User = Depends(require_permission("contratos", "read")),
    service: NegotiationReportService = Depends(get_negotiation_report_service),
) -> Response:
    pdf_bytes, filename = await service.generate_negotiation_pdf(negotiation_id)
    headers = {"Content-Disposition": f'inline; filename="{filename}"'}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.post("/", response_model=NegotiationRead, status_code=status.HTTP_201_CREATED, summary="Criar negociacao")
async def create_negotiation(
    payload: NegotiationCreateRequest,
    current_user: User = Depends(require_permission("contratos", "create")),
    service: NegotiationService = Depends(get_negotiation_service),
) -> NegotiationRead:
    return await service.create_negotiation(payload, current_user.id, current_user.nome or "")
