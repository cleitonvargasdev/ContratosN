from collections.abc import Sequence
from datetime import datetime, time, timedelta

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounts_receivable import ContaReceber
from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.receipt import Recebimento
from app.models.user import User
from app.schemas.accounts_receivable import AccountsReceivableListParams


class AccountsReceivableRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_contract_by_id(self, contract_id: int) -> Contrato | None:
        result = await self.session.execute(select(Contrato).where(Contrato.contratos_id == contract_id))
        return result.scalar_one_or_none()

    async def list_by_contract(self, contract_id: int) -> Sequence[ContaReceber]:
        result = await self.session.execute(
            select(ContaReceber)
            .where(ContaReceber.contratos_id == contract_id)
            .order_by(ContaReceber.parcela_nro.asc(), ContaReceber.vencimentol.asc(), ContaReceber.id.asc())
        )
        return result.scalars().all()

    async def list_installments(self, params: AccountsReceivableListParams) -> tuple[list[tuple[ContaReceber, int | None, str | None, str | None]], int]:
        filters = []
        due_date_expr = func.coalesce(ContaReceber.vencimentol, ContaReceber.vencimento_original)

        if params.recebida is True:
            filters.append(ContaReceber.quitado.is_(True))
        elif params.recebida is False:
            filters.append(or_(ContaReceber.quitado.is_(False), ContaReceber.quitado.is_(None)))

        if params.cliente_query:
            term = f"%{params.cliente_query}%"
            normalized_document = func.replace(func.replace(func.replace(func.coalesce(Cliente.cpf_cnpj, ""), ".", ""), "-", ""), "/", "")
            numeric_query = "".join(char for char in params.cliente_query if char.isdigit())
            query_filters = [Cliente.nome.ilike(term), Cliente.cpf_cnpj.ilike(term)]
            if numeric_query:
                query_filters.append(normalized_document.ilike(f"%{numeric_query}%"))
            filters.append(or_(*query_filters))

        if params.data_vencimento_inicial is not None:
            start_due = datetime.combine(params.data_vencimento_inicial, time.min)
            filters.append(due_date_expr >= start_due)

        if params.data_vencimento_final is not None:
            end_due_exclusive = datetime.combine(params.data_vencimento_final + timedelta(days=1), time.min)
            filters.append(due_date_expr < end_due_exclusive)

        stmt = (
            select(ContaReceber, Contrato.cliente_id, Cliente.nome, Cliente.cpf_cnpj)
            .outerjoin(Contrato, Contrato.contratos_id == ContaReceber.contratos_id)
            .outerjoin(Cliente, Cliente.clientes_id == Contrato.cliente_id)
        )
        count_stmt = (
            select(func.count())
            .select_from(ContaReceber)
            .outerjoin(Contrato, Contrato.contratos_id == ContaReceber.contratos_id)
            .outerjoin(Cliente, Cliente.clientes_id == Contrato.cliente_id)
        )

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        stmt = stmt.order_by(due_date_expr.asc(), ContaReceber.contratos_id.asc(), ContaReceber.parcela_nro.asc(), ContaReceber.id.asc())
        stmt = stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)

        result = await self.session.execute(stmt)
        total = await self.session.scalar(count_stmt)
        return result.all(), int(total or 0)

    async def get_by_id(self, installment_id: int) -> ContaReceber | None:
        result = await self.session.execute(select(ContaReceber).where(ContaReceber.id == installment_id))
        return result.scalar_one_or_none()

    async def get_by_contract_and_parcela(self, contract_id: int | None, parcela_nro: int | None) -> ContaReceber | None:
        if contract_id is None or parcela_nro is None:
            return None
        result = await self.session.execute(
            select(ContaReceber).where(
                ContaReceber.contratos_id == contract_id,
                ContaReceber.parcela_nro == parcela_nro,
            )
        )
        return result.scalar_one_or_none()

    async def contract_has_receipts(self, contract_id: int) -> bool:
        count = await self.session.scalar(select(func.count()).select_from(Recebimento).where(Recebimento.contrato_id == contract_id))
        return bool(count)

    async def delete_installments_by_contract(self, contract_id: int) -> None:
        await self.session.execute(delete(ContaReceber).where(ContaReceber.contratos_id == contract_id))

    async def add_installments(self, installments: list[ContaReceber]) -> None:
        self.session.add_all(installments)

    async def add_receipt(self, receipt: Recebimento) -> None:
        self.session.add(receipt)

    async def list_receipts_for_installment(self, contract_id: int | None, parcela_nro: int | None):
        if contract_id is None or parcela_nro is None:
            return []

        result = await self.session.execute(
            select(Recebimento, User.nome)
            .outerjoin(User, User.id == Recebimento.usuario_id)
            .where(
                Recebimento.contrato_id == contract_id,
                Recebimento.parcela_nro == parcela_nro,
            )
            .order_by(Recebimento.data_recebimento.desc(), Recebimento.recebimento_id.desc())
        )
        return result.all()

    async def get_receipt_by_id(self, receipt_id: int) -> Recebimento | None:
        result = await self.session.execute(select(Recebimento).where(Recebimento.recebimento_id == receipt_id))
        return result.scalar_one_or_none()

    async def delete_receipt(self, receipt: Recebimento) -> None:
        await self.session.delete(receipt)

    async def delete_receipts_for_installment(self, contract_id: int, parcela_nro: int | None) -> None:
        await self.session.execute(
            delete(Recebimento).where(
                Recebimento.contrato_id == contract_id,
                Recebimento.parcela_nro == parcela_nro,
            )
        )

    @staticmethod
    def build_contract_totals(installments: Sequence[ContaReceber], reference_datetime: datetime | None = None) -> dict[str, float | bool]:
        today = (reference_datetime or datetime.now()).date()
        total_received = 0.0
        total_open = 0.0
        total_overdue = 0.0
        total_contract_value = 0.0
        all_paid = bool(installments)

        for installment in installments:
            total_value = float(installment.valor_total or 0)
            received_value = float(installment.valor_recebido or 0)
            remaining_value = 0.0 if installment.quitado else max(total_value - received_value, 0.0)
            due_date = installment.vencimentol or installment.vencimento_original

            total_received += received_value
            total_open += remaining_value
            total_contract_value += total_value

            if remaining_value > 0 and due_date is not None and due_date.date() < today:
                total_overdue += remaining_value

            if not installment.quitado:
                all_paid = False

        return {
            "valor_final": round(total_contract_value, 4),
            "valor_recebido": round(total_received, 4),
            "valor_em_aberto": round(total_open, 4),
            "valor_em_atraso": round(total_overdue, 4),
            "quitado": all_paid,
        }

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh(self, instance: ContaReceber | Contrato) -> None:
        await self.session.refresh(instance)