from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment_plan import PaymentPlan


class PaymentPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_payment_plans(self, descricao: str | None = None) -> Sequence[PaymentPlan]:
        stmt = select(PaymentPlan)
        if descricao:
            stmt = stmt.where(PaymentPlan.descricao.ilike(f"%{descricao}%"))
        result = await self.session.execute(stmt.order_by(PaymentPlan.plano_id))
        return result.scalars().all()

    async def get_by_id(self, plano_id: int) -> PaymentPlan | None:
        return await self.session.get(PaymentPlan, plano_id)

    async def create(self, payload: dict[str, object]) -> PaymentPlan:
        record = PaymentPlan(**payload)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def update(self, record: PaymentPlan, payload: dict[str, object]) -> PaymentPlan:
        for field, value in payload.items():
            setattr(record, field, value)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def delete(self, record: PaymentPlan) -> None:
        await self.session.delete(record)
        await self.session.commit()