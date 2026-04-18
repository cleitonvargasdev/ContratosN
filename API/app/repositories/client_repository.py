from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Cliente
from app.schemas.client import ClientListParams


class ClientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self, params: ClientListParams) -> tuple[Sequence[Cliente], int]:
        filters = []

        if params.nome:
            filters.append(Cliente.nome.ilike(f"%{params.nome}%"))
        if params.cpf_cnpj:
            filters.append(Cliente.cpf_cnpj == params.cpf_cnpj)
        if params.endereco:
            filters.append(Cliente.endereco.ilike(f"%{params.endereco}%"))
        if params.ativo is not None:
            filters.append(Cliente.ativo == params.ativo)

        stmt = select(Cliente)
        count_stmt = select(func.count()).select_from(Cliente)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        stmt = stmt.order_by(Cliente.clientes_id).offset((params.page - 1) * params.page_size).limit(params.page_size)

        result = await self.session.execute(stmt)
        total = await self.session.scalar(count_stmt)
        return result.scalars().all(), int(total or 0)

    async def get_by_id(self, client_id: int) -> Cliente | None:
        result = await self.session.execute(select(Cliente).where(Cliente.clientes_id == client_id))
        return result.scalar_one_or_none()

    async def create(self, client: Cliente) -> Cliente:
        self.session.add(client)
        await self.session.commit()
        await self.session.refresh(client)
        return client

    async def update_fields(self, client: Cliente, values: dict[str, object]) -> Cliente:
        for field, value in values.items():
            setattr(client, field, value)
        await self.session.commit()
        await self.session.refresh(client)
        return client

    async def delete(self, client: Cliente) -> None:
        await self.session.delete(client)
        await self.session.commit()