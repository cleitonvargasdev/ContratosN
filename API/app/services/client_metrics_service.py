from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounts_receivable import ContaReceber
from app.models.client import Cliente
from app.models.client_score_log import ClientScoreLog
from app.models.contract import Contrato
from app.models.parameter import Parametro


class ClientMetricsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.local_timezone = datetime.now().astimezone().tzinfo or UTC

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

        metrics, score_context = self._build_metrics(contracts, installments, parameter)
        previous_score = int(client.score) if client.score is not None else int(metrics["score"])
        for field, value in metrics.items():
            setattr(client, field, value)

        current_score = int(metrics["score"])
        if current_score != previous_score:
            score_snapshot = self._build_score_log_snapshot(current_score - previous_score, score_context)
            self._append_score_log(
                client.clientes_id,
                previous_score,
                current_score - previous_score,
                str(score_snapshot["event_name"]),
                rule_points=int(score_snapshot["rule_points"]) if score_snapshot["rule_points"] is not None else None,
                quantity_reference=int(score_snapshot["quantity_reference"]) if score_snapshot["quantity_reference"] is not None else None,
                calculation_detail=str(score_snapshot["calculation_detail"]) if score_snapshot["calculation_detail"] is not None else None,
            )

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
    ) -> tuple[dict[str, object], dict[str, int]]:
        today = datetime.now(self.local_timezone).date()
        installments_by_contract: dict[int, list[ContaReceber]] = {}
        total_open = 0.0
        total_overdue = 0.0
        total_open_count = 0
        overdue_count = 0
        overdue_installment_days = 0
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
            due_date = self._to_local_date(due_datetime)
            total_value = float(installment.valor_total or 0)
            received_value = float(installment.valor_recebido or 0)
            remaining_value = 0.0 if installment.quitado else max(total_value - received_value, 0.0)
            paid_delay_days = 0

            if remaining_value > 0:
                total_open += remaining_value
                total_open_count += 1
                if next_due_datetime is None or self._normalize_datetime(due_datetime) < self._normalize_datetime(next_due_datetime):
                    next_due_datetime = due_datetime

                if due_date is not None and due_date < today:
                    overdue_count += 1
                    total_overdue += remaining_value
                    overdue_days = (today - due_date).days
                    overdue_installment_days += overdue_days
                    if overdue_days > max_overdue_days:
                        max_overdue_days = overdue_days

                    installment_delay_sum += overdue_days
                    installment_delay_count += 1

            if due_date is not None and installment.data_recebimento is not None:
                payment_date = self._to_local_date(installment.data_recebimento)
                delay_days = max(((payment_date - due_date).days if payment_date is not None else 0), 0)
                installment_delay_sum += delay_days
                installment_delay_count += 1
                paid_delay_days = delay_days
                if float(installment.valor_recebido or 0) > 0 and delay_days == 0:
                    on_time_payments += 1

            if paid_delay_days > 0:
                overdue_installment_days += paid_delay_days

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
        points_late_installment = abs(int(parameter.score_pontos_atraso_parcela)) if parameter and parameter.score_pontos_atraso_parcela is not None else 15
        points_late_contract = (
            abs(int(parameter.score_pontos_atraso_quitacao_contrato))
            if parameter and parameter.score_pontos_atraso_quitacao_contrato is not None
            else 30
        )
        points_on_time_payment = abs(int(parameter.score_pontos_pagamento_em_dia)) if parameter and parameter.score_pontos_pagamento_em_dia is not None else 5
        points_on_time_contract = abs(int(parameter.score_pontos_quitacao_em_dia)) if parameter and parameter.score_pontos_quitacao_em_dia is not None else 20

        media_atraso_parcelas = round(installment_delay_sum / installment_delay_count, 6) if installment_delay_count else 0.0
        media_atraso_contratos = round(contract_delay_sum / contract_delay_count, 6) if contract_delay_count else 0.0
        installment_penalty = overdue_installment_days * points_late_installment
        contract_penalty = late_settled_contracts * points_late_contract
        payment_bonus = on_time_payments * points_on_time_payment
        contract_bonus = on_time_contracts * points_on_time_contract

        score = initial_score
        score -= installment_penalty
        score -= contract_penalty
        score += payment_bonus
        score += contract_bonus
        score = max(score, 0)

        return (
            {
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
            },
            {
                "points_late_installment": points_late_installment,
                "points_late_contract": points_late_contract,
                "points_on_time_payment": points_on_time_payment,
                "points_on_time_contract": points_on_time_contract,
                "overdue_installment_days": overdue_installment_days,
                "late_settled_contracts": late_settled_contracts,
                "on_time_payments": on_time_payments,
                "on_time_contracts": on_time_contracts,
                "installment_penalty": installment_penalty,
                "contract_penalty": contract_penalty,
                "payment_bonus": payment_bonus,
                "contract_bonus": contract_bonus,
            },
        )

    def _append_score_log(
        self,
        client_id: int,
        previous_score: int,
        score_delta: int,
        event_name: str,
        *,
        rule_points: int | None = None,
        quantity_reference: int | None = None,
        calculation_detail: str | None = None,
    ) -> None:
        current_score = max(previous_score + score_delta, 0)
        self.session.add(
            ClientScoreLog(
                cliente_id=client_id,
                data_hora_evento=datetime.now(UTC),
                evento=event_name,
                pontuacao_anterior=max(previous_score, 0),
                variacao_pontos=score_delta,
                pontuacao_atual=current_score,
                regra_pontos=rule_points,
                quantidade_referencia=quantity_reference,
                detalhe_calculo=calculation_detail,
            )
        )

    @classmethod
    def _build_score_log_snapshot(cls, score_delta: int, score_context: dict[str, int]) -> dict[str, object]:
        if score_delta == 0:
            return {
                "event_name": "Reprocessamento score",
                "rule_points": None,
                "quantity_reference": None,
                "calculation_detail": None,
            }

        pure_event = cls._resolve_score_log_event(score_delta, score_context)
        if pure_event == "Pagamento":
            quantity = score_context["on_time_payments"]
            rule = score_context["points_on_time_payment"]
            return {
                "event_name": pure_event,
                "rule_points": rule,
                "quantity_reference": quantity,
                "calculation_detail": f"+{rule} pts x {quantity} pagamento(s) em dia",
            }
        if pure_event == "Quitação":
            quantity = score_context["on_time_contracts"]
            rule = score_context["points_on_time_contract"]
            return {
                "event_name": pure_event,
                "rule_points": rule,
                "quantity_reference": quantity,
                "calculation_detail": f"+{rule} pts x {quantity} quitação(ões) em dia",
            }
        if pure_event == "Atraso pag. parcela":
            quantity = score_context["overdue_installment_days"]
            rule = score_context["points_late_installment"]
            return {
                "event_name": pure_event,
                "rule_points": -rule,
                "quantity_reference": quantity,
                "calculation_detail": f"-{rule} pts x {quantity} dia(s) de atraso em parcelas",
            }
        if pure_event == "Atraso quit. contrato":
            quantity = score_context["late_settled_contracts"]
            rule = score_context["points_late_contract"]
            return {
                "event_name": pure_event,
                "rule_points": -rule,
                "quantity_reference": quantity,
                "calculation_detail": f"-{rule} pts x {quantity} quitação(ões) com atraso",
            }

        detail_parts: list[str] = []
        if score_context["installment_penalty"]:
            detail_parts.append(
                f"-{score_context['points_late_installment']} pts x {score_context['overdue_installment_days']} dia(s) atraso parcelas"
            )
        if score_context["contract_penalty"]:
            detail_parts.append(
                f"-{score_context['points_late_contract']} pts x {score_context['late_settled_contracts']} quitação(ões) em atraso"
            )
        if score_context["payment_bonus"]:
            detail_parts.append(
                f"+{score_context['points_on_time_payment']} pts x {score_context['on_time_payments']} pagamento(s) em dia"
            )
        if score_context["contract_bonus"]:
            detail_parts.append(
                f"+{score_context['points_on_time_contract']} pts x {score_context['on_time_contracts']} quitação(ões) em dia"
            )

        return {
            "event_name": pure_event,
            "rule_points": None,
            "quantity_reference": None,
            "calculation_detail": "; ".join(detail_parts) or None,
        }

    @staticmethod
    def _resolve_score_log_event(score_delta: int, score_context: dict[str, int]) -> str:
        if score_delta > 0:
            matches_payment = score_context["points_on_time_payment"] > 0 and score_delta % score_context["points_on_time_payment"] == 0
            matches_contract = score_context["points_on_time_contract"] > 0 and score_delta % score_context["points_on_time_contract"] == 0
            if matches_payment and not matches_contract:
                return "Pagamento"
            if matches_contract and not matches_payment:
                return "Quitação"
        elif score_delta < 0:
            magnitude = abs(score_delta)
            matches_installment = score_context["points_late_installment"] > 0 and magnitude % score_context["points_late_installment"] == 0
            matches_contract = score_context["points_late_contract"] > 0 and magnitude % score_context["points_late_contract"] == 0
            if matches_installment and not matches_contract:
                return "Atraso pag. parcela"
            if matches_contract and not matches_installment:
                return "Atraso quit. contrato"

        return "Reprocessamento score"

    @staticmethod
    def _normalize_datetime(value: datetime | None) -> datetime:
        if value is None:
            return datetime.min
        if value.tzinfo is None or value.utcoffset() is None:
            return value
        return value.astimezone(UTC).replace(tzinfo=None)

    def _to_local_date(self, value: datetime | None):
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            return value.date()
        return value.astimezone(self.local_timezone).date()