from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, require_permission
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.access_control import PermissionResourceRead, ProfileCreate, ProfileRead, ProfileUpdate
from app.services.access_control_service import AccessControlService


router = APIRouter(dependencies=[Depends(get_current_active_user)])


def get_access_control_service(session: AsyncSession = Depends(get_db_session)) -> AccessControlService:
    return AccessControlService(session)


@router.get("/recursos", response_model=list[PermissionResourceRead], summary="Listar recursos de permissao")
async def list_resources(service: AccessControlService = Depends(get_access_control_service)) -> list[PermissionResourceRead]:
    return service.list_permission_resources()


@router.get("/perfis", response_model=list[ProfileRead], summary="Listar perfis")
async def list_profiles(
    term: Annotated[str | None, Query(description="Filtro por nome do perfil.")] = None,
    _: User = Depends(require_permission("perfis", "read")),
    service: AccessControlService = Depends(get_access_control_service),
) -> list[ProfileRead]:
    return await service.list_profiles(term)


@router.get("/perfis/{profile_id}", response_model=ProfileRead, summary="Buscar perfil")
async def get_profile(
    profile_id: int,
    _: User = Depends(require_permission("perfis", "read")),
    service: AccessControlService = Depends(get_access_control_service),
) -> ProfileRead:
    record = await service.get_profile(profile_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil nao encontrado")
    return record


@router.post("/perfis", response_model=ProfileRead, status_code=status.HTTP_201_CREATED, summary="Criar perfil")
async def create_profile(
    payload: ProfileCreate,
    _: User = Depends(require_permission("perfis", "create")),
    service: AccessControlService = Depends(get_access_control_service),
) -> ProfileRead:
    return await service.create_profile(payload)


@router.put("/perfis/{profile_id}", response_model=ProfileRead, summary="Atualizar perfil")
async def update_profile(
    profile_id: int,
    payload: ProfileUpdate,
    _: User = Depends(require_permission("perfis", "update")),
    service: AccessControlService = Depends(get_access_control_service),
) -> ProfileRead:
    record = await service.update_profile(profile_id, payload)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil nao encontrado")
    return record


@router.delete("/perfis/{profile_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir perfil")
async def delete_profile(
    profile_id: int,
    _: User = Depends(require_permission("perfis", "delete")),
    service: AccessControlService = Depends(get_access_control_service),
) -> Response:
    deleted = await service.delete_profile(profile_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil nao encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
