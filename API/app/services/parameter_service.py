from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.timezone import get_local_timezone
from app.core.secrets import encrypt_secret, secret_matches, secret_needs_reencryption
from app.repositories.api_config_repository import ApiConfigRepository
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
        self.api_config_repository = ApiConfigRepository(session)
        self.location_service = LocationService(session)
        self.client_metrics_service = ClientMetricsService(session)
        self.local_timezone = get_local_timezone()

    async def get_parameters(self) -> Parametro:
        parameter = await self.repository.get_singleton()
        if parameter is not None:
            parameter_changed = self._apply_whatsapp_defaults(parameter)
            api_configs_changed = await self._ensure_whatsapp_api_configs(parameter)
            if parameter_changed:
                await self.repository.commit()
                await self.repository.refresh(parameter)
            elif api_configs_changed:
                await self.repository.refresh(parameter)
            return parameter

        parameter = Parametro(
            emitir_sons=True,
            score_valor_inicial=1000,
            score_pontos_atraso_parcela=15,
            score_pontos_atraso_quitacao_contrato=30,
            score_pontos_pagamento_em_dia=5,
            score_pontos_quitacao_em_dia=20,
            score_pontos_negociacao=0,
            score_atualizacao_automatica=False,
            score_agendamentos=[],
            whatsapp_cobranca_automatica=False,
            whatsapp_agendamentos=[],
            whatsapp_cobranca_dias_antes=1,
            whatsapp_cobranca_dias_depois=1,
            regra_nono_dig_whats=[],
            pais_whatsapp=55,
            flag_whatsapp_telefone1=False,
            flag_whatsapp_telefone2=False,
            api_whatsapp="quepasa",
            usuario_api_whatsapp=(settings.quepasa_user.strip() if settings.quepasa_user else "cleitinhojt@gmail.com"),
            token_api_whatsapp=settings.quepasa_token.strip() or "CONTRATOS",
            sufixo_whatsapp="@s.whatsapp.net",
            ligar_websocket=False,
            silenciar_mensagem=False,
            whatsapp_cobranca_modelo=(
                "Olá, {cliente_nome}. Identificamos parcelas próximas do vencimento ou em atraso. "
                "Entre em contato para regularização."
            ),
        )
        parameter = await self.repository.add(parameter)
        await self._ensure_whatsapp_api_configs(parameter)
        return parameter

    @staticmethod
    def _apply_whatsapp_defaults(parameter: Parametro) -> bool:
        changed = False

        default_user = settings.quepasa_user.strip() if settings.quepasa_user else "cleitinhojt@gmail.com"
        default_token = settings.quepasa_token.strip() or "CONTRATOS"

        if not parameter.api_whatsapp:
            parameter.api_whatsapp = "quepasa"
            changed = True
        if not parameter.usuario_api_whatsapp:
            parameter.usuario_api_whatsapp = default_user
            changed = True
        if not parameter.token_api_whatsapp:
            parameter.token_api_whatsapp = default_token
            changed = True
        if not parameter.sufixo_whatsapp:
            parameter.sufixo_whatsapp = "@s.whatsapp.net"
            changed = True
        if not parameter.pais_whatsapp:
            parameter.pais_whatsapp = 55
            changed = True
        if parameter.flag_whatsapp_telefone1 is None:
            parameter.flag_whatsapp_telefone1 = False
            changed = True
        if parameter.flag_whatsapp_telefone2 is None:
            parameter.flag_whatsapp_telefone2 = False
            changed = True

        return changed

    async def list_whatsapp_api_names(self) -> list[str]:
        parameter = await self.get_parameters()
        api_names = await self.api_config_repository.list_distinct_api_names()
        current_name = parameter.api_whatsapp.strip() if isinstance(parameter.api_whatsapp, str) else None
        if current_name and current_name not in api_names:
            return sorted([*api_names, current_name], key=str.lower)
        return api_names

    async def _ensure_whatsapp_api_configs(self, parameter: Parametro) -> bool:
        api_name = (parameter.api_whatsapp or "quepasa").strip().lower()
        if api_name != "quepasa":
            return False

        health_password = settings.quepasa_health_password.strip()
        defaults = [
            {
                "nome_api": "quepasa",
                "funcionalidade": "conectar",
                "url": f"{settings.quepasa_apiwpp_url.rstrip('/')}/scan",
                "key1": "Accept",
                "value1": "application/json, image/png, */*",
                "key2": "X-QUEPASA-TOKEN",
                "value2": "{token_api_whatsapp}",
                "key3": "X-QUEPASA-USER",
                "value3": "{usuario_api_whatsapp}",
            },
            {
                "nome_api": "quepasa",
                "funcionalidade": "verificar",
                "url": f"{settings.quepasa_apiwpp_url.rstrip('/')}/info",
                "key1": "Accept",
                "value1": "application/json",
                "key2": "X-QUEPASA-TOKEN",
                "value2": "{token_api_whatsapp}",
            },
            {
                "nome_api": "quepasa",
                "funcionalidade": "mensagem",
                "url": f"{settings.quepasa_apiwpp_url.rstrip('/')}/v3/bot/{{token_api_whatsapp}}/send",
                "key1": "Accept",
                "value1": "application/json",
                "key2": "Content-Type",
                "value2": "application/json",
                "body": '{"chatid":"{chatid}","text":"{text}"}',
            },
            {
                "nome_api": "quepasa",
                "funcionalidade": "documento",
                "url": f"{settings.quepasa_apiwpp_url.rstrip('/')}/v3/bot/{{token_api_whatsapp}}/senddocument",
                "key1": "Accept",
                "value1": "application/json",
                "key2": "Content-Type",
                "value2": "application/json",
                "body": '{"chatId":"{chatId}","url":"{url}","text":"{text}"}',
            },
            {
                "nome_api": "quepasa",
                "funcionalidade": "health",
                "url": f"{settings.quepasa_apiwpp_url.rstrip('/')}/health",
                "key1": "Accept",
                "value1": "application/json",
                "key2": "X-QUEPASA-USER",
                "value2": "{usuario_api_whatsapp}",
                "key3": "X-QUEPASA-PASSWORD",
                "value3": health_password,
                "_encrypted_fields": {"value3"},
            },
        ]

        changed = False
        for payload in defaults:
            encrypted_fields = payload.get("_encrypted_fields", set())
            record = await self.api_config_repository.get_by_name_and_functionality(payload["nome_api"], payload["funcionalidade"])
            if record is None:
                await self.api_config_repository.create(self._prepare_api_config_payload(payload, encrypted_fields))
                changed = True
                continue

            updates = {
                field: self._prepare_api_config_field_value(field, value, encrypted_fields)
                for field, value in payload.items()
                if not field.startswith("_") and not self._api_config_field_matches(record, field, value, encrypted_fields)
            }
            if updates:
                await self.api_config_repository.update(record, updates)
                changed = True

        return changed

    @staticmethod
    def _prepare_api_config_payload(payload: dict[str, object], encrypted_fields: set[str]) -> dict[str, object]:
        return {
            field: ParameterService._prepare_api_config_field_value(field, value, encrypted_fields)
            for field, value in payload.items()
            if not field.startswith("_")
        }

    @staticmethod
    def _prepare_api_config_field_value(field: str, value: object, encrypted_fields: set[str]) -> object:
        if field in encrypted_fields and isinstance(value, str):
            return encrypt_secret(value)
        return value

    @staticmethod
    def _api_config_field_matches(record: object, field: str, expected_value: object, encrypted_fields: set[str]) -> bool:
        current_value = getattr(record, field)
        if field in encrypted_fields and isinstance(expected_value, str):
            return secret_matches(current_value, expected_value) and not secret_needs_reencryption(current_value)
        return current_value == expected_value

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
        sent_whatsapp = 0
        error_whatsapp = 0
        whatsapp_batch_id: int | None = None

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
                from app.services.whatsapp_dispatch_service import WhatsAppDispatchService

                dispatch_service = WhatsAppDispatchService(self.session)
                dispatch_result = await dispatch_service.execute_scheduled_dispatch(
                    parameter,
                    executed_at=now,
                    scheduled_for=None if manual else parameter.whatsapp_cobranca_proxima_execucao,
                    manual=manual,
                )
                prepared_whatsapp = int(dispatch_result.get("prepared") or 0)
                sent_whatsapp = int(dispatch_result.get("sent") or 0)
                error_whatsapp = int(dispatch_result.get("errors") or 0)
                whatsapp_batch_id = int(dispatch_result["batch_id"]) if dispatch_result.get("batch_id") is not None else None
                parameter.whatsapp_cobranca_ultima_execucao = now
                parameter.whatsapp_ultima_execucao_sucesso = error_whatsapp == 0
                parameter.whatsapp_ultimo_erro = None if error_whatsapp == 0 else f"{error_whatsapp} envio(s) com erro."
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
            cobrancas_whatsapp_enviadas=sent_whatsapp,
            cobrancas_whatsapp_erros=error_whatsapp,
            whatsapp_batch_id=whatsapp_batch_id,
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
        today = reference.date()
        result = await self.session.execute(
            select(func.count())
            .select_from(ContaReceber)
            .join(Contrato, Contrato.contratos_id == ContaReceber.contratos_id)
            .join(Cliente, Cliente.clientes_id == Contrato.cliente_id)
            .where(
                ContaReceber.quitado.is_(False),
                Cliente.flag_whatsapp.is_(True),
                Cliente.nao_enviar_whatsapp.is_(False),
                ContaReceber.vencimentol.is_not(None),
                ContaReceber.msg_whatsapp.is_(False),
                func.date(ContaReceber.vencimentol) >= lower_bound,
                func.date(ContaReceber.vencimentol) <= today,
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