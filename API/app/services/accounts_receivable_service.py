from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounts_receivable import ContaReceber
from app.models.receipt import Recebimento
from app.repositories.accounts_receivable_repository import AccountsReceivableRepository
from app.schemas.accounts_receivable import (
    ContractReceiptRead,
    ContractInstallmentGenerateRequest,
    ContractInstallmentRead,
    InstallmentPaymentCreate,
    InstallmentSettleRequest,
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

    async def _sync_contract_financials(self, contract, installments: list[ContaReceber] | tuple[ContaReceber, ...]) -> bool:
        totals = self.repository.build_contract_totals(installments)
        has_changes = False

        for field in ("valor_final", "valor_recebido", "valor_em_aberto", "valor_em_atraso", "quitado"):
            new_value = totals[field]
            if getattr(contract, field) != new_value:
                setattr(contract, field, new_value)
                has_changes = True

        return has_changes

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