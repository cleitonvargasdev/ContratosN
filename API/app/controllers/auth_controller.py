from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.db.session import get_db_session
from app.schemas.auth import RefreshTokenRequest, TokenPair
from app.schemas.user import AuthenticatedUserRead
from app.services.auth_service import AuthService
from app.models.user import User


router = APIRouter()


def get_auth_service(session: AsyncSession = Depends(get_db_session)) -> AuthService:
    return AuthService(session)


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Login",
    description="Autentica o usuario com login e senha e retorna access e refresh tokens.",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> TokenPair:
    return await service.login(form_data.username, form_data.password)


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Refresh token",
    description="Recebe um refresh token valido e retorna um novo par de tokens.",
)
async def refresh_tokens(
    payload: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenPair:
    return await service.refresh(payload.refresh_token)


@router.get(
    "/me",
    response_model=AuthenticatedUserRead,
    summary="Usuario autenticado",
    description="Retorna os dados do usuario autenticado com base no JWT.",
)
async def read_current_user(current_user: User = Depends(get_current_active_user)) -> AuthenticatedUserRead:
    return current_user