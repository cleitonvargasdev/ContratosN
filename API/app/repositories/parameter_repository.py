from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parameter import Parametro


class ParameterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_singleton(self) -> Parametro | None:
        result = await self.session.execute(select(Parametro).order_by(Parametro.parametros_id.asc()).limit(1))
        return result.scalar_one_or_none()

    async def add(self, parameter: Parametro) -> Parametro:
        self.session.add(parameter)
        await self.session.commit()
        await self.session.refresh(parameter)
        return parameter

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh(self, parameter: Parametro) -> None:
        await self.session.refresh(parameter)