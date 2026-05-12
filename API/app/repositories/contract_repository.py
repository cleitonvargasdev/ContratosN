from collections.abc import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.orm import aliased, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.contract_commodato import ContratoComodato, ContratoComodatoItem
from app.models.product import Produto
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

    async def get_client_by_id(self, client_id: int) -> Cliente | None:
        return await self.session.get(Cliente, client_id)

    async def list_products_by_ids(self, product_ids: list[int]) -> Sequence[Produto]:
        if not product_ids:
            return []
        result = await self.session.execute(select(Produto).where(Produto.produto_id.in_(product_ids)))
        return result.scalars().all()

    async def get_commodato_by_contract_id(self, contract_id: int) -> ContratoComodato | None:
        stmt = (
            select(ContratoComodato)
            .options(selectinload(ContratoComodato.avalista), selectinload(ContratoComodato.items))
            .where(ContratoComodato.contrato_id == contract_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_commodato(
        self,
        contract_id: int,
        avalista_id: int | None,
        items: list[dict[str, object]],
    ) -> ContratoComodato:
        record = await self.get_commodato_by_contract_id(contract_id)
        if record is None:
            record = ContratoComodato(contrato_id=contract_id, avalista_cliente_id=avalista_id)
            self.session.add(record)
            await self.session.flush()
        else:
            record.avalista_cliente_id = avalista_id

        await self.session.execute(delete(ContratoComodatoItem).where(ContratoComodatoItem.comodato_id == record.comodato_id))
        for item in items:
            self.session.add(ContratoComodatoItem(comodato_id=record.comodato_id, **item))

        await self.session.commit()
        reloaded = await self.get_commodato_by_contract_id(contract_id)
        return reloaded or record

    async def delete_commodato_by_contract_id(self, contract_id: int) -> bool:
        record = await self.get_commodato_by_contract_id(contract_id)
        if record is None:
            return False

        await self.session.delete(record)
        await self.session.commit()
        return True

    async def update_fields(self, contract: Contrato, values: dict[str, object]) -> Contrato:
        for field, value in values.items():
            setattr(contract, field, value)
        await self.session.commit()
        await self.session.refresh(contract)
        return contract

    async def delete(self, contract: Contrato) -> None:
        await self.session.delete(contract)
        await self.session.commit()