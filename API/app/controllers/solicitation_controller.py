from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db_session, get_pagination_params, require_permission
from app.models.user import User
from app.schemas.pagination import PaginationParams
from app.schemas.solicitation import (
    SolicitationCompleteContractRequest,
    SolicitationDetailRead,
    SolicitationLinkClientRequest,
    SolicitationListParams,
    SolicitationListResponse,
    SolicitationPendingCountRead,
    SolicitationRead,
)
from app.services.solicitation_service import SolicitationService


router = APIRouter(dependencies=[Depends(get_current_active_user)])


def get_solicitation_service(session: AsyncSession = Depends(get_db_session)) -> SolicitationService:
    return SolicitationService(session)


@router.get("/pendentes/contagem", response_model=SolicitationPendingCountRead, summary="Contar solicitacoes pendentes")
async def get_pending_solicitation_count(
    _: User = Depends(require_permission("solicitacoes", "read")),
    service: SolicitationService = Depends(get_solicitation_service),
) -> SolicitationPendingCountRead:
    return await service.get_pending_count()


@router.get("/", response_model=SolicitationListResponse, summary="Listar solicitacoes")
async def list_solicitations(
    pagination: PaginationParams = Depends(get_pagination_params),
    status_filter: Annotated[str | None, Query(alias="status", description="Filtra pelo status da solicitacao.")] = None,
    tipo: Annotated[str | None, Query(description="Filtra pelo tipo da solicitacao.")] = None,
    cliente_id: Annotated[int | None, Query(description="Filtra pelo cliente vinculado.")] = None,
    termo: Annotated[str | None, Query(description="Busca por nome, telefone ou CPF/CNPJ.")] = None,
    _: User = Depends(require_permission("solicitacoes", "read")),
    service: SolicitationService = Depends(get_solicitation_service),
) -> SolicitationListResponse:
    params = SolicitationListParams(
        page=pagination.page,
        page_size=pagination.page_size,
        status=status_filter,
        tipo=tipo,
        cliente_id=cliente_id,
        termo=termo,
    )
    return await service.list_solicitations(params)


@router.get("/{solicitation_id}", response_model=SolicitationDetailRead, summary="Buscar solicitacao por ID")
async def get_solicitation(
    solicitation_id: int,
    _: User = Depends(require_permission("solicitacoes", "read")),
    service: SolicitationService = Depends(get_solicitation_service),
) -> SolicitationDetailRead:
    solicitation = await service.get_solicitation_detail(solicitation_id)
    if solicitation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitacao nao encontrada")
    return solicitation


@router.post("/{solicitation_id}/vincular-cliente", response_model=SolicitationRead, summary="Vincular cliente a solicitacao")
async def link_client_to_solicitation(
    solicitation_id: int,
    payload: SolicitationLinkClientRequest,
    _: User = Depends(require_permission("solicitacoes", "update")),
    service: SolicitationService = Depends(get_solicitation_service),
) -> SolicitationRead:
    solicitation = await service.link_client(solicitation_id, payload)
    if solicitation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitacao nao encontrada")
    return solicitation


@router.post("/{solicitation_id}/concluir-contrato", response_model=SolicitationRead, summary="Concluir solicitacao com contrato gerado")
async def complete_solicitation_with_contract(
    solicitation_id: int,
    payload: SolicitationCompleteContractRequest,
    current_user: User = Depends(require_permission("solicitacoes", "update")),
    service: SolicitationService = Depends(get_solicitation_service),
) -> SolicitationRead:
    solicitation = await service.complete_with_contract(solicitation_id, payload, current_user_id=current_user.id)
    if solicitation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitacao nao encontrada")
    return solicitation


@router.post("/{solicitation_id}/rejeitar", response_model=SolicitationRead, summary="Marcar solicitacao como rejeitada")
async def reject_solicitation(
    solicitation_id: int,
    current_user: User = Depends(require_permission("solicitacoes", "update")),
    service: SolicitationService = Depends(get_solicitation_service),
) -> SolicitationRead:
    solicitation = await service.reject(solicitation_id, current_user_id=current_user.id)
    if solicitation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitacao nao encontrada")
    return solicitation
