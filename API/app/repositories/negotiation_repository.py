from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.negotiation import Negociacao, NegociacaoContrato
from app.models.user import User
from app.schemas.negotiation import NegotiationListParams


class NegotiationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self, params: NegotiationListParams) -> tuple[Sequence[Negociacao], int]:
        filters = []

        if params.cliente_nome:
            filters.append(Cliente.nome.ilike(f"%{params.cliente_nome}%"))
        if params.contrato_gerado_id is not None:
            filters.append(Negociacao.contrato_gerado_id == params.contrato_gerado_id)

        stmt = (
            select(Negociacao, Cliente.nome, User.nome, Contrato.quitado)
            .outerjoin(Cliente, Cliente.clientes_id == Negociacao.cliente_id)
            .outerjoin(User, User.id == Negociacao.usuario_id)
            .outerjoin(Contrato, Contrato.contratos_id == Negociacao.contrato_gerado_id)
        )
        count_stmt = (
            select(func.count())
            .select_from(Negociacao)
            .outerjoin(Cliente, Cliente.clientes_id == Negociacao.cliente_id)
        )

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        stmt = stmt.order_by(Negociacao.negociacao_id.desc()).offset((params.page - 1) * params.page_size).limit(params.page_size)

        result = await self.session.execute(stmt)
        total = await self.session.scalar(count_stmt)
        rows = result.all()
        negotiations: list[Negociacao] = []
        for negotiation, client_name, user_name, contrato_quitado in rows:
            setattr(negotiation, "cliente_nome", client_name)
            setattr(negotiation, "usuario_nome", user_name)
            setattr(negotiation, "contrato_quitado", contrato_quitado)
            negotiations.append(negotiation)

        return negotiations, int(total or 0)

    async def get_by_id(self, negotiation_id: int) -> Negociacao | None:
        result = await self.session.execute(
            select(Negociacao, Cliente.nome, User.nome, Contrato.quitado)
            .outerjoin(Cliente, Cliente.clientes_id == Negociacao.cliente_id)
            .outerjoin(User, User.id == Negociacao.usuario_id)
            .outerjoin(Contrato, Contrato.contratos_id == Negociacao.contrato_gerado_id)
            .where(Negociacao.negociacao_id == negotiation_id)
        )
        row = result.one_or_none()
        if row is None:
            return None

        negotiation, client_name, user_name, contrato_quitado = row
        setattr(negotiation, "cliente_nome", client_name)
        setattr(negotiation, "usuario_nome", user_name)
        setattr(negotiation, "contrato_quitado", contrato_quitado)
        return negotiation

    async def create(self, negotiation: Negociacao) -> Negociacao:
        self.session.add(negotiation)
        await self.session.flush()
        return negotiation

    async def get_negotiation_contracts(self, negotiation_id: int) -> list[NegociacaoContrato]:
        result = await self.session.execute(
            select(NegociacaoContrato).where(NegociacaoContrato.negociacao_id == negotiation_id)
        )
        return list(result.scalars().all())

    async def create_negotiation_contract(self, item: NegociacaoContrato) -> NegociacaoContrato:
        self.session.add(item)
        await self.session.flush()
        return item

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh(self, obj: object) -> None:
        await self.session.refresh(obj)
