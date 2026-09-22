from collections import defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timezone import get_local_timezone
from app.models.accounts_receivable import ContaReceber
from app.models.client import Cliente
from app.models.contract import Contrato
from app.schemas.dashboard import DashboardChartPoint, DashboardEndingContract, DashboardSummaryRead


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.timezone = get_local_timezone()

    async def get_summary(self, *, agrupamento: str, referencia: date, dias_finalizacao: int) -> DashboardSummaryRead:
        dias_finalizacao = max(1, min(dias_finalizacao, 10))
        pontos = await self._get_chart(agrupamento, referencia)
        finalizando, total = await self._get_ending_contracts(referencia, dias_finalizacao)
        return DashboardSummaryRead(
            pontos=pontos,
            contratos_finalizando=finalizando,
            total_contratos_finalizando=total,
        )

    async def _get_chart(self, agrupamento: str, referencia: date) -> list[DashboardChartPoint]:
        if agrupamento == "ano":
            inicio, fim = date(referencia.year, 1, 1), date(referencia.year + 1, 1, 1)
            chaves = [(mes, f"{mes:02d}") for mes in range(1, 13)]
            key_for = lambda valor: valor.month
        else:
            inicio = referencia.replace(day=1)
            fim = date(referencia.year + (referencia.month == 12), (referencia.month % 12) + 1, 1)
            total_dias = (fim - inicio).days
            chaves = [(dia, f"{dia:02d}") for dia in range(1, total_dias + 1)]
            key_for = lambda valor: valor.day

        inicio_dt = datetime.combine(inicio, time.min, tzinfo=self.timezone)
        fim_dt = datetime.combine(fim, time.min, tzinfo=self.timezone)
        previstos = defaultdict(float)
        recebidos = defaultdict(float)

        query = select(ContaReceber.vencimentol, ContaReceber.valor_total).where(
            ContaReceber.vencimentol >= inicio_dt, ContaReceber.vencimentol < fim_dt
        )
        for vencimento, valor in (await self.session.execute(query)).all():
            if vencimento:
                previstos[key_for(vencimento.astimezone(self.timezone))] += float(valor or 0)

        query = select(ContaReceber.data_recebimento, ContaReceber.valor_recebido).where(
            ContaReceber.data_recebimento >= inicio_dt, ContaReceber.data_recebimento < fim_dt
        )
        for recebimento, valor in (await self.session.execute(query)).all():
            if recebimento:
                recebidos[key_for(recebimento.astimezone(self.timezone))] += float(valor or 0)

        return [DashboardChartPoint(label=label, previsto=previstos[key], recebido=recebidos[key]) for key, label in chaves]

    async def _get_ending_contracts(self, referencia: date, dias: int) -> tuple[list[DashboardEndingContract], int]:
        limite = referencia + timedelta(days=dias)
        query = (
            select(Contrato, Cliente.nome)
            .outerjoin(Cliente, Cliente.clientes_id == Contrato.cliente_id)
            .where(
                Contrato.data_final.is_not(None),
                func.date(Contrato.data_final) >= referencia,
                func.date(Contrato.data_final) <= limite,
                (Contrato.quitado.is_(False)) | (Contrato.quitado.is_(None)),
            )
            .order_by(Contrato.data_final.asc())
        )
        rows = (await self.session.execute(query)).all()
        items = [
            DashboardEndingContract(
                contratos_id=contrato.contratos_id,
                cliente_nome=nome,
                data_final=contrato.data_final.date() if contrato.data_final else None,
                valor_em_aberto=float(contrato.valor_em_aberto or 0),
                dias_para_finalizar=(contrato.data_final.date() - referencia).days if contrato.data_final else 0,
            )
            for contrato, nome in rows
        ]
        return items[:8], len(items)
