from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import build_api_key_prefix, generate_api_key_value, hash_api_key_value
from app.models.access_control import Profile, ProfilePermission
from app.repositories.access_control_repository import AccessControlRepository
from app.repositories.user_repository import UserRepository
from app.schemas.access_control import PermissionResourceRead, ProfileCreate, ProfilePermissionWrite, ProfileRead, ProfileUpdate, UserApiKeyInfo, UserApiKeySecret


RESOURCE_CATALOG: tuple[PermissionResourceRead, ...] = (
    PermissionResourceRead(resource_key="acesso_web", resource_label="Acesso Web", resource_group="Sistema", supported_actions=["read"]),
    PermissionResourceRead(resource_key="dashboard", resource_label="Dashboard", resource_group="Sistema", supported_actions=["read"]),
    PermissionResourceRead(resource_key="usuarios", resource_label="Usuarios", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="clientes", resource_label="Clientes", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="solicitacoes", resource_label="Solicitacoes", resource_group="Cadastros", supported_actions=["read", "update"]),
    PermissionResourceRead(resource_key="contratos", resource_label="Contratos", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="apis", resource_label="APIs", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="usuarios_api_keys", resource_label="Chaves de API dos usuarios", resource_group="Seguranca", supported_actions=["read", "update"]),
    PermissionResourceRead(resource_key="perfis", resource_label="Perfis e permissoes", resource_group="Seguranca", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="planos_pagamentos", resource_label="Planos de Pagamento", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="localidades_ufs", resource_label="UFs", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="localidades_cidades", resource_label="Cidades", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="localidades_bairros", resource_label="Bairros", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
    PermissionResourceRead(resource_key="localidades_feriados", resource_label="Feriados", resource_group="Cadastros", supported_actions=["create", "read", "update", "delete"]),
)


class AccessControlService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = AccessControlRepository(session)
        self.user_repository = UserRepository(session)

    async def list_profiles(self, term: str | None = None) -> list[ProfileRead]:
        return [ProfileRead.model_validate(item) for item in await self.repository.list_profiles(term)]

    async def get_profile(self, profile_id: int) -> ProfileRead | None:
        record = await self.repository.get_profile_by_id(profile_id)
        if record is None:
            return None
        return ProfileRead.model_validate(record)

    async def create_profile(self, payload: ProfileCreate) -> ProfileRead:
        if await self.repository.get_profile_by_name(payload.nome):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Perfil ja cadastrado")

        profile = Profile(nome=payload.nome, descricao=payload.descricao, ativo=payload.ativo)
        profile.permissions = self._build_permission_entities(payload.permissions)
        saved = await self.repository.create_profile(profile)
        return ProfileRead.model_validate(saved)

    async def update_profile(self, profile_id: int, payload: ProfileUpdate) -> ProfileRead | None:
        profile = await self.repository.get_profile_by_id(profile_id)
        if profile is None:
            return None

        if payload.nome and payload.nome.lower() != profile.nome.lower():
            existing = await self.repository.get_profile_by_name(payload.nome)
            if existing is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Perfil ja cadastrado")
            profile.nome = payload.nome

        if payload.descricao is not None:
            profile.descricao = payload.descricao
        if payload.ativo is not None:
            profile.ativo = payload.ativo
        if payload.permissions is not None:
            profile.permissions.clear()
            await self.session.flush()
            profile.permissions = self._build_permission_entities(payload.permissions)

        saved = await self.repository.save_profile(profile)
        return ProfileRead.model_validate(saved)

    async def delete_profile(self, profile_id: int) -> bool:
        profile = await self.repository.get_profile_by_id(profile_id)
        if profile is None:
            return False

        if await self.repository.count_users_by_profile(profile_id) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Perfil vinculado a usuarios e nao pode ser removido",
            )

        await self.repository.delete_profile(profile)
        return True

    def list_permission_resources(self) -> list[PermissionResourceRead]:
        return list(RESOURCE_CATALOG)

    async def rotate_user_api_key(self, user_id: int) -> UserApiKeySecret | None:
        user = await self.user_repository.get_by_id(user_id)
        if user is None:
            return None

        raw_key = generate_api_key_value()
        key_hash = hash_api_key_value(raw_key, settings.jwt_secret_key)
        record = await self.repository.upsert_user_api_key(user_id=user_id, key_hash=key_hash, key_prefix=build_api_key_prefix(raw_key))
        payload = UserApiKeyInfo.model_validate(record).model_dump()
        return UserApiKeySecret(**payload, api_key=raw_key)

    async def get_user_api_key_info(self, user_id: int) -> UserApiKeyInfo | None:
        record = await self.repository.get_user_api_key_by_user_id(user_id)
        if record is None:
            return None
        return UserApiKeyInfo.model_validate(record)

    def _build_permission_entities(self, permissions: list[ProfilePermissionWrite]) -> list[ProfilePermission]:
        normalized: dict[str, ProfilePermissionWrite] = {}
        for item in permissions:
            if not any((item.can_read, item.can_create, item.can_update, item.can_delete)):
                continue
            normalized[item.resource_key] = item

        entities: list[ProfilePermission] = []
        for item in normalized.values():
            entities.append(
                ProfilePermission(
                    resource_key=item.resource_key,
                    resource_label=item.resource_label,
                    can_read=item.can_read,
                    can_create=item.can_create,
                    can_update=item.can_update,
                    can_delete=item.can_delete,
                )
            )
        return entities
