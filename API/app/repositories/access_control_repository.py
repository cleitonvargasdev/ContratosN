from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.access_control import Profile, ProfilePermission, UserApiKey
from app.models.user import User


class AccessControlRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_profiles(self, term: str | None = None) -> Sequence[Profile]:
        stmt = select(Profile).options(selectinload(Profile.permissions)).order_by(Profile.nome)
        if term:
            stmt = stmt.where(Profile.nome.ilike(f"%{term}%"))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_profile_by_id(self, profile_id: int) -> Profile | None:
        stmt = select(Profile).options(selectinload(Profile.permissions)).where(Profile.id == profile_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_profile_by_name(self, nome: str) -> Profile | None:
        stmt = select(Profile).options(selectinload(Profile.permissions)).where(func.lower(Profile.nome) == nome.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_profile(self, profile: Profile) -> Profile:
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return await self.get_profile_by_id(profile.id) or profile

    async def save_profile(self, profile: Profile) -> Profile:
        await self.session.commit()
        await self.session.refresh(profile)
        return await self.get_profile_by_id(profile.id) or profile

    async def delete_profile(self, profile: Profile) -> None:
        await self.session.delete(profile)
        await self.session.commit()

    async def count_users_by_profile(self, profile_id: int) -> int:
        stmt = select(func.count()).select_from(User).where(User.perfil_id == profile_id)
        total = await self.session.scalar(stmt)
        return int(total or 0)

    async def get_user_api_key_by_hash(self, key_hash: str) -> UserApiKey | None:
        stmt = (
            select(UserApiKey)
            .options(
                selectinload(UserApiKey.user)
                .selectinload(User.profile)
                .selectinload(Profile.permissions),
                selectinload(UserApiKey.user).selectinload(User.api_key),
            )
            .where(UserApiKey.key_hash == key_hash, UserApiKey.active.is_(True))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_api_key_by_user_id(self, user_id: int) -> UserApiKey | None:
        stmt = select(UserApiKey).where(UserApiKey.user_id == user_id, UserApiKey.active.is_(True))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_user_api_key(self, user_id: int, key_hash: str, key_prefix: str) -> UserApiKey:
        record = await self.get_user_api_key_by_user_id(user_id)
        now = datetime.now(timezone.utc)

        if record is None:
            record = UserApiKey(user_id=user_id, key_hash=key_hash, key_prefix=key_prefix, active=True)
            self.session.add(record)
        else:
            record.key_hash = key_hash
            record.key_prefix = key_prefix
            record.active = True
            record.rotated_at = now

        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def touch_user_api_key(self, record: UserApiKey) -> None:
        record.last_used_at = datetime.now(timezone.utc)
        await self.session.commit()
