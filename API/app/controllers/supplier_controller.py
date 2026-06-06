from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, require_permission
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.supplier import SupplierCreate, SupplierListResponse, SupplierRead, SupplierUpdate
from app.services.supplier_service import SupplierService


router = APIRouter(dependencies=[Depends(get_current_active_user)])


def get_supplier_service(session: AsyncSession = Depends(get_db_session)) -> SupplierService:
    return SupplierService(session)


@router.get("/", response_model=SupplierListResponse, summary="Listar fornecedores")
async def list_suppliers(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    nome: Annotated[str | None, Query(description="Filtro por nome.")] = None,
    cpf_cnpj: Annotated[str | None, Query(description="Filtro por CPF/CNPJ.")] = None,
    ativo: Annotated[bool | None, Query(description="Filtro por situacao.")] = None,
    _: User = Depends(require_permission("fornecedores", "read")),
    service: SupplierService = Depends(get_supplier_service),
) -> SupplierListResponse:
    return await service.list_suppliers(nome=nome, cpf_cnpj=cpf_cnpj, ativo=ativo, page=page, page_size=page_size)


@router.get("/{supplier_id}", response_model=SupplierRead, summary="Buscar fornecedor")
async def get_supplier(
    supplier_id: int,
    _: User = Depends(require_permission("fornecedores", "read")),
    service: SupplierService = Depends(get_supplier_service),
) -> SupplierRead:
    record = await service.get_supplier(supplier_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor nao encontrado")
    return record


@router.post("/", response_model=SupplierRead, status_code=status.HTTP_201_CREATED, summary="Criar fornecedor")
async def create_supplier(
    payload: SupplierCreate,
    _: User = Depends(require_permission("fornecedores", "create")),
    service: SupplierService = Depends(get_supplier_service),
) -> SupplierRead:
    return await service.create_supplier(payload)


@router.put("/{supplier_id}", response_model=SupplierRead, summary="Atualizar fornecedor")
async def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    _: User = Depends(require_permission("fornecedores", "update")),
    service: SupplierService = Depends(get_supplier_service),
) -> SupplierRead:
    record = await service.update_supplier(supplier_id, payload)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor nao encontrado")
    return record


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir fornecedor")
async def delete_supplier(
    supplier_id: int,
    _: User = Depends(require_permission("fornecedores", "delete")),
    service: SupplierService = Depends(get_supplier_service),
) -> Response:
    deleted = await service.delete_supplier(supplier_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor nao encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)