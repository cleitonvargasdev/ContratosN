from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.whatsapp_chatbot import Solicitacao
from app.models.user import User
from app.schemas.solicitation import SolicitationListParams


class SolicitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self, params: SolicitationListParams) -> tuple[Sequence[Solicitacao], int]:
        vendedor = aliased(User)
        aprovador = aliased(User)
        filters = self._build_filters(params)

        stmt = (
            select(Solicitacao, Cliente.nome, vendedor.nome, aprovador.nome)
            .outerjoin(Cliente, Cliente.clientes_id == Solicitacao.cliente_id)
            .outerjoin(vendedor, vendedor.id == Solicitacao.vendedor_id)
            .outerjoin(aprovador, aprovador.id == Solicitacao.usuario_id_aprovou)
        )
        count_stmt = (
            select(func.count())
            .select_from(Solicitacao)
            .outerjoin(Cliente, Cliente.clientes_id == Solicitacao.cliente_id)
            .outerjoin(vendedor, vendedor.id == Solicitacao.vendedor_id)
            .outerjoin(aprovador, aprovador.id == Solicitacao.usuario_id_aprovou)
        )

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        stmt = stmt.order_by(Solicitacao.datahora_solicitacao.desc(), Solicitacao.id.desc())
        stmt = stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)

        result = await self.session.execute(stmt)
        total = await self.session.scalar(count_stmt)
        return self._map_rows(result.all()), int(total or 0)

    async def get_by_id(self, solicitation_id: int) -> Solicitacao | None:
        vendedor = aliased(User)
        aprovador = aliased(User)
        result = await self.session.execute(
            select(Solicitacao, Cliente.nome, vendedor.nome, aprovador.nome)
            .outerjoin(Cliente, Cliente.clientes_id == Solicitacao.cliente_id)
            .outerjoin(vendedor, vendedor.id == Solicitacao.vendedor_id)
            .outerjoin(aprovador, aprovador.id == Solicitacao.usuario_id_aprovou)
            .where(Solicitacao.id == solicitation_id)
        )
        row = result.one_or_none()
        if row is None:
            return None
        return self._map_rows([row])[0]

    async def count_pending(self) -> int:
        total = await self.session.scalar(
            select(func.count()).select_from(Solicitacao).where(func.upper(func.coalesce(Solicitacao.status, "PENDENTE")) == "PENDENTE")
        )
        return int(total or 0)

    async def get_client_by_id(self, client_id: int | None) -> Cliente | None:
        if client_id is None:
            return None
        result = await self.session.execute(select(Cliente).where(Cliente.clientes_id == client_id))
        return result.scalar_one_or_none()

    async def get_contract_by_id(self, contract_id: int | None) -> Contrato | None:
        if contract_id is None:
            return None
        result = await self.session.execute(select(Contrato).where(Contrato.contratos_id == contract_id))
        return result.scalar_one_or_none()

    async def get_latest_contract_for_client(self, client_id: int | None) -> Contrato | None:
        if client_id is None:
            return None
        result = await self.session.execute(
            select(Contrato)
            .where(Contrato.cliente_id == client_id)
            .order_by(Contrato.data_contrato.desc(), Contrato.contratos_id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def save(self, solicitation: Solicitacao) -> Solicitacao:
        await self.session.commit()
        await self.session.refresh(solicitation)
        return solicitation

    def _build_filters(self, params: SolicitationListParams) -> list[object]:
        filters: list[object] = []

        if params.status:
            filters.append(func.upper(func.coalesce(Solicitacao.status, "")) == params.status.strip().upper())
        if params.tipo:
            filters.append(func.upper(func.coalesce(Solicitacao.tipo, "")) == params.tipo.strip().upper())
        if params.cliente_id is not None:
            filters.append(Solicitacao.cliente_id == params.cliente_id)
        if params.termo:
            term = params.termo.strip()
            if term:
                filters.append(
                    or_(
                        Solicitacao.nome_informado.ilike(f"%{term}%"),
                        Solicitacao.telefone.ilike(f"%{term}%"),
                        Solicitacao.cpf_cnpj.ilike(f"%{term}%"),
                        Cliente.nome.ilike(f"%{term}%"),
                    )
                )

        return filters

    @staticmethod
    def _map_rows(rows: Sequence[tuple[Solicitacao, str | None, str | None, str | None]]) -> list[Solicitacao]:
        solicitations: list[Solicitacao] = []
        for solicitation, client_name, vendedor_nome, aprovador_nome in rows:
            setattr(solicitation, "cliente_nome", client_name)
            setattr(solicitation, "vendedor_nome", vendedor_nome)
            setattr(solicitation, "usuario_nome_aprovou", aprovador_nome)
            solicitations.append(solicitation)
        return solicitations
