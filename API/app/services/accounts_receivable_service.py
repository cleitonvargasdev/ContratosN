from calendar import monthrange
from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounts_receivable import ContaReceber
from app.models.contract import Contrato
from app.models.receipt import Recebimento
from app.repositories.accounts_receivable_repository import AccountsReceivableRepository
from app.repositories.client_repository import ClientRepository
from app.repositories.location_repository import LocationRepository
from app.schemas.accounts_receivable import (
    InstallmentCreateRequest,
    ContractReceiptRead,
    ContractInstallmentGenerateRequest,
    ContractInstallmentRead,
    InstallmentPaymentCreate,
    InstallmentSettleRequest,
    InstallmentUpdateRequest,
)


WEEKDAY_LABELS = {
    0: "SEGUNDA-FEIRA",
    1: "TERCA-FEIRA",
    2: "QUARTA-FEIRA",
    3: "QUINTA-FEIRA",
    4: "SEXTA-FEIRA",
    5: "SABADO",
    6: "DOMINGO",
}


class AccountsReceivableService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = AccountsReceivableRepository(session)
        self.client_repository = ClientRepository(session)
        self.location_repository = LocationRepository(session)

    async def list_contract_installments(self, contract_id: int) -> list[ContractInstallmentRead]:
        contract = await self.repository.get_contract_by_id(contract_id)
        if contract is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato nao encontrado")

        rows = await self.repository.list_by_contract(contract_id)
        if await self._sync_contract_financials(contract, rows):
            await self.repository.commit()
        return [self._build_installment_read(item) for item in rows]

    async def generate_contract_installments(
        self,
        contract_id: int,
        payload: ContractInstallmentGenerateRequest,
        current_user_id: int | None,
    ) -> list[ContractInstallmentRead]:
        contract = await self.repository.get_contract_by_id(contract_id)
        if contract is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato nao encontrado")

        if not payload.parcelas:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhuma parcela informada")

        if await self.repository.contract_has_receipts(contract_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ja existem recebimentos para este contrato. Exclua os pagamentos antes de recalcular as parcelas.",
            )

        await self.repository.delete_installments_by_contract(contract_id)

        installments = [
            ContaReceber(
                contratos_id=contract_id,
                vencimento_original=item.vencimento,
                vencimentol=item.vencimento,
                valor_base=item.valor_total,
                valor_total=item.valor_total,
                valor_recebido=0,
                quitado=False,
                usuarios_id=current_user_id,
                parcela_nro=item.parcela_nro,
                desconto=0,
                valor_juros=0,
            )
            for item in payload.parcelas
        ]
        await self.repository.add_installments(installments)
        await self._sync_contract_financials(contract, installments)
        await self.repository.commit()

        rows = await self.repository.list_by_contract(contract_id)
        return [self._build_installment_read(item) for item in rows]

    async def receive_installment(
        self,
        installment_id: int,
        payload: InstallmentPaymentCreate,
        current_user_id: int | None,
    ) -> ContractInstallmentRead:
        installment = await self.repository.get_by_id(installment_id)
        if installment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela nao encontrada")

        contract = await self.repository.get_contract_by_id(installment.contratos_id) if installment.contratos_id is not None else None
        if contract is not None and contract.recorrencia:
            return await self._receive_recurring_installment(installment, contract, payload, current_user_id)

        payment_date = payload.data_recebimento or datetime.now()
        current_total = float(installment.valor_total or 0)
        current_received = float(installment.valor_recebido or 0)
        payment_value = float(payload.valor_recebido or 0)
        remaining_before_payment = max(current_total - current_received, 0)
        interest_value = max(payment_value - remaining_before_payment, 0)

        receipt = Recebimento(
            contrato_id=installment.contratos_id,
            valor_recebido=payment_value,
            usuario_id=current_user_id,
            data_recebimento=payment_date,
            parcela_nro=installment.parcela_nro,
            desconto=None,
            juros=interest_value,
        )
        await self.repository.add_receipt(receipt)

        installment.valor_recebido = current_received + payment_value
        installment.desconto = float(installment.desconto or 0)
        installment.valor_juros = float(installment.valor_juros or 0) + interest_value
        installment.valor_total = float(installment.valor_base or 0) + float(installment.valor_juros or 0)
        installment.data_recebimento = payment_date
        installment.quitado = float(installment.valor_recebido or 0) >= float(installment.valor_total or 0)
        await self._sync_contract_by_id(installment.contratos_id)
        await self.repository.commit()
        await self.repository.refresh(installment)
        return self._build_installment_read(installment)

    async def create_installment(
        self,
        contract_id: int,
        payload: InstallmentCreateRequest,
        current_user_id: int | None,
    ) -> ContractInstallmentRead:
        contract = await self.repository.get_contract_by_id(contract_id)
        if contract is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato nao encontrado")

        if contract.quitado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contrato quitado nao permite incluir novas parcelas.",
            )

        if payload.parcela_nro <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Numero da parcela deve ser maior que zero")

        existing_installment = await self.repository.get_by_contract_and_parcela(contract_id, payload.parcela_nro)
        if existing_installment is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ja existe parcela com este numero para o contrato")

        base_value = float(payload.valor_base or 0)
        interest_value = float(payload.valor_juros or 0)
        total_value = round(base_value + interest_value, 4)

        if base_value < 0 or interest_value < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valores da parcela nao podem ser negativos")

        installment = ContaReceber(
            contratos_id=contract_id,
            vencimento_original=payload.vencimento,
            vencimentol=payload.vencimento,
            valor_base=round(base_value, 4),
            valor_total=total_value,
            valor_recebido=0,
            quitado=False,
            usuarios_id=current_user_id,
            parcela_nro=payload.parcela_nro,
            desconto=0,
            valor_juros=round(interest_value, 4),
        )

        await self.repository.add_installments([installment])
        await self._sync_contract_by_id(contract_id)
        await self.repository.commit()
        await self.repository.refresh(installment)
        return self._build_installment_read(installment)

    async def update_installment(self, installment_id: int, payload: InstallmentUpdateRequest) -> ContractInstallmentRead:
        installment = await self.repository.get_by_id(installment_id)
        if installment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela nao encontrada")

        if installment.quitado:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parcela quitada nao pode ser alterada")

        receipts = await self.repository.list_receipts_for_installment(installment.contratos_id, installment.parcela_nro)
        if receipts:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parcela com pagamentos lancados nao pode ser alterada")

        if payload.parcela_nro <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Numero da parcela deve ser maior que zero")

        base_value = float(payload.valor_base or 0)
        interest_value = float(payload.valor_juros or 0)
        total_value = round(base_value + interest_value, 4)

        if base_value < 0 or interest_value < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valores da parcela nao podem ser negativos")

        installment.parcela_nro = payload.parcela_nro
        installment.vencimento_original = payload.vencimento
        installment.vencimentol = payload.vencimento
        installment.valor_base = round(base_value, 4)
        installment.valor_juros = round(interest_value, 4)
        installment.valor_total = total_value

        await self._sync_contract_by_id(installment.contratos_id)
        await self.repository.commit()
        await self.repository.refresh(installment)
        return self._build_installment_read(installment)

    async def _receive_recurring_installment(
        self,
        installment: ContaReceber,
        contract: Contrato,
        payload: InstallmentPaymentCreate,
        current_user_id: int | None,
    ) -> ContractInstallmentRead:
        payment_date = payload.data_recebimento or datetime.now()
        payment_value = float(payload.valor_recebido or 0)
        current_total = float(installment.valor_total or 0)
        current_received = float(installment.valor_recebido or 0)
        remaining_balance = max(current_total - current_received - payment_value, 0)
        recurring_interest_percent = float(contract.percent_juros or installment.percent_juros or 0)
        next_installment_value = round(remaining_balance * (1 + (recurring_interest_percent / 100)), 4)

        receipt = Recebimento(
            contrato_id=installment.contratos_id,
            valor_recebido=payment_value,
            usuario_id=current_user_id,
            data_recebimento=payment_date,
            parcela_nro=installment.parcela_nro,
            desconto=None,
            juros=0,
        )
        await self.repository.add_receipt(receipt)

        installment.valor_base = payment_value
        installment.valor_total = payment_value
        installment.valor_recebido = payment_value
        installment.desconto = 0
        installment.valor_juros = 0
        installment.data_recebimento = payment_date
        installment.quitado = True

        if next_installment_value > 0:
            next_due_date = await self._calculate_next_recurring_due_date(contract, installment, payment_date)
            contract.data_final = next_due_date

            existing_installments = await self.repository.list_by_contract(contract.contratos_id)
            next_parcela_nro = max((item.parcela_nro or 0) for item in existing_installments) + 1 if existing_installments else 1

            next_installment = ContaReceber(
                contratos_id=contract.contratos_id,
                vencimento_original=next_due_date,
                vencimentol=next_due_date,
                valor_base=next_installment_value,
                valor_total=next_installment_value,
                valor_recebido=0,
                percent_juros=recurring_interest_percent,
                quitado=False,
                usuarios_id=current_user_id,
                parcela_nro=next_parcela_nro,
                valor_juros=0,
                desconto=0,
                prorrogada=False,
            )
            await self.repository.add_installments([next_installment])

        await self._sync_contract_by_id(installment.contratos_id)
        await self.repository.commit()
        await self.repository.refresh(installment)
        return self._build_installment_read(installment)

    async def list_installment_receipts(self, installment_id: int) -> list[ContractReceiptRead]:
        installment = await self.repository.get_by_id(installment_id)
        if installment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela nao encontrada")

        rows = await self.repository.list_receipts_for_installment(installment.contratos_id, installment.parcela_nro)
        return [
            ContractReceiptRead(
                recebimento_id=receipt.recebimento_id,
                contrato_id=receipt.contrato_id,
                parcela_nro=receipt.parcela_nro,
                valor_recebido=receipt.valor_recebido,
                desconto=receipt.desconto,
                juros=receipt.juros,
                data_recebimento=receipt.data_recebimento,
                usuario_id=receipt.usuario_id,
                usuario_nome=user_name,
            )
            for receipt, user_name in rows
        ]

    async def settle_installment(self, installment_id: int, payload: InstallmentSettleRequest) -> ContractInstallmentRead:
        installment = await self.repository.get_by_id(installment_id)
        if installment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela nao encontrada")

        installment.quitado = True
        installment.data_recebimento = payload.data_recebimento or installment.data_recebimento or datetime.now()
        await self._sync_contract_by_id(installment.contratos_id)
        await self.repository.commit()
        await self.repository.refresh(installment)
        return self._build_installment_read(installment)

    async def reopen_installment(self, installment_id: int) -> ContractInstallmentRead:
        installment = await self.repository.get_by_id(installment_id)
        if installment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela nao encontrada")

        total_value = float(installment.valor_total or 0)
        received_value = float(installment.valor_recebido or 0)
        if received_value >= total_value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parcela recebida integralmente nao pode ser reaberta")

        installment.quitado = False
        await self._sync_contract_by_id(installment.contratos_id)
        await self.repository.commit()
        await self.repository.refresh(installment)
        return self._build_installment_read(installment)

    async def delete_installment_payment(self, installment_id: int) -> ContractInstallmentRead:
        installment = await self.repository.get_by_id(installment_id)
        if installment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela nao encontrada")

        await self.repository.delete_receipts_for_installment(installment.contratos_id or 0, installment.parcela_nro)
        installment.valor_recebido = 0
        installment.data_recebimento = None
        installment.desconto = 0
        installment.valor_juros = 0
        installment.valor_total = float(installment.valor_base or 0)
        installment.quitado = False
        await self._sync_contract_by_id(installment.contratos_id)
        await self.repository.commit()
        await self.repository.refresh(installment)
        return self._build_installment_read(installment)

    async def delete_receipt_payment(self, receipt_id: int) -> ContractInstallmentRead:
        receipt = await self.repository.get_receipt_by_id(receipt_id)
        if receipt is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pagamento nao encontrado")

        installment = await self.repository.get_by_contract_and_parcela(receipt.contrato_id, receipt.parcela_nro)
        if installment is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela nao encontrada")

        await self.repository.delete_receipt(receipt)
        remaining_receipts = await self.repository.list_receipts_for_installment(installment.contratos_id, installment.parcela_nro)

        total_received = 0.0
        total_discount = 0.0
        total_interest = 0.0
        last_payment_date = None
        for remaining_receipt, _ in remaining_receipts:
            total_received += float(remaining_receipt.valor_recebido or 0)
            total_discount += float(remaining_receipt.desconto or 0)
            total_interest += float(remaining_receipt.juros or 0)
            if last_payment_date is None or (remaining_receipt.data_recebimento and remaining_receipt.data_recebimento > last_payment_date):
                last_payment_date = remaining_receipt.data_recebimento

        installment.valor_recebido = total_received
        installment.desconto = total_discount
        installment.valor_juros = total_interest
        installment.valor_total = float(installment.valor_base or 0) + total_interest
        installment.data_recebimento = last_payment_date
        installment.quitado = total_received >= float(installment.valor_total or 0) if remaining_receipts else False
        await self._sync_contract_by_id(installment.contratos_id)
        await self.repository.commit()
        await self.repository.refresh(installment)
        return self._build_installment_read(installment)

    async def _sync_contract_by_id(self, contract_id: int | None) -> None:
        if contract_id is None:
            return

        contract = await self.repository.get_contract_by_id(contract_id)
        if contract is None:
            return

        installments = await self.repository.list_by_contract(contract_id)
        await self._sync_contract_financials(contract, installments)

    async def _calculate_next_recurring_due_date(
        self,
        contract: Contrato,
        installment: ContaReceber,
        payment_date: datetime,
    ) -> datetime:
        base_due_date = installment.vencimentol or installment.vencimento_original or payment_date
        next_month_date = self._add_months(base_due_date, 1)
        holidays = await self._load_contract_holidays(contract)
        return self._move_to_next_business_day(next_month_date, holidays)

    async def _load_contract_holidays(self, contract: Contrato) -> set[date]:
        holidays = await self.location_repository.list_feriados(nivel=1)

        if contract.cliente_id is None:
            return {item.data for item in holidays}

        client = await self.client_repository.get_by_id(contract.cliente_id)
        if client is None:
            return {item.data for item in holidays}

        holiday_dates = {item.data for item in holidays}

        if client.uf:
            state_holidays = await self.location_repository.list_feriados(nivel=2, uf=client.uf)
            holiday_dates.update(item.data for item in state_holidays)

        if client.cidade_id is not None:
            city_holidays = await self.location_repository.list_feriados(nivel=3, cidade_id=client.cidade_id)
            holiday_dates.update(item.data for item in city_holidays)

        return holiday_dates

    def _move_to_next_business_day(self, value: datetime, holidays: set[date]) -> datetime:
        candidate = value
        while candidate.weekday() >= 5 or candidate.date() in holidays:
            candidate += timedelta(days=1)
        return candidate

    def _add_months(self, value: datetime, months: int) -> datetime:
        month_index = value.month - 1 + months
        year = value.year + month_index // 12
        month = month_index % 12 + 1
        day = min(value.day, monthrange(year, month)[1])
        return value.replace(year=year, month=month, day=day)

    async def _sync_contract_financials(self, contract, installments: list[ContaReceber] | tuple[ContaReceber, ...]) -> bool:
        totals = self.repository.build_contract_totals(installments)
        has_changes = False

        for field in ("valor_final", "valor_recebido", "valor_em_aberto", "valor_em_atraso", "quitado"):
            new_value = totals[field]
            if getattr(contract, field) != new_value:
                setattr(contract, field, new_value)
                has_changes = True

        due_dates = [item.vencimentol or item.vencimento_original for item in installments if (item.vencimentol or item.vencimento_original) is not None]
        latest_due_date = max(due_dates, key=self._normalize_datetime_for_compare, default=None)
        if not self._same_datetime_value(getattr(contract, "data_final", None), latest_due_date):
            contract.data_final = latest_due_date
            has_changes = True

        return has_changes

    @staticmethod
    def _normalize_datetime_for_compare(value: datetime | None) -> datetime:
        if value is None:
            return datetime.min
        if value.tzinfo is None or value.utcoffset() is None:
            return value
        return value.astimezone(UTC).replace(tzinfo=None)

    @classmethod
    def _same_datetime_value(cls, left: datetime | None, right: datetime | None) -> bool:
        if left is None or right is None:
                        return left is right
        return cls._normalize_datetime_for_compare(left) == cls._normalize_datetime_for_compare(right)

    def _build_installment_read(self, installment: ContaReceber) -> ContractInstallmentRead:
        due_date = installment.vencimentol or installment.vencimento_original
        weekday = None
        if due_date is not None:
            weekday = WEEKDAY_LABELS[due_date.weekday()]

        return ContractInstallmentRead(
            id=installment.id,
            contratos_id=installment.contratos_id,
            parcela_nro=installment.parcela_nro,
            vencimento_original=installment.vencimento_original,
            vencimentol=installment.vencimentol,
            valor_base=installment.valor_base,
            valor_total=installment.valor_total,
            valor_recebido=installment.valor_recebido,
            data_recebimento=installment.data_recebimento,
            quitado=installment.quitado,
            desconto=installment.desconto,
            valor_juros=installment.valor_juros,
            dia_semana=weekday,
            possui_pagamento=bool((installment.valor_recebido or 0) > 0 or installment.data_recebimento),
        )