from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounts_receivable import ContaReceber
from app.models.mobile_batch import MobileBatch, MobileBatchItem, MobileOccurrence
from app.models.receipt import Recebimento
from app.models.user import User
from app.schemas.mobile_batch import MobileBatchCreate, MobileBatchRead
from app.services.accounts_receivable_service import AccountsReceivableService


class MobileBatchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user: User, payload: MobileBatchCreate) -> MobileBatchRead:
        existing = await self.session.scalar(select(MobileBatch).where(MobileBatch.user_id == user.id, MobileBatch.source_id == payload.source_id))
        if existing is not None:
            return await self._read(existing)
        duplicate_item = await self.session.scalar(
            select(MobileBatchItem.id).where(
                MobileBatchItem.user_id == user.id,
                MobileBatchItem.source_item_id.in_([item.source_item_id for item in payload.items]),
            ).limit(1)
        )
        if duplicate_item is not None:
            raise HTTPException(409, "Uma operacao deste lote ja foi enviada em outro lote")
        now = datetime.now(UTC)
        batch = MobileBatch(user_id=user.id, source_id=payload.source_id, created_at=now)
        self.session.add(batch)
        await self.session.flush()
        for source in payload.items:
            item = MobileBatchItem(
                batch_id=batch.id, user_id=user.id, source_item_id=source.source_item_id, kind=source.kind,
                client_id=source.client_id, contract_id=source.contract_id, installment_id=source.installment_id,
                amount=None if source.amount_units is None else source.amount_units / 10000,
                latitude=None if source.latitude is None else str(source.latitude),
                longitude=None if source.longitude is None else str(source.longitude),
                gps_status=source.gps_status, device_recorded_at=source.device_recorded_at,
                server_date=now.date(),
            )
            self.session.add(item)
        await self.session.commit()
        return await self._read(batch)

    async def get(self, batch_id: int, user: User, *, admin: bool = False) -> MobileBatchRead:
        statement = select(MobileBatch).where(MobileBatch.id == batch_id)
        if not admin:
            statement = statement.where(MobileBatch.user_id == user.id)
        batch = await self.session.scalar(statement)
        if batch is None:
            raise HTTPException(404, "Lote nao encontrado")
        return await self._read(batch)

    async def execute(self, batch_id: int, user: User) -> MobileBatchRead:
        batch = await self.session.scalar(select(MobileBatch).where(MobileBatch.id == batch_id, MobileBatch.user_id == user.id).with_for_update())
        if batch is None:
            raise HTTPException(404, "Lote nao encontrado")
        if batch.status in {"processed", "blocked"}:
            return await self._read(batch)
        # A request can die after marking the batch as processing but before
        # returning its result. After the lease expires, a retry safely resumes
        # the same unprocessed children; processed children are never repeated.
        if batch.status == "processing" and batch.execution_requested_at and \
                batch.execution_requested_at > datetime.now(UTC) - timedelta(minutes=2):
            return await self._read(batch)
        now = datetime.now(UTC)
        batch_id = batch.id
        batch.status = "processing"
        batch.execution_requested_at = batch.execution_requested_at or now
        await self.session.commit()
        items = (await self.session.execute(select(MobileBatchItem).where(MobileBatchItem.batch_id == batch_id).order_by(MobileBatchItem.id))).scalars().all()
        for item in items:
            if item.processed or item.blocked:
                continue
            item_id = item.id
            try:
                await self._process_item(batch, item, user, now)
            except Exception as exc:
                await self.session.rollback()
                item = await self.session.get(MobileBatchItem, item_id)
                batch = await self.session.get(MobileBatch, batch_id)
                if item is not None and batch is not None:
                    item.blocked = True
                    item.block_reason = self._reason(exc)
                    batch.blocked = True
                    batch.block_reason = batch.block_reason or item.block_reason
                    await self.session.commit()
        batch = await self.session.get(MobileBatch, batch_id)
        if batch is None:
            raise HTTPException(404, "Lote nao encontrado")
        blocked = await self.session.scalar(select(MobileBatchItem.id).where(MobileBatchItem.batch_id == batch.id, MobileBatchItem.blocked.is_(True)).limit(1))
        batch.status = "blocked" if blocked is not None else "processed"
        batch.blocked = blocked is not None
        batch.finished_at = datetime.now(UTC)
        await self.session.commit()
        return await self._read(batch)

    async def unlock(self, batch_id: int, admin: User, reason: str) -> MobileBatchRead:
        batch = await self.session.scalar(select(MobileBatch).where(MobileBatch.id == batch_id).with_for_update())
        if batch is None:
            raise HTTPException(404, "Lote nao encontrado")
        if not batch.blocked:
            raise HTTPException(400, "Lote nao esta bloqueado")
        batch.blocked = False
        batch.status = "processed"
        batch.unlocked_at = datetime.now(UTC)
        batch.unlocked_by_id = admin.id
        batch.unlock_reason = reason
        await self.session.commit()
        return await self._read(batch)

    async def list_blocked(self) -> list[MobileBatchRead]:
        batches = (await self.session.execute(
            select(MobileBatch).where(MobileBatch.blocked.is_(True)).order_by(MobileBatch.created_at.desc())
        )).scalars().all()
        return [await self._read(batch) for batch in batches]

    async def _process_item(self, batch: MobileBatch, item: MobileBatchItem, user: User, now: datetime) -> None:
        if item.kind in {"unpaid", "closed"}:
            self.session.add(MobileOccurrence(
                batch_id=batch.id, item_id=item.id, user_id=user.id, client_id=item.client_id,
                contract_id=item.contract_id, kind=item.kind, latitude=item.latitude, longitude=item.longitude,
                gps_status=item.gps_status, device_time=item.device_recorded_at, server_date=now.date(), created_at=now,
            ))
            item.processed = True
            item.processed_at = now
            await self.session.commit()
            return
        installment = await self.session.scalar(select(ContaReceber).where(ContaReceber.id == item.installment_id).with_for_update())
        if installment is None or installment.contratos_id != item.contract_id:
            raise ValueError("Parcela ou contrato nao encontrado")
        if installment.quitado or float(installment.valor_total or 0) <= float(installment.valor_recebido or 0):
            raise ValueError("Parcela ja quitada")
        amount = float(item.amount or 0)
        if amount <= 0:
            raise ValueError("Valor do recebimento invalido")
        remaining = max(float(installment.valor_total or 0) - float(installment.valor_recebido or 0), 0)
        interest = max(amount - remaining, 0)
        receipt = Recebimento(contrato_id=item.contract_id, valor_recebido=amount, usuario_id=user.id,
            data_recebimento=now, parcela_nro=installment.parcela_nro, latitude=item.latitude,
            longitude=item.longitude, juros=interest, lote_id=batch.id, item_lote_id=item.id)
        self.session.add(receipt)
        await self.session.flush()
        installment.valor_recebido = float(installment.valor_recebido or 0) + amount
        installment.valor_juros = float(installment.valor_juros or 0) + interest
        installment.valor_total = float(installment.valor_base or 0) + float(installment.valor_juros or 0)
        installment.data_recebimento = now
        installment.quitado = float(installment.valor_recebido or 0) >= float(installment.valor_total or 0)
        item.receipt_id = receipt.recebimento_id
        item.processed = True
        item.processed_at = now
        await AccountsReceivableService(self.session)._sync_contract_by_id(item.contract_id)
        await self.session.commit()

    async def _read(self, batch: MobileBatch) -> MobileBatchRead:
        items = (await self.session.execute(select(MobileBatchItem).where(MobileBatchItem.batch_id == batch.id).order_by(MobileBatchItem.id))).scalars().all()
        return MobileBatchRead(id=batch.id, source_id=batch.source_id, user_id=batch.user_id, status=batch.status, blocked=batch.blocked,
            block_reason=batch.block_reason, items=[{"id": item.id, "source_item_id": item.source_item_id,
            "kind": item.kind, "client_id": item.client_id, "contract_id": item.contract_id,
            "installment_id": item.installment_id,
            "amount_units": None if item.amount is None else round(float(item.amount) * 10000),
            "processed": item.processed, "blocked": item.blocked, "block_reason": item.block_reason} for item in items])

    @staticmethod
    def _reason(exc: Exception) -> str:
        text = str(exc).strip() or "Falha ao processar item"
        return text[:1000]
