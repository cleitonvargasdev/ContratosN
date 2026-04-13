from datetime import date, datetime, time, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounts_receivable import ContaReceber
from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.parameter import Parametro
from app.models.whatsapp_dispatch import WhatsAppDispatchBatch, WhatsAppDispatchItem
from app.schemas.whatsapp_dispatch import (
    WhatsAppDispatchBatchListParams,
    WhatsAppDispatchBatchListResponse,
    WhatsAppDispatchBatchRead,
    WhatsAppDispatchItemListResponse,
    WhatsAppDispatchItemRead,
)
from app.services.accounts_receivable_service import AccountsReceivableService


class WhatsAppDispatchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.accounts_receivable_service = AccountsReceivableService(session)

    async def execute_scheduled_dispatch(
        self,
        parameter: Parametro,
        *,
        executed_at: datetime,
        scheduled_for: datetime | None,
        manual: bool,
    ) -> dict[str, int | str | None]:
        schedule_snapshot = self._resolve_schedule_snapshot(parameter.whatsapp_agendamentos, scheduled_for)
        source_phone = self._resolve_source_phone(parameter)
        batch = WhatsAppDispatchBatch(
            parametros_id=parameter.parametros_id,
            scheduled_for=scheduled_for,
            executed_at=executed_at,
            status="processing",
            source_phone=source_phone,
            schedule_snapshot=schedule_snapshot,
            summary_json={"manual": manual},
            total_items=0,
            total_sent=0,
            total_errors=0,
        )
        self.session.add(batch)
        await self.session.flush()

        sent_count = 0
        error_count = 0
        candidates = await self._list_candidates(parameter, executed_at)
        batch.total_items = len(candidates)

        try:
            for installment, contract, client in candidates:
                try:
                    dispatch_result = await self.accounts_receivable_service.send_installment_whatsapp_from_entities(
                        installment,
                        contract,
                        client,
                        send_type=2,
                        commit=False,
                    )
                    sent_count += 1
                    self.session.add(
                        WhatsAppDispatchItem(
                            batch_id=batch.id,
                            conta_receber_id=installment.id,
                            contratos_id=contract.contratos_id,
                            cliente_id=client.clientes_id,
                            parcela_nro=installment.parcela_nro,
                            client_name=client.nome,
                            destination_phone=str(dispatch_result["destination_phone"]),
                            source_phone=source_phone,
                            status="sent",
                            amount=float(installment.valor_total or 0),
                            due_at=installment.vencimentol or installment.vencimento_original,
                            sent_at=dispatch_result["sent_at"],
                            message_payload=dispatch_result["message_payload"],
                            provider_payload=dispatch_result["provider_payload"],
                        )
                    )
                except Exception as exc:
                    error_count += 1
                    self.session.add(
                        WhatsAppDispatchItem(
                            batch_id=batch.id,
                            conta_receber_id=installment.id,
                            contratos_id=contract.contratos_id,
                            cliente_id=client.clientes_id,
                            parcela_nro=installment.parcela_nro,
                            client_name=client.nome,
                            destination_phone=(client.celular01 or "").strip() or None,
                            source_phone=source_phone,
                            status="error",
                            amount=float(installment.valor_total or 0),
                            due_at=installment.vencimentol or installment.vencimento_original,
                            message_payload=self.accounts_receivable_service.build_installment_whatsapp_payload(client.nome, contract.contratos_id, installment),
                            error_message=self._extract_error_message(exc),
                        )
                    )

            batch.total_sent = sent_count
            batch.total_errors = error_count
            batch.status = self._resolve_batch_status(batch.total_items, sent_count, error_count)
            batch.error_message = None if error_count == 0 else f"{error_count} envio(s) com erro."
            batch.summary_json = {
                "manual": manual,
                "total_items": batch.total_items,
                "total_sent": sent_count,
                "total_errors": error_count,
            }
            await self.session.flush()
            return {
                "batch_id": batch.id,
                "prepared": batch.total_items,
                "sent": sent_count,
                "errors": error_count,
                "status": batch.status,
            }
        except Exception as exc:
            batch.total_sent = sent_count
            batch.total_errors = error_count or 1
            batch.status = "error"
            batch.error_message = self._extract_error_message(exc)
            batch.summary_json = {
                "manual": manual,
                "total_items": batch.total_items,
                "total_sent": sent_count,
                "total_errors": batch.total_errors,
            }
            await self.session.flush()
            raise

    async def list_batches(self, params: WhatsAppDispatchBatchListParams) -> WhatsAppDispatchBatchListResponse:
        query = select(WhatsAppDispatchBatch)
        count_query = select(func.count()).select_from(WhatsAppDispatchBatch)

        query, count_query = self._apply_batch_date_filter(query, count_query, params.data_inicial, params.data_final)

        total = int((await self.session.execute(count_query)).scalar() or 0)
        offset = (params.page - 1) * params.page_size
        result = await self.session.execute(
            query
            .order_by(WhatsAppDispatchBatch.executed_at.desc(), WhatsAppDispatchBatch.id.desc())
            .offset(offset)
            .limit(params.page_size)
        )
        items = [WhatsAppDispatchBatchRead.model_validate(item) for item in result.scalars().all()]
        return WhatsAppDispatchBatchListResponse(items=items, total=total, page=params.page, page_size=params.page_size)

    async def list_batch_items(self, batch_id: int, page: int, page_size: int) -> WhatsAppDispatchItemListResponse:
        batch = await self.session.get(WhatsAppDispatchBatch, batch_id)
        if batch is None:
            raise HTTPException(status_code=404, detail="Lote de envio nao encontrado")

        total = int(
            (await self.session.execute(select(func.count()).select_from(WhatsAppDispatchItem).where(WhatsAppDispatchItem.batch_id == batch_id))).scalar()
            or 0
        )
        offset = (page - 1) * page_size
        result = await self.session.execute(
            select(WhatsAppDispatchItem)
            .where(WhatsAppDispatchItem.batch_id == batch_id)
            .order_by(WhatsAppDispatchItem.sent_at.desc(), WhatsAppDispatchItem.id.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = [WhatsAppDispatchItemRead.model_validate(item) for item in result.scalars().all()]
        return WhatsAppDispatchItemListResponse(items=items, total=total, page=page, page_size=page_size)

    async def delete_batch(self, batch_id: int) -> bool:
        batch = await self.session.get(WhatsAppDispatchBatch, batch_id)
        if batch is None:
            return False
        await self.session.delete(batch)
        await self.session.commit()
        return True

    async def _list_candidates(self, parameter: Parametro, reference: datetime) -> list[tuple[ContaReceber, Contrato, Cliente]]:
        lower_bound = reference.date() - timedelta(days=max(parameter.whatsapp_cobranca_dias_depois or 0, 0))
        today = reference.date()
        result = await self.session.execute(
            select(ContaReceber, Contrato, Cliente)
            .join(Contrato, Contrato.contratos_id == ContaReceber.contratos_id)
            .join(Cliente, Cliente.clientes_id == Contrato.cliente_id)
            .where(
                ContaReceber.quitado.is_(False),
                ContaReceber.vencimentol.is_not(None),
                ContaReceber.msg_whatsapp.is_(False),
                func.date(ContaReceber.vencimentol) >= lower_bound,
                func.date(ContaReceber.vencimentol) <= today,
                Cliente.flag_whatsapp.is_(True),
                Cliente.nao_enviar_whatsapp.is_(False),
                func.coalesce(func.nullif(Cliente.celular01, ""), "") != "",
            )
            .order_by(ContaReceber.vencimentol.asc(), ContaReceber.id.asc())
        )
        return [(installment, contract, client) for installment, contract, client in result.all()]

    @staticmethod
    def _resolve_schedule_snapshot(schedules: object, scheduled_for: datetime | None) -> dict[str, object] | None:
        if scheduled_for is None or not isinstance(schedules, list):
            return None
        weekday = scheduled_for.weekday()
        time_label = scheduled_for.strftime("%H:%M")
        for item in schedules:
            if not isinstance(item, dict):
                continue
            days = item.get("dias_semana")
            hour = item.get("horario")
            if isinstance(days, list) and weekday in [int(value) for value in days] and hour == time_label:
                return {"dias_semana": [int(value) for value in days], "horario": time_label}
        return {"horario": time_label, "dias_semana": [weekday]}

    @staticmethod
    def _resolve_source_phone(parameter: Parametro) -> str | None:
        candidates = [
            ((parameter.telefone1 or "").strip(), bool(parameter.flag_whatsapp_telefone1)),
            ((parameter.telefone2 or "").strip(), bool(parameter.flag_whatsapp_telefone2)),
            ((parameter.telefone1 or "").strip(), False),
            ((parameter.telefone2 or "").strip(), False),
        ]
        for phone, preferred in candidates:
            if preferred and phone:
                return phone
        for phone, _ in candidates:
            if phone:
                return phone
        return None

    @staticmethod
    def _resolve_batch_status(total_items: int, sent_count: int, error_count: int) -> str:
        if total_items == 0:
            return "empty"
        if sent_count and error_count:
            return "partial"
        if error_count:
            return "error"
        return "success"

    @staticmethod
    def _extract_error_message(exc: Exception) -> str:
        if isinstance(exc, HTTPException):
            detail = exc.detail
            return str(detail) if detail else "Falha ao enviar mensagem pelo WhatsApp."
        return str(exc) or "Falha ao enviar mensagem pelo WhatsApp."

    @staticmethod
    def _apply_batch_date_filter(query, count_query, data_inicial: date | None, data_final: date | None):
        if data_inicial is not None:
            start = datetime.combine(data_inicial, time.min).astimezone()
            query = query.where(WhatsAppDispatchBatch.executed_at >= start)
            count_query = count_query.where(WhatsAppDispatchBatch.executed_at >= start)
        if data_final is not None:
            end = datetime.combine(data_final, time.max).astimezone()
            query = query.where(WhatsAppDispatchBatch.executed_at <= end)
            count_query = count_query.where(WhatsAppDispatchBatch.executed_at <= end)
        return query, count_query