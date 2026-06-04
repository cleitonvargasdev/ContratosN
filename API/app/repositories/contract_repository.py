from collections.abc import Sequence

from sqlalchemy import String, delete, func, or_, select, cast
from sqlalchemy.orm import aliased, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.contract_commodato import ContratoComodato, ContratoComodatoItem
from app.models.product import Produto
from app.models.user import User
from app.schemas.contract import BatchReceiptContractSearchParams, ContractListParams


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

    async def search_open_contracts_for_batch_receipt(
        self,
        params: BatchReceiptContractSearchParams,
    ) -> tuple[list[tuple[int, int | None, str | None, str | None, bool, float | None]], int]:
        raw_query = (params.query or '').strip()
        numeric_query = ''.join(char for char in raw_query if char.isdigit())
        if len(raw_query) < 3 and len(numeric_query) < 3:
            return [], 0

        normalized_document_expr = func.replace(func.replace(func.replace(func.coalesce(Cliente.cpf_cnpj, ''), '.', ''), '-', ''), '/', '')
        logical_client_key_expr = func.coalesce(
            func.nullif(normalized_document_expr, ''),
            func.nullif(func.lower(func.trim(func.coalesce(Cliente.nome, ''))), ''),
            '__sem_cliente__',
        )
        comodato_exists_expr = ContratoComodato.contrato_id.is_not(None)
        filters = [or_(Contrato.quitado.is_(False), Contrato.quitado.is_(None))]

        query_filters = []
        if len(raw_query) >= 3:
            query_filters.append(Cliente.nome.ilike(f'%{raw_query}%'))
        if len(numeric_query) >= 3:
            query_filters.append(normalized_document_expr.ilike(f'%{numeric_query}%'))
            query_filters.append(cast(Contrato.contratos_id, String).ilike(f'%{numeric_query}%'))

        if query_filters:
            filters.append(or_(*query_filters))

        client_groups_stmt = (
            select(
                logical_client_key_expr.label('logical_client_key'),
                func.max(Cliente.nome).label('cliente_nome'),
                func.max(Cliente.cpf_cnpj).label('cliente_cpf_cnpj'),
            )
            .select_from(Contrato)
            .outerjoin(Cliente, Cliente.clientes_id == Contrato.cliente_id)
            .outerjoin(ContratoComodato, ContratoComodato.contrato_id == Contrato.contratos_id)
            .where(*filters)
        )
        client_groups_stmt = client_groups_stmt.group_by(logical_client_key_expr)
        client_groups_stmt = client_groups_stmt.order_by(func.max(Cliente.nome).asc(), logical_client_key_expr.asc())

        total_stmt = select(func.count()).select_from(client_groups_stmt.subquery())
        paged_clients_stmt = client_groups_stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)

        paged_clients = (await self.session.execute(paged_clients_stmt)).all()
        total = await self.session.scalar(total_stmt)

        if not paged_clients:
            return [], int(total or 0)

        logical_client_keys = list(dict.fromkeys(str(row.logical_client_key) for row in paged_clients))

        stmt = (
            select(
                Contrato.contratos_id,
                Contrato.cliente_id,
                Cliente.nome,
                Cliente.cpf_cnpj,
                comodato_exists_expr.label('comodato'),
                Contrato.valor_parcela,
            )
            .select_from(Contrato)
            .outerjoin(Cliente, Cliente.clientes_id == Contrato.cliente_id)
            .outerjoin(ContratoComodato, ContratoComodato.contrato_id == Contrato.contratos_id)
            .where(*filters)
            .where(logical_client_key_expr.in_(logical_client_keys))
            .order_by(logical_client_key_expr.asc(), Cliente.nome.asc(), Contrato.contratos_id.desc())
        )

        rows = (await self.session.execute(stmt)).all()
        return rows, int(total or 0)

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