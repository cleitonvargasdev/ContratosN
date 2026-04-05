from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.access_control import Profile
from app.models.user import User
from app.schemas.user import UserListParams, UserUpdate


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _load_options() -> tuple:
        return (
            selectinload(User.profiles).selectinload(Profile.permissions),
            selectinload(User.api_key),
        )

    async def list_all(self, params: UserListParams) -> tuple[Sequence[User], int]:
        filters = []

        if params.nome:
            filters.append(User.nome.ilike(f"%{params.nome}%"))
        if params.email:
            filters.append(User.email == str(params.email))
        if params.ativo is not None:
            filters.append(User.ativo == params.ativo)

        stmt = select(User).options(*self._load_options())
        count_stmt = select(func.count()).select_from(User)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        stmt = stmt.order_by(User.id).offset((params.page - 1) * params.page_size).limit(params.page_size)

        result = await self.session.execute(stmt)
        total = await self.session.scalar(count_stmt)
        return result.scalars().all(), int(total or 0)

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).options(*self._load_options()).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_login(self, login: str) -> User | None:
        result = await self.session.execute(select(User).options(*self._load_options()).where(User.login == login))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).options(*self._load_options()).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user: User, payload: UserUpdate) -> User:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_fields(self, user: User, values: dict[str, object]) -> User:
        for field, value in values.items():
            setattr(user, field, value)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.commit()
