from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounts_receivable import ContaReceber
from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.parameter import Parametro
from app.repositories.parameter_repository import ParameterRepository
from app.schemas.parameter import ParameterAutomationRunResponse, ParameterRead, ParameterUpdate
from app.services.client_metrics_service import ClientMetricsService
from app.services.location_service import LocationService


class ParameterService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ParameterRepository(session)
        self.location_service = LocationService(session)
        self.client_metrics_service = ClientMetricsService(session)
        self.local_timezone = datetime.now().astimezone().tzinfo or UTC

    async def get_parameters(self) -> Parametro:
        parameter = await self.repository.get_singleton()
        if parameter is not None:
            return parameter

        parameter = Parametro(
            emitir_sons=True,
            score_valor_inicial=1000,
            score_pontos_atraso_parcela=15,
            score_pontos_atraso_quitacao_contrato=30,
            score_pontos_pagamento_em_dia=5,
            score_pontos_quitacao_em_dia=20,
            score_atualizacao_automatica=False,
            score_agendamentos=[],
            whatsapp_cobranca_automatica=False,
            whatsapp_agendamentos=[],
            whatsapp_cobranca_dias_antes=1,
            whatsapp_cobranca_dias_depois=1,
            regra_nono_dig_whats=[],
            pais_whatsapp=55,
            ligar_websocket=False,
            silenciar_mensagem=False,
            whatsapp_cobranca_modelo=(
                "Olá, {cliente_nome}. Identificamos parcelas próximas do vencimento ou em atraso. "
                "Entre em contato para regularização."
            ),
        )
        return await self.repository.add(parameter)

    async def update_parameters(self, payload: ParameterUpdate) -> Parametro:
        parameter = await self.get_parameters()
        values = await self._normalize_payload(payload.model_dump(exclude_unset=True))
        for field, value in values.items():
            setattr(parameter, field, value)
        await self.repository.commit()
        await self.repository.refresh(parameter)
        return parameter

    async def run_scheduled_actions(self) -> ParameterAutomationRunResponse:
        return await self._execute_actions(manual=True)

    async def run_due_scheduled_actions(self) -> ParameterAutomationRunResponse:
        return await self._execute_actions(manual=False)

    async def _execute_actions(self, manual: bool) -> ParameterAutomationRunResponse:
        parameter = await self.get_parameters()
        now = datetime.now(self.local_timezone)
        recalculated_clients = 0
        prepared_whatsapp = 0

        score_due = manual or self._is_schedule_due(parameter.score_atualizacao_automatica, parameter.score_atualizacao_proxima_execucao, now)
        whatsapp_due = manual or self._is_schedule_due(parameter.whatsapp_cobranca_automatica, parameter.whatsapp_cobranca_proxima_execucao, now)

        if score_due:
            try:
                recalculated_clients = await self.client_metrics_service.refresh_all_clients()
                parameter.score_atualizacao_ultima_execucao = now
                parameter.score_ultima_execucao_sucesso = True
                parameter.score_ultimo_erro = None
            except Exception as exc:
                parameter.score_atualizacao_ultima_execucao = now
                parameter.score_ultima_execucao_sucesso = False
                parameter.score_ultimo_erro = str(exc)

        if whatsapp_due:
            try:
                prepared_whatsapp = await self._count_whatsapp_candidates(parameter, now)
                parameter.whatsapp_cobranca_ultima_execucao = now
                parameter.whatsapp_ultima_execucao_sucesso = True
                parameter.whatsapp_ultimo_erro = None
            except Exception as exc:
                parameter.whatsapp_cobranca_ultima_execucao = now
                parameter.whatsapp_ultima_execucao_sucesso = False
                parameter.whatsapp_ultimo_erro = str(exc)

        parameter.score_atualizacao_proxima_execucao = self._calculate_next_execution(parameter.score_agendamentos, now)
        parameter.whatsapp_cobranca_proxima_execucao = self._calculate_next_execution(parameter.whatsapp_agendamentos, now)

        await self.repository.commit()
        await self.repository.refresh(parameter)
        return ParameterAutomationRunResponse(
            executado_em=now,
            clientes_recalculados=recalculated_clients,
            cobrancas_whatsapp_preparadas=prepared_whatsapp,
            parametros=ParameterRead.model_validate(parameter),
        )

    async def _normalize_payload(self, values: dict[str, object]) -> dict[str, object]:
        location_payload = {
            "uf": values.get("uf"),
            "cidade_id": values.get("cidade_id"),
            "bairro_id": values.get("bairrosid"),
            "cep": values.get("cep"),
            "endereco": values.get("endereco"),
        }
        normalized_location = await self.location_service.normalize_user_location_fields(location_payload)
        values["uf"] = normalized_location.get("uf")
        values["cidade_id"] = normalized_location.get("cidade_id")
        values["bairrosid"] = normalized_location.get("bairro_id")
        values["cep"] = normalized_location.get("cep")

        values["score_agendamentos"] = self._normalize_schedules(values.get("score_agendamentos"))
        values["whatsapp_agendamentos"] = self._normalize_schedules(values.get("whatsapp_agendamentos"))
        local_now = datetime.now(self.local_timezone)
        values["score_atualizacao_proxima_execucao"] = self._calculate_next_execution(values.get("score_agendamentos"), local_now)
        values["whatsapp_cobranca_proxima_execucao"] = self._calculate_next_execution(values.get("whatsapp_agendamentos"), local_now)

        return values

    async def _count_whatsapp_candidates(self, parameter: Parametro, reference: datetime) -> int:
        lower_bound = reference.date() - timedelta(days=max(parameter.whatsapp_cobranca_dias_depois or 0, 0))
        upper_bound = reference.date() + timedelta(days=max(parameter.whatsapp_cobranca_dias_antes or 0, 0))
        result = await self.session.execute(
            select(func.count())
            .select_from(ContaReceber)
            .join(Contrato, Contrato.contratos_id == ContaReceber.contratos_id)
            .join(Cliente, Cliente.clientes_id == Contrato.cliente_id)
            .where(
                ContaReceber.quitado.is_(False),
                Cliente.flag_whatsapp.is_(True),
                ContaReceber.vencimentol.is_not(None),
                func.date(ContaReceber.vencimentol) >= lower_bound,
                func.date(ContaReceber.vencimentol) <= upper_bound,
            )
        )
        return int(result.scalar() or 0)

    def _normalize_schedules(self, value: object) -> list[dict[str, object]]:
        if value in (None, ""):
            return []

        normalized: list[dict[str, object]] = []
        if not isinstance(value, list):
            return normalized

        for item in value:
            if not isinstance(item, dict):
                continue
            dias = sorted({int(day) for day in item.get("dias_semana", []) if 0 <= int(day) <= 6})
            horario = str(item.get("horario", "")).strip()
            if not dias or not self._is_valid_hour(horario):
                continue
            normalized.append({"dias_semana": dias, "horario": horario})

        return normalized

    def _calculate_next_execution(self, schedules: object, reference: datetime) -> datetime | None:
        candidates: list[datetime] = []
        if not isinstance(schedules, list):
            return None

        local_reference = reference.astimezone(self.local_timezone) if reference.tzinfo is not None else reference.replace(tzinfo=self.local_timezone)

        for item in schedules:
            if not isinstance(item, dict):
                continue
            dias = item.get("dias_semana", [])
            horario = item.get("horario")
            if not isinstance(dias, list) or not isinstance(horario, str) or not self._is_valid_hour(horario):
                continue

            hour, minute = (int(part) for part in horario.split(":"))
            for day in dias:
                day_value = int(day)
                for offset in range(0, 8):
                    candidate_date = (local_reference + timedelta(days=offset)).date()
                    if candidate_date.weekday() != day_value:
                        continue
                    candidate_local = datetime(
                        candidate_date.year,
                        candidate_date.month,
                        candidate_date.day,
                        hour,
                        minute,
                        tzinfo=self.local_timezone,
                    )
                    if candidate_local > local_reference:
                        candidates.append(candidate_local)
                        break

        return min(candidates) if candidates else None

    @staticmethod
    def _is_schedule_due(enabled: bool, next_run: datetime | None, reference: datetime) -> bool:
        return enabled and next_run is not None and next_run <= reference

    @staticmethod
    def _is_valid_hour(value: str) -> bool:
        parts = value.split(":")
        if len(parts) != 2:
            return False
        hour, minute = parts
        if not hour.isdigit() or not minute.isdigit():
            return False
        hour_value = int(hour)
        minute_value = int(minute)
        return 0 <= hour_value <= 23 and 0 <= minute_value <= 59