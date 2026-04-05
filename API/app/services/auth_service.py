from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenPair


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = UserRepository(session)

    @staticmethod
    def _ensure_web_access(user: User) -> None:
        has_access = any(permission.resource_key == "acesso_web" and permission.can_read for permission in user.permissions)
        if not has_access:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão de acesso")

    def _build_token_pair(self, user: User) -> TokenPair:
        token_data = {"sub": user.login}
        access_token = create_access_token(
            data={**token_data, "token_type": "access"},
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            expires_minutes=settings.jwt_access_token_expire_minutes,
        )
        refresh_token = create_access_token(
            data={**token_data, "token_type": "refresh"},
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            expires_minutes=settings.jwt_refresh_token_expire_minutes,
        )
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    async def authenticate_user(self, login: str, password: str) -> User:
        user = await self.repository.get_by_login(login)
        if user is None or not verify_password(password, user.senha_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login ou senha invalidos")
        if not user.ativo:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inativo")
        self._ensure_web_access(user)
        return user

    async def login(self, login: str, password: str) -> TokenPair:
        user = await self.authenticate_user(login, password)
        return self._build_token_pair(user)

    async def refresh(self, refresh_token: str) -> TokenPair:
        credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalido")

        try:
            payload = jwt.decode(refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            login = payload.get("sub")
            token_type = payload.get("token_type")
            if not isinstance(login, str) or token_type != "refresh":
                raise credentials_exception
        except JWTError as exc:
            raise credentials_exception from exc

        user = await self.repository.get_by_login(login)
        if user is None or not user.ativo:
            raise credentials_exception
        self._ensure_web_access(user)
        return self._build_token_pair(user)