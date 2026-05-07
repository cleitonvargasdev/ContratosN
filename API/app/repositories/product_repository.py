from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Marca, Produto
from app.schemas.product import BrandListParams, ProductListParams


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_brands(self, params: BrandListParams) -> tuple[Sequence[Marca], int]:
        filters = []
        if params.descricao:
            filters.append(Marca.descricao.ilike(f"%{params.descricao}%"))

        stmt = select(Marca)
        count_stmt = select(func.count()).select_from(Marca)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        stmt = stmt.order_by(Marca.marca_id).offset((params.page - 1) * params.page_size).limit(params.page_size)
        result = await self.session.execute(stmt)
        total = await self.session.scalar(count_stmt)
        return result.scalars().all(), int(total or 0)

    async def list_brand_options(self) -> Sequence[Marca]:
        result = await self.session.execute(select(Marca).order_by(Marca.descricao))
        return result.scalars().all()

    async def get_brand_by_id(self, marca_id: int) -> Marca | None:
        return await self.session.get(Marca, marca_id)

    async def get_brand_by_description(self, descricao: str) -> Marca | None:
        result = await self.session.execute(select(Marca).where(func.lower(Marca.descricao) == descricao.lower()))
        return result.scalar_one_or_none()

    async def create_brand(self, payload: dict[str, object]) -> Marca:
        record = Marca(**payload)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def update_brand(self, record: Marca, payload: dict[str, object]) -> Marca:
        for field, value in payload.items():
            setattr(record, field, value)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def delete_brand(self, record: Marca) -> None:
        await self.session.delete(record)
        await self.session.commit()

    async def count_products_by_brand(self, marca_id: int) -> int:
        total = await self.session.scalar(select(func.count()).select_from(Produto).where(Produto.marca_id == marca_id))
        return int(total or 0)

    async def list_products(self, params: ProductListParams) -> tuple[Sequence[Produto], int]:
        filters = []
        if params.descricao:
            filters.append(Produto.descricao.ilike(f"%{params.descricao}%"))
        if params.marca_id is not None:
            filters.append(Produto.marca_id == params.marca_id)
        if params.ativo is not None:
            filters.append(Produto.ativo == params.ativo)

        stmt = select(Produto).options(selectinload(Produto.marca))
        count_stmt = select(func.count()).select_from(Produto)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        stmt = stmt.order_by(Produto.produto_id).offset((params.page - 1) * params.page_size).limit(params.page_size)
        result = await self.session.execute(stmt)
        total = await self.session.scalar(count_stmt)
        return result.scalars().all(), int(total or 0)

    async def get_product_by_id(self, produto_id: int) -> Produto | None:
        stmt = select(Produto).options(selectinload(Produto.marca)).where(Produto.produto_id == produto_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_product(self, payload: dict[str, object]) -> Produto:
        record = Produto(**payload)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return await self.get_product_by_id(record.produto_id) or record

    async def update_product(self, record: Produto, payload: dict[str, object]) -> Produto:
        for field, value in payload.items():
            setattr(record, field, value)
        await self.session.commit()
        await self.session.refresh(record)
        return await self.get_product_by_id(record.produto_id) or record

    async def delete_product(self, record: Produto) -> None:
        await self.session.delete(record)
        await self.session.commit()