from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db_session, get_pagination_params, require_permission
from app.models.user import User
from app.schemas.api_config import ApiConfigCreate, ApiConfigListParams, ApiConfigListResponse, ApiConfigRead, ApiConfigUpdate
from app.schemas.pagination import PaginationParams
from app.services.api_config_service import ApiConfigService


router = APIRouter(dependencies=[Depends(get_current_active_user)])


def get_api_config_service(session: AsyncSession = Depends(get_db_session)) -> ApiConfigService:
    return ApiConfigService(session)


@router.get("/", response_model=ApiConfigListResponse, summary="Listar APIs")
async def list_api_configs(
    pagination: PaginationParams = Depends(get_pagination_params),
    nome_api: Annotated[str | None, Query(description="Filtra por parte do nome da API.")] = None,
    usuario_id: Annotated[int | None, Query(description="Filtra pelo usuario vinculado.")] = None,
    _: User = Depends(require_permission("apis", "read")),
    service: ApiConfigService = Depends(get_api_config_service),
) -> ApiConfigListResponse:
    params = ApiConfigListParams(page=pagination.page, page_size=pagination.page_size, nome_api=nome_api, usuario_id=usuario_id)
    return await service.list_api_configs(params)


@router.get("/{api_id}", response_model=ApiConfigRead, summary="Buscar API por ID")
async def get_api_config(
    api_id: int,
    _: User = Depends(require_permission("apis", "read")),
    service: ApiConfigService = Depends(get_api_config_service),
) -> ApiConfigRead:
    record = await service.get_api_config(api_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API nao encontrada")
    return record


@router.post("/", response_model=ApiConfigRead, status_code=status.HTTP_201_CREATED, summary="Criar API")
async def create_api_config(
    payload: ApiConfigCreate,
    _: User = Depends(require_permission("apis", "create")),
    service: ApiConfigService = Depends(get_api_config_service),
) -> ApiConfigRead:
    return await service.create_api_config(payload)


@router.put("/{api_id}", response_model=ApiConfigRead, summary="Atualizar API")
async def update_api_config(
    api_id: int,
    payload: ApiConfigUpdate,
    _: User = Depends(require_permission("apis", "update")),
    service: ApiConfigService = Depends(get_api_config_service),
) -> ApiConfigRead:
    record = await service.update_api_config(api_id, payload)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API nao encontrada")
    return record


@router.delete("/{api_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir API")
async def delete_api_config(
    api_id: int,
    _: User = Depends(require_permission("apis", "delete")),
    service: ApiConfigService = Depends(get_api_config_service),
) -> Response:
    deleted = await service.delete_api_config(api_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API nao encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)