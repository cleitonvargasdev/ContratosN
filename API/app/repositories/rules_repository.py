from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rules import RegraJuros


class RulesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active_regra_juros(self) -> list[RegraJuros]:
        result = await self.session.execute(
            select(RegraJuros).where(RegraJuros.ativo.is_(True)).order_by(RegraJuros.descricao, RegraJuros.regra_juros_id)
        )
        return list(result.scalars().all())