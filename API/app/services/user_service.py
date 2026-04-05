from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.repositories.access_control_repository import AccessControlRepository
from app.models.user import User
from app.realtime.user_events import user_event_broker
from app.services.location_service import LocationService
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserListParams, UserListResponse, UserUpdate


USER_LIST_VISIBLE_FIELDS = {"nome", "login", "email", "funcao", "telefone", "celular", "ativo", "cpf", "uf"}


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = UserRepository(session)
        self.access_repository = AccessControlRepository(session)
        self.location_service = LocationService(session)

    async def list_users(self, params: UserListParams) -> UserListResponse:
        users, total = await self.repository.list_all(params)
        return UserListResponse(items=list(users), total=total, page=params.page, page_size=params.page_size)

    async def get_user(self, user_id: int) -> User | None:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            return None

        try:
            return await self.location_service.backfill_user_cep(user)
        except Exception:
            return user

    async def get_user_by_login(self, login: str) -> User | None:
        return await self.repository.get_by_login(login)

    async def create_user(self, payload: UserCreate) -> User:
        if await self.repository.get_by_login(payload.login):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Login ja cadastrado")
        if await self.repository.get_by_email(str(payload.email)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email ja cadastrado")
        await self._validate_profile(payload.perfil_id)

        payload_data = payload.model_dump(exclude={"senha"})
        payload_data = await self.location_service.normalize_user_location_fields(payload_data)
        user = User(**payload_data, senha_hash=hash_password(payload.senha))
        created_user = await self.repository.create(user)
        await user_event_broker.broadcast("created", user_id=created_user.id, changed_fields=payload_data.keys())
        return created_user

    async def update_user(self, user_id: int, payload: UserUpdate) -> User | None:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            return None

        if payload.login and payload.login != user.login:
            existing_login = await self.repository.get_by_login(payload.login)
            if existing_login is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Login ja cadastrado")

        if payload.email and str(payload.email) != user.email:
            existing_email = await self.repository.get_by_email(str(payload.email))
            if existing_email is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email ja cadastrado")

        await self._validate_profile(payload.perfil_id)

        update_data = payload.model_dump(exclude_unset=True, exclude={"senha"})
        update_data = await self.location_service.normalize_user_location_fields(update_data)
        changed_fields = [field for field in update_data if field in USER_LIST_VISIBLE_FIELDS]
        if payload.senha:
            update_data["senha_hash"] = hash_password(payload.senha)

        updated_user = await self.repository.update_fields(user, update_data)
        if changed_fields:
            await user_event_broker.broadcast("updated", user_id=updated_user.id, changed_fields=changed_fields)
        return updated_user

    async def delete_user(self, user_id: int) -> bool:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            return False
        await self.repository.delete(user)
        await user_event_broker.broadcast("deleted", user_id=user_id)
        return True

    async def _validate_profile(self, profile_id: int | None) -> None:
        if profile_id is None:
            return
        if await self.access_repository.get_profile_by_id(profile_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Perfil informado nao existe")
