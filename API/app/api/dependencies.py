from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_api_key_value
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.access_control_repository import AccessControlRepository
from app.repositories.user_repository import UserRepository
from app.schemas.pagination import PaginationParams


bearer_scheme = HTTPBearer(auto_error=False)
api_key_scheme = APIKeyHeader(name=settings.api_key_header_name, auto_error=False)


def _raise_invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )


def decode_access_token_subject(token: str) -> str:
    credentials_exception = _raise_invalid_credentials()

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        login = payload.get("sub")
        token_type = payload.get("token_type")
        if not isinstance(login, str) or token_type != "access":
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    return login


async def get_pagination_params(
    page: Annotated[int, Query(ge=1, description="Numero da pagina.")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Quantidade de registros por pagina.")] = 10,
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


async def get_user_from_access_token(token: str, session: AsyncSession) -> User:
    login = decode_access_token_subject(token)

    repository = UserRepository(session)
    user = await repository.get_by_login(login)
    if user is None:
        raise _raise_invalid_credentials()
    return user


async def get_user_from_api_key(api_key: str, session: AsyncSession) -> User:
    repository = AccessControlRepository(session)
    key_hash = hash_api_key_value(api_key, settings.jwt_secret_key)
    record = await repository.get_user_api_key_by_hash(key_hash)
    if record is None or record.user is None or not record.user.ativo:
        raise _raise_invalid_credentials()

    await repository.touch_user_api_key(record)
    return record.user


async def get_current_user(
    bearer: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    api_key: str | None = Depends(api_key_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    if bearer is not None and bearer.scheme.lower() == "bearer":
        return await get_user_from_access_token(bearer.credentials, session)
    if api_key:
        return await get_user_from_api_key(api_key, session)
    raise _raise_invalid_credentials()


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.ativo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inativo")
    return current_user


def require_profile_names(*profile_names: str) -> Callable[[User], User]:
    async def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        active_profile_names = {profile.nome for profile in current_user.profiles if profile.ativo}
        if not active_profile_names.intersection(profile_names):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissao insuficiente")
        return current_user

    return dependency


def require_permission(resource_key: str, action: str) -> Callable[[User], User]:
    permission_field = {
        "create": "can_create",
        "read": "can_read",
        "update": "can_update",
        "delete": "can_delete",
    }.get(action)

    if permission_field is None:
        raise ValueError(f"Acao de permissao invalida: {action}")

    async def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        for permission in current_user.permissions:
            if permission.resource_key == resource_key and getattr(permission, permission_field, False):
                return current_user

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissao insuficiente")

    return dependency


async def get_current_admin_user(current_user: User = Depends(require_profile_names("Administrador"))) -> User:
    return current_user
