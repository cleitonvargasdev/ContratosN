from collections.abc import Sequence

from sqlalchemy import distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.accounts_payable import ContaPagar, ContaPagarParcela, PagamentoContaPagar
from app.models.client import Cliente
from app.models.supplier import Fornecedor
from app.models.user import User
from app.schemas.accounts_payable import AccountsPayableListParams


class AccountsPayableRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_accounts_payable(self, params: AccountsPayableListParams) -> tuple[Sequence[ContaPagar], int]:
        stmt = (
            select(ContaPagar)
            .outerjoin(Cliente, ContaPagar.cliente_id == Cliente.clientes_id)
            .outerjoin(User, ContaPagar.usuario_id == User.id)
            .outerjoin(Fornecedor, ContaPagar.fornecedor_id == Fornecedor.fornecedor_id)
            .outerjoin(ContaPagarParcela, ContaPagarParcela.conta_pagar_id == ContaPagar.conta_pagar_id)
            .options(
                selectinload(ContaPagar.cliente),
                selectinload(ContaPagar.usuario),
                selectinload(ContaPagar.fornecedor),
                selectinload(ContaPagar.parcelas).selectinload(ContaPagarParcela.pagamentos),
            )
            .distinct()
        )
        count_stmt = (
            select(func.count(distinct(ContaPagar.conta_pagar_id)))
            .select_from(ContaPagar)
            .outerjoin(Cliente, ContaPagar.cliente_id == Cliente.clientes_id)
            .outerjoin(User, ContaPagar.usuario_id == User.id)
            .outerjoin(Fornecedor, ContaPagar.fornecedor_id == Fornecedor.fornecedor_id)
            .outerjoin(ContaPagarParcela, ContaPagarParcela.conta_pagar_id == ContaPagar.conta_pagar_id)
        )

        if params.quitado is not None:
            stmt = stmt.where(ContaPagar.quitado.is_(params.quitado))
            count_stmt = count_stmt.where(ContaPagar.quitado.is_(params.quitado))
        if params.tipo_pessoa:
            stmt = stmt.where(ContaPagar.tipo_pessoa == params.tipo_pessoa)
            count_stmt = count_stmt.where(ContaPagar.tipo_pessoa == params.tipo_pessoa)
        if params.pessoa_query:
            pattern = f"%{params.pessoa_query}%"
            filters = or_(
                Cliente.nome.ilike(pattern),
                Cliente.cpf_cnpj.ilike(pattern),
                User.nome.ilike(pattern),
                User.cpf.ilike(pattern),
                Fornecedor.nome.ilike(pattern),
                Fornecedor.cpf_cnpj.ilike(pattern),
            )
            stmt = stmt.where(filters)
            count_stmt = count_stmt.where(filters)
        if params.data_vencimento_inicial is not None:
            stmt = stmt.where(ContaPagarParcela.vencimento >= params.data_vencimento_inicial)
            count_stmt = count_stmt.where(ContaPagarParcela.vencimento >= params.data_vencimento_inicial)
        if params.data_vencimento_final is not None:
            stmt = stmt.where(ContaPagarParcela.vencimento <= params.data_vencimento_final)
            count_stmt = count_stmt.where(ContaPagarParcela.vencimento <= params.data_vencimento_final)
        if params.data_referencia_inicial is not None:
            stmt = stmt.where(ContaPagar.data_referencia_inicial >= params.data_referencia_inicial)
            count_stmt = count_stmt.where(ContaPagar.data_referencia_inicial >= params.data_referencia_inicial)
        if params.data_referencia_final is not None:
            stmt = stmt.where(ContaPagar.data_referencia_final <= params.data_referencia_final)
            count_stmt = count_stmt.where(ContaPagar.data_referencia_final <= params.data_referencia_final)

        total = int((await self.session.execute(count_stmt)).scalar_one())
        result = await self.session.execute(
            stmt.order_by(ContaPagar.created_at.desc(), ContaPagar.conta_pagar_id.desc())
            .offset((params.page - 1) * params.page_size)
            .limit(params.page_size)
        )
        return result.scalars().unique().all(), total

    async def get_by_id(self, conta_pagar_id: int) -> ContaPagar | None:
        result = await self.session.execute(
            select(ContaPagar)
            .where(ContaPagar.conta_pagar_id == conta_pagar_id)
            .options(
                selectinload(ContaPagar.cliente),
                selectinload(ContaPagar.usuario),
                selectinload(ContaPagar.fornecedor),
                selectinload(ContaPagar.parcelas).selectinload(ContaPagarParcela.pagamentos),
            )
        )
        return result.scalars().unique().first()

    async def get_installment_by_id(self, parcela_id: int) -> ContaPagarParcela | None:
        result = await self.session.execute(
            select(ContaPagarParcela)
            .where(ContaPagarParcela.parcela_id == parcela_id)
            .options(
                selectinload(ContaPagarParcela.conta).selectinload(ContaPagar.parcelas),
                selectinload(ContaPagarParcela.pagamentos),
            )
        )
        return result.scalars().unique().first()

    async def get_client_by_id(self, cliente_id: int) -> Cliente | None:
        return await self.session.get(Cliente, cliente_id)

    async def get_user_by_id(self, usuario_id: int) -> User | None:
        return await self.session.get(User, usuario_id)

    async def get_supplier_by_id(self, fornecedor_id: int) -> Fornecedor | None:
        return await self.session.get(Fornecedor, fornecedor_id)

    async def search_people(self, query: str, limit: int = 10) -> tuple[Sequence[Cliente], Sequence[User], Sequence[Fornecedor]]:
        pattern = f"%{query}%"
        clients = (
            await self.session.execute(
                select(Cliente)
                .where(or_(Cliente.nome.ilike(pattern), Cliente.cpf_cnpj.ilike(pattern)))
                .order_by(Cliente.nome)
                .limit(limit)
            )
        ).scalars().all()
        users = (
            await self.session.execute(
                select(User)
                .where(or_(User.nome.ilike(pattern), User.cpf.ilike(pattern)))
                .order_by(User.nome)
                .limit(limit)
            )
        ).scalars().all()
        suppliers = (
            await self.session.execute(
                select(Fornecedor)
                .where(or_(Fornecedor.nome.ilike(pattern), Fornecedor.cpf_cnpj.ilike(pattern)))
                .order_by(Fornecedor.nome)
                .limit(limit)
            )
        ).scalars().all()
        return clients, users, suppliers

    async def add_account(self, record: ContaPagar) -> ContaPagar:
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def add_payment(self, payment: PagamentoContaPagar) -> None:
        self.session.add(payment)

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh_account(self, record: ContaPagar) -> None:
        await self.session.refresh(record)

    async def refresh_installment(self, record: ContaPagarParcela) -> None:
        await self.session.refresh(record)

    async def delete_account(self, record: ContaPagar) -> None:
        await self.session.delete(record)
        await self.session.commit()