from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_config import ApiConfig
from app.models.user import User
from app.schemas.api_config import ApiConfigListParams


class ApiConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self, params: ApiConfigListParams) -> tuple[Sequence[tuple[ApiConfig, str | None]], int]:
        stmt = select(ApiConfig, User.nome).outerjoin(User, User.id == ApiConfig.usuario_id)
        count_stmt = select(func.count()).select_from(ApiConfig)

        if params.nome_api:
            stmt = stmt.where(ApiConfig.nome_api.ilike(f"%{params.nome_api}%"))
            count_stmt = count_stmt.where(ApiConfig.nome_api.ilike(f"%{params.nome_api}%"))
        if params.usuario_id is not None:
            stmt = stmt.where(ApiConfig.usuario_id == params.usuario_id)
            count_stmt = count_stmt.where(ApiConfig.usuario_id == params.usuario_id)

        stmt = stmt.order_by(ApiConfig.api_id).offset((params.page - 1) * params.page_size).limit(params.page_size)
        result = await self.session.execute(stmt)
        total = await self.session.scalar(count_stmt)
        return result.all(), int(total or 0)

    async def get_by_id(self, api_id: int) -> ApiConfig | None:
        return await self.session.get(ApiConfig, api_id)

    async def create(self, payload: dict[str, object]) -> ApiConfig:
        record = ApiConfig(**payload)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def update(self, record: ApiConfig, payload: dict[str, object]) -> ApiConfig:
        for field, value in payload.items():
            setattr(record, field, value)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def delete(self, record: ApiConfig) -> None:
        await self.session.delete(record)
        await self.session.commit()