from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.user import User
from app.schemas.contract import ContractListParams


class ContractRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self, params: ContractListParams) -> tuple[Sequence[Contrato], int]:
        filters = []
        cobrador = aliased(User)

        if params.contratos_id is not None:
            filters.append(Contrato.contratos_id == params.contratos_id)
        elif params.cliente_nome:
            filters.append(Cliente.nome.ilike(f"%{params.cliente_nome}%"))
        if params.contratos_id is None and params.cobrador_nome:
            filters.append(cobrador.nome.ilike(f"%{params.cobrador_nome}%"))
        if params.contratos_id is None and params.quitado is not None:
            filters.append(Contrato.quitado == params.quitado)

        stmt = (
            select(Contrato, Cliente.nome, Cliente.celular01, Cliente.telefone, cobrador.nome)
            .outerjoin(Cliente, Cliente.clientes_id == Contrato.cliente_id)
            .outerjoin(cobrador, cobrador.id == Contrato.usuario_id_vendedor)
        )
        count_stmt = (
            select(func.count())
            .select_from(Contrato)
            .outerjoin(Cliente, Cliente.clientes_id == Contrato.cliente_id)
            .outerjoin(cobrador, cobrador.id == Contrato.usuario_id_vendedor)
        )

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        stmt = stmt.order_by(Contrato.contratos_id.desc()).offset((params.page - 1) * params.page_size).limit(params.page_size)

        result = await self.session.execute(stmt)
        total = await self.session.scalar(count_stmt)
        rows = result.all()
        contracts: list[Contrato] = []
        for contract, client_name, client_mobile, client_phone, cobrador_nome in rows:
            setattr(contract, "cliente_nome", client_name)
            setattr(contract, "cliente_telefone", client_mobile or client_phone)
            setattr(contract, "cobrador_nome", cobrador_nome)
            contracts.append(contract)

        return contracts, int(total or 0)

    async def get_by_id(self, contract_id: int) -> Contrato | None:
        cobrador = aliased(User)
        result = await self.session.execute(
            select(Contrato, Cliente.nome, Cliente.celular01, Cliente.telefone, cobrador.nome)
            .outerjoin(Cliente, Cliente.clientes_id == Contrato.cliente_id)
            .outerjoin(cobrador, cobrador.id == Contrato.usuario_id_vendedor)
            .where(Contrato.contratos_id == contract_id)
        )
        row = result.one_or_none()
        if row is None:
            return None

        contract, client_name, client_mobile, client_phone, cobrador_nome = row
        setattr(contract, "cliente_nome", client_name)
        setattr(contract, "cliente_telefone", client_mobile or client_phone)
        setattr(contract, "cobrador_nome", cobrador_nome)
        return contract

    async def create(self, contract: Contrato) -> Contrato:
        self.session.add(contract)
        await self.session.commit()
        await self.session.refresh(contract)
        return contract

    async def update_fields(self, contract: Contrato, values: dict[str, object]) -> Contrato:
        for field, value in values.items():
            setattr(contract, field, value)
        await self.session.commit()
        await self.session.refresh(contract)
        return contract

    async def delete(self, contract: Contrato) -> None:
        await self.session.delete(contract)
        await self.session.commit()