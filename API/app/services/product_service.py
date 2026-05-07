from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.product_repository import ProductRepository
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


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = ProductRepository(session)

    async def list_brands(self, params: BrandListParams) -> BrandListResponse:
        items, total = await self.repository.list_brands(params)
        return BrandListResponse(items=[BrandRead.model_validate(item) for item in items], total=total, page=params.page, page_size=params.page_size)

    async def list_brand_options(self) -> list[BrandOptionRead]:
        return [BrandOptionRead.model_validate(item) for item in await self.repository.list_brand_options()]

    async def get_brand(self, marca_id: int) -> BrandRead | None:
        record = await self.repository.get_brand_by_id(marca_id)
        return BrandRead.model_validate(record) if record else None

    async def create_brand(self, payload: BrandCreate) -> BrandRead:
        data = self._normalize_brand_payload(payload.model_dump())
        await self._ensure_brand_description_is_available(data["descricao"])
        record = await self.repository.create_brand(data)
        return BrandRead.model_validate(record)

    async def update_brand(self, marca_id: int, payload: BrandUpdate) -> BrandRead | None:
        record = await self.repository.get_brand_by_id(marca_id)
        if record is None:
            return None

        data = self._normalize_brand_payload(payload.model_dump(exclude_unset=True), partial=True)
        descricao = data.get("descricao")
        if descricao is not None and descricao.lower() != record.descricao.lower():
            await self._ensure_brand_description_is_available(descricao)

        saved = await self.repository.update_brand(record, data)
        return BrandRead.model_validate(saved)

    async def delete_brand(self, marca_id: int) -> bool:
        record = await self.repository.get_brand_by_id(marca_id)
        if record is None:
            return False
        if await self.repository.count_products_by_brand(marca_id) > 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Marca vinculada a produtos e nao pode ser removida")
        await self.repository.delete_brand(record)
        return True

    async def list_products(self, params: ProductListParams) -> ProductListResponse:
        items, total = await self.repository.list_products(params)
        return ProductListResponse(items=[ProductRead.model_validate(item) for item in items], total=total, page=params.page, page_size=params.page_size)

    async def get_product(self, produto_id: int) -> ProductRead | None:
        record = await self.repository.get_product_by_id(produto_id)
        return ProductRead.model_validate(record) if record else None

    async def create_product(self, payload: ProductCreate) -> ProductRead:
        data = await self._normalize_product_payload(payload.model_dump())
        record = await self.repository.create_product(data)
        return ProductRead.model_validate(record)

    async def update_product(self, produto_id: int, payload: ProductUpdate) -> ProductRead | None:
        record = await self.repository.get_product_by_id(produto_id)
        if record is None:
            return None

        data = await self._normalize_product_payload(payload.model_dump(exclude_unset=True), partial=True)
        saved = await self.repository.update_product(record, data)
        return ProductRead.model_validate(saved)

    async def delete_product(self, produto_id: int) -> bool:
        record = await self.repository.get_product_by_id(produto_id)
        if record is None:
            return False
        await self.repository.delete_product(record)
        return True

    async def _ensure_brand_description_is_available(self, descricao: str) -> None:
        if await self.repository.get_brand_by_description(descricao):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Marca ja cadastrada")

    def _normalize_brand_payload(self, values: dict[str, object], partial: bool = False) -> dict[str, object]:
        descricao = values.get("descricao")
        if not partial and descricao is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Descricao da marca obrigatoria")
        if descricao is not None and not str(descricao).strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Descricao da marca obrigatoria")
        return values

    async def _normalize_product_payload(self, values: dict[str, object], partial: bool = False) -> dict[str, object]:
        descricao = values.get("descricao")
        if not partial and descricao is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Descricao do produto obrigatoria")
        if descricao is not None and not str(descricao).strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Descricao do produto obrigatoria")

        for field, message in (("valor_compra", "Valor de compra invalido"), ("valor_venda", "Valor de venda invalido")):
            if values.get(field) is not None and float(values[field]) < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
            if values.get(field) is not None:
                values[field] = self._round_currency(float(values[field]))

        for field, message in (("garantia", "Garantia invalida"), ("estoque", "Estoque invalido")):
            if values.get(field) is not None and int(values[field]) < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        if values.get("marca_id") is not None:
            marca = await self.repository.get_brand_by_id(int(values["marca_id"]))
            if marca is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Marca nao encontrada")

        return values

    @staticmethod
    def _round_currency(value: float) -> float:
        return round(value + 1e-9, 2)