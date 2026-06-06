from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.supplier import Fornecedor


class SupplierRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_suppliers(
        self,
        *,
        nome: str | None,
        cpf_cnpj: str | None,
        ativo: bool | None,
        page: int,
        page_size: int,
    ) -> tuple[Sequence[Fornecedor], int]:
        stmt = select(Fornecedor)
        count_stmt = select(func.count()).select_from(Fornecedor)

        if nome:
            stmt = stmt.where(Fornecedor.nome.ilike(f"%{nome}%"))
            count_stmt = count_stmt.where(Fornecedor.nome.ilike(f"%{nome}%"))
        if cpf_cnpj:
            stmt = stmt.where(Fornecedor.cpf_cnpj.ilike(f"%{cpf_cnpj}%"))
            count_stmt = count_stmt.where(Fornecedor.cpf_cnpj.ilike(f"%{cpf_cnpj}%"))
        if ativo is not None:
            stmt = stmt.where(Fornecedor.ativo.is_(ativo))
            count_stmt = count_stmt.where(Fornecedor.ativo.is_(ativo))

        total = int((await self.session.execute(count_stmt)).scalar_one())
        result = await self.session.execute(
            stmt.order_by(Fornecedor.nome, Fornecedor.fornecedor_id).offset((page - 1) * page_size).limit(page_size)
        )
        return result.scalars().all(), total

    async def get_by_id(self, supplier_id: int) -> Fornecedor | None:
        return await self.session.get(Fornecedor, supplier_id)

    async def create(self, record: Fornecedor) -> Fornecedor:
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def update(self, record: Fornecedor) -> Fornecedor:
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def delete(self, record: Fornecedor) -> None:
        await self.session.delete(record)
        await self.session.commit()