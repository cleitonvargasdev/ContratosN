from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.rules_repository import RulesRepository
from app.schemas.rules import RegraComissaoOptionRead, RegraJurosOptionRead


class RulesService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = RulesRepository(session)

    async def list_active_regra_juros(self) -> list[RegraJurosOptionRead]:
        return [RegraJurosOptionRead.model_validate(item) for item in await self.repository.list_active_regra_juros()]

    async def list_active_regra_comissao(self) -> list[RegraComissaoOptionRead]:
        return [RegraComissaoOptionRead.model_validate(item) for item in await self.repository.list_active_regra_comissao()]