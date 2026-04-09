from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounts_receivable import ContaReceber
from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.parameter import Parametro


class ClientMetricsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def refresh_client_metrics(self, client_id: int | None) -> Cliente | None:
        if client_id is None:
            return None

        client_result = await self.session.execute(select(Cliente).where(Cliente.clientes_id == client_id))
        client = client_result.scalar_one_or_none()
        if client is None:
            return None

        parameter = await self._load_parameter()
        contract_result = await self.session.execute(select(Contrato).where(Contrato.cliente_id == client_id))
        contracts = contract_result.scalars().all()
        contract_ids = [contract.contratos_id for contract in contracts if contract.contratos_id is not None]

        installments: list[ContaReceber] = []
        if contract_ids:
            installment_result = await self.session.execute(
                select(ContaReceber)
                .where(ContaReceber.contratos_id.in_(contract_ids))
                .order_by(ContaReceber.contratos_id.asc(), ContaReceber.parcela_nro.asc(), ContaReceber.id.asc())
            )
            installments = list(installment_result.scalars().all())

        metrics = self._build_metrics(contracts, installments, parameter)
        for field, value in metrics.items():
            setattr(client, field, value)

        return client

    async def refresh_all_clients(self) -> int:
        result = await self.session.execute(select(Cliente.clientes_id).order_by(Cliente.clientes_id.asc()))
        client_ids = [row[0] for row in result.all()]
        for client_id in client_ids:
            await self.refresh_client_metrics(client_id)
        return len(client_ids)

    async def _load_parameter(self) -> Parametro | None:
        result = await self.session.execute(select(Parametro).order_by(Parametro.parametros_id.asc()).limit(1))
        return result.scalar_one_or_none()

    def _build_metrics(
        self,
        contracts: list[Contrato],
        installments: list[ContaReceber],
        parameter: Parametro | None,
    ) -> dict[str, object]:
        today = datetime.now(UTC).date()
        installments_by_contract: dict[int, list[ContaReceber]] = {}
        total_open = 0.0
        total_overdue = 0.0
        total_open_count = 0
        overdue_count = 0
        max_overdue_days = 0
        next_due_datetime = None
        installment_delay_sum = 0
        installment_delay_count = 0
        on_time_payments = 0

        for installment in installments:
            contract_id = installment.contratos_id
            if contract_id is not None:
                installments_by_contract.setdefault(contract_id, []).append(installment)

            due_datetime = installment.vencimentol or installment.vencimento_original
            due_date = due_datetime.date() if due_datetime is not None else None
            total_value = float(installment.valor_total or 0)
            received_value = float(installment.valor_recebido or 0)
            remaining_value = 0.0 if installment.quitado else max(total_value - received_value, 0.0)

            if remaining_value > 0:
                total_open += remaining_value
                total_open_count += 1
                if next_due_datetime is None or self._normalize_datetime(due_datetime) < self._normalize_datetime(next_due_datetime):
                    next_due_datetime = due_datetime

                if due_date is not None and due_date < today:
                    overdue_count += 1
                    total_overdue += remaining_value
                    overdue_days = (today - due_date).days
                    if overdue_days > max_overdue_days:
                        max_overdue_days = overdue_days

                    installment_delay_sum += overdue_days
                    installment_delay_count += 1

            if due_date is not None and installment.data_recebimento is not None:
                delay_days = max((installment.data_recebimento.date() - due_date).days, 0)
                installment_delay_sum += delay_days
                installment_delay_count += 1
                if float(installment.valor_recebido or 0) > 0 and delay_days == 0:
                    on_time_payments += 1

        on_time_contracts = 0
        late_settled_contracts = 0
        contract_delay_sum = 0
        contract_delay_count = 0

        for contract in contracts:
            contract_installments = installments_by_contract.get(contract.contratos_id, [])
            last_payment = max(
                (item.data_recebimento for item in contract_installments if item.data_recebimento is not None),
                default=None,
                key=self._normalize_datetime,
            )

            if not contract.quitado and contract.data_final is not None and contract.data_final.date() < today:
                delay_days = (today - contract.data_final.date()).days
                contract_delay_sum += delay_days
                contract_delay_count += 1

            if contract.quitado and contract.data_final is not None and last_payment is not None:
                delay_days = max((last_payment.date() - contract.data_final.date()).days, 0)
                contract_delay_sum += delay_days
                contract_delay_count += 1
                if delay_days == 0:
                    on_time_contracts += 1
                else:
                    late_settled_contracts += 1

        initial_score = int(parameter.score_valor_inicial) if parameter and parameter.score_valor_inicial is not None else 1000
        points_late_installment = int(parameter.score_pontos_atraso_parcela) if parameter and parameter.score_pontos_atraso_parcela is not None else 15
        points_late_contract = (
            int(parameter.score_pontos_atraso_quitacao_contrato)
            if parameter and parameter.score_pontos_atraso_quitacao_contrato is not None
            else 30
        )
        points_on_time_payment = int(parameter.score_pontos_pagamento_em_dia) if parameter and parameter.score_pontos_pagamento_em_dia is not None else 5
        points_on_time_contract = int(parameter.score_pontos_quitacao_em_dia) if parameter and parameter.score_pontos_quitacao_em_dia is not None else 20

        media_atraso_parcelas = round(installment_delay_sum / installment_delay_count, 6) if installment_delay_count else 0.0
        media_atraso_contratos = round(contract_delay_sum / contract_delay_count, 6) if contract_delay_count else 0.0
        installment_penalty = int(round(points_late_installment * media_atraso_parcelas))

        score = initial_score
        score -= installment_penalty
        score -= late_settled_contracts * points_late_contract
        score += on_time_payments * points_on_time_payment
        score += on_time_contracts * points_on_time_contract
        score = max(score, 0)

        return {
            "debito_atual": round(total_open, 4),
            "valor_em_aberto": round(total_open, 4),
            "valor_atrasado": round(total_overdue, 4),
            "parc_aberto": total_open_count,
            "parc_atrasadas": overdue_count,
            "prox_vencto": next_due_datetime,
            "mais_atrasada": str(max_overdue_days) if max_overdue_days > 0 else None,
            "score": score,
            "media_atraso_parcelas": media_atraso_parcelas,
            "media_atraso_contratos": media_atraso_contratos,
        }

    @staticmethod
    def _normalize_datetime(value: datetime | None) -> datetime:
        if value is None:
            return datetime.min
        if value.tzinfo is None or value.utcoffset() is None:
            return value
        return value.astimezone(UTC).replace(tzinfo=None)