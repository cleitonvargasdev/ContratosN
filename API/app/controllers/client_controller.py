from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db_session, get_pagination_params, require_permission
from app.models.user import User
from app.schemas.client import ClientCobradorOptionRead, ClientCreate, ClientListParams, ClientListResponse, ClientRead, ClientUpdate
from app.schemas.pagination import PaginationParams
from app.schemas.rules import RegraComissaoOptionRead, RegraJurosOptionRead
from app.services.client_service import ClientService
from app.services.rules_service import RulesService


router = APIRouter(dependencies=[Depends(get_current_active_user)])


def get_client_service(session: AsyncSession = Depends(get_db_session)) -> ClientService:
    return ClientService(session)


def get_rules_service(session: AsyncSession = Depends(get_db_session)) -> RulesService:
    return RulesService(session)


@router.get("/opcoes/regras-juros", response_model=list[RegraJurosOptionRead], summary="Listar regras de juros ativas")
async def list_active_regra_juros(
    _: User = Depends(require_permission("clientes", "read")),
    service: RulesService = Depends(get_rules_service),
) -> list[RegraJurosOptionRead]:
    return await service.list_active_regra_juros()


@router.get("/opcoes/regras-comissao", response_model=list[RegraComissaoOptionRead], summary="Listar regras de comissao ativas")
async def list_active_regra_comissao(
    _: User = Depends(require_permission("clientes", "read")),
    service: RulesService = Depends(get_rules_service),
) -> list[RegraComissaoOptionRead]:
    return await service.list_active_regra_comissao()


@router.get("/opcoes/cobradores", response_model=list[ClientCobradorOptionRead], summary="Listar usuarios ativos para cobrador")
async def list_active_cobradores(
    _: User = Depends(require_permission("clientes", "read")),
    service: ClientService = Depends(get_client_service),
) -> list[ClientCobradorOptionRead]:
    return await service.list_active_cobradores()


@router.get("/", response_model=ClientListResponse, summary="Listar clientes")
async def list_clients(
    pagination: PaginationParams = Depends(get_pagination_params),
    nome: Annotated[str | None, Query(description="Filtra por parte do nome.")] = None,
    cpf_cnpj: Annotated[str | None, Query(description="Filtra por CPF/CNPJ.")] = None,
    ativo: Annotated[bool | None, Query(description="Filtra por status ativo/inativo.")] = None,
    _: User = Depends(require_permission("clientes", "read")),
    service: ClientService = Depends(get_client_service),
) -> ClientListResponse:
    params = ClientListParams(page=pagination.page, page_size=pagination.page_size, nome=nome, cpf_cnpj=cpf_cnpj, ativo=ativo)
    return await service.list_clients(params)


@router.get("/{client_id}", response_model=ClientRead, summary="Buscar cliente por ID")
async def get_client(
    client_id: int,
    _: User = Depends(require_permission("clientes", "read")),
    service: ClientService = Depends(get_client_service),
) -> ClientRead:
    client = await service.get_client(client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente nao encontrado")
    return client


@router.post("/", response_model=ClientRead, status_code=status.HTTP_201_CREATED, summary="Criar cliente")
async def create_client(
    payload: ClientCreate,
    current_user: User = Depends(require_permission("clientes", "create")),
    service: ClientService = Depends(get_client_service),
) -> ClientRead:
    return await service.create_client(payload, current_user_id=current_user.id)


@router.put("/{client_id}", response_model=ClientRead, summary="Atualizar cliente")
async def update_client(
    client_id: int,
    payload: ClientUpdate,
    _: User = Depends(require_permission("clientes", "update")),
    service: ClientService = Depends(get_client_service),
) -> ClientRead:
    client = await service.update_client(client_id, payload)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente nao encontrado")
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir cliente")
async def delete_client(
    client_id: int,
    _: User = Depends(require_permission("clientes", "delete")),
    service: ClientService = Depends(get_client_service),
) -> Response:
    deleted = await service.delete_client(client_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente nao encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)