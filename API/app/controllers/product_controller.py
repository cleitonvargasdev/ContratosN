from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_pagination_params, require_permission
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.pagination import PaginationParams
from app.schemas.product import (
    BrandCreate,
    BrandListParams,
    BrandListResponse,
    BrandOptionRead,
    BrandRead,
    BrandUpdate,
    ProductCreate,
    ProductListParams,
    ProductListResponse,
    ProductRead,
    ProductUpdate,
)
from app.services.product_service import ProductService


brands_router = APIRouter(dependencies=[Depends(get_current_active_user)])
products_router = APIRouter(dependencies=[Depends(get_current_active_user)])


def get_product_service(session: AsyncSession = Depends(get_db_session)) -> ProductService:
    return ProductService(session)


@brands_router.get("/opcoes", response_model=list[BrandOptionRead], summary="Listar marcas para selecao")
async def list_brand_options(
    _: User = Depends(require_permission("marcas", "read")),
    service: ProductService = Depends(get_product_service),
) -> list[BrandOptionRead]:
    return await service.list_brand_options()


@brands_router.get("/", response_model=BrandListResponse, summary="Listar marcas")
async def list_brands(
    pagination: PaginationParams = Depends(get_pagination_params),
    descricao: Annotated[str | None, Query(description="Filtra por parte da descricao da marca.")] = None,
    _: User = Depends(require_permission("marcas", "read")),
    service: ProductService = Depends(get_product_service),
) -> BrandListResponse:
    params = BrandListParams(page=pagination.page, page_size=pagination.page_size, descricao=descricao)
    return await service.list_brands(params)


@brands_router.get("/{marca_id}", response_model=BrandRead, summary="Buscar marca por ID")
async def get_brand(
    marca_id: int,
    _: User = Depends(require_permission("marcas", "read")),
    service: ProductService = Depends(get_product_service),
) -> BrandRead:
    record = await service.get_brand(marca_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marca nao encontrada")
    return record


@brands_router.post("/", response_model=BrandRead, status_code=status.HTTP_201_CREATED, summary="Criar marca")
async def create_brand(
    payload: BrandCreate,
    _: User = Depends(require_permission("marcas", "create")),
    service: ProductService = Depends(get_product_service),
) -> BrandRead:
    return await service.create_brand(payload)


@brands_router.put("/{marca_id}", response_model=BrandRead, summary="Atualizar marca")
async def update_brand(
    marca_id: int,
    payload: BrandUpdate,
    _: User = Depends(require_permission("marcas", "update")),
    service: ProductService = Depends(get_product_service),
) -> BrandRead:
    record = await service.update_brand(marca_id, payload)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marca nao encontrada")
    return record


@brands_router.delete("/{marca_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir marca")
async def delete_brand(
    marca_id: int,
    _: User = Depends(require_permission("marcas", "delete")),
    service: ProductService = Depends(get_product_service),
) -> Response:
    deleted = await service.delete_brand(marca_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marca nao encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@products_router.get("/", response_model=ProductListResponse, summary="Listar produtos")
async def list_products(
    pagination: PaginationParams = Depends(get_pagination_params),
    descricao: Annotated[str | None, Query(description="Filtra por parte da descricao do produto.")] = None,
    marca_id: Annotated[int | None, Query(description="Filtra pelo identificador da marca.")] = None,
    ativo: Annotated[bool | None, Query(description="Filtra por status ativo/inativo.")] = None,
    _: User = Depends(require_permission("produtos", "read")),
    service: ProductService = Depends(get_product_service),
) -> ProductListResponse:
    params = ProductListParams(page=pagination.page, page_size=pagination.page_size, descricao=descricao, marca_id=marca_id, ativo=ativo)
    return await service.list_products(params)


@products_router.get("/{produto_id}", response_model=ProductRead, summary="Buscar produto por ID")
async def get_product(
    produto_id: int,
    _: User = Depends(require_permission("produtos", "read")),
    service: ProductService = Depends(get_product_service),
) -> ProductRead:
    record = await service.get_product(produto_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado")
    return record


@products_router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED, summary="Criar produto")
async def create_product(
    payload: ProductCreate,
    _: User = Depends(require_permission("produtos", "create")),
    service: ProductService = Depends(get_product_service),
) -> ProductRead:
    return await service.create_product(payload)


@products_router.put("/{produto_id}", response_model=ProductRead, summary="Atualizar produto")
async def update_product(
    produto_id: int,
    payload: ProductUpdate,
    _: User = Depends(require_permission("produtos", "update")),
    service: ProductService = Depends(get_product_service),
) -> ProductRead:
    record = await service.update_product(produto_id, payload)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado")
    return record


@products_router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir produto")
async def delete_product(
    produto_id: int,
    _: User = Depends(require_permission("produtos", "delete")),
    service: ProductService = Depends(get_product_service),
) -> Response:
    deleted = await service.delete_product(produto_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto nao encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)