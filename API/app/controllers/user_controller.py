from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_pagination_params, get_user_from_access_token, require_permission
from app.db.session import AsyncSessionLocal, get_db_session
from app.models.user import User
from app.realtime.user_events import user_event_broker
from app.schemas.access_control import UserApiKeyInfo, UserApiKeySecret
from app.schemas.user import UserCreate, UserListParams, UserListResponse, UserRead, UserUpdate
from app.schemas.pagination import PaginationParams
from app.services.access_control_service import AccessControlService
from app.services.user_service import UserService


router = APIRouter(dependencies=[Depends(get_current_active_user)])
ws_router = APIRouter()


def get_user_service(session: AsyncSession = Depends(get_db_session)) -> UserService:
    return UserService(session)


def get_access_control_service(session: AsyncSession = Depends(get_db_session)) -> AccessControlService:
    return AccessControlService(session)


@ws_router.websocket("/ws")
async def users_updates_websocket(websocket: WebSocket, token: str = Query(...)) -> None:
    async with AsyncSessionLocal() as session:
        try:
            await get_user_from_access_token(token, session)
        except HTTPException:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await user_event_broker.connect(websocket)

    try:
        await websocket.send_json({"resource": "usuarios", "event": "connected"})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await user_event_broker.disconnect(websocket)


@router.get(
    "/",
    response_model=UserListResponse,
    summary="Listar usuarios",
    description="Retorna usuarios com paginacao e filtros opcionais por nome, email e status.",
    responses={
        200: {
            "description": "Lista paginada de usuarios.",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "nome": "Ana Souza",
                                "login": "ana.souza",
                                "email": "ana.souza@example.com",
                                "telefone": "11990000001",
                                "ativo": True,
                                "created_at": "2026-04-01T10:00:00Z",
                                "updated_at": "2026-04-01T10:00:00Z",
                            }
                        ],
                        "total": 10,
                        "page": 1,
                        "page_size": 10,
                    }
                }
            },
        }
    },
)
async def list_users(
    pagination: PaginationParams = Depends(get_pagination_params),
    nome: Annotated[str | None, Query(description="Filtra por parte do nome.")] = None,
    email: Annotated[str | None, Query(description="Filtra por email exato.")] = None,
    ativo: Annotated[bool | None, Query(description="Filtra por status ativo/inativo.")] = None,
    _: User = Depends(require_permission("usuarios", "read")),
    service: UserService = Depends(get_user_service),
) -> UserListResponse:
    params = UserListParams(
        page=pagination.page,
        page_size=pagination.page_size,
        nome=nome,
        email=email,
        ativo=ativo,
    )
    return await service.list_users(params)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Buscar usuario por ID",
    description="Retorna um usuario especifico a partir do identificador.",
    responses={
        200: {
            "description": "Usuario encontrado.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "nome": "Ana Souza",
                        "login": "ana.souza",
                        "email": "ana.souza@example.com",
                        "telefone": "11990000001",
                        "ativo": True,
                        "created_at": "2026-04-01T10:00:00Z",
                        "updated_at": "2026-04-01T10:00:00Z",
                    }
                }
            },
        },
        404: {"description": "Usuario nao encontrado."},
    },
)
async def get_user(
    user_id: int,
    _: User = Depends(require_permission("usuarios", "read")),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    user = await service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado")
    return user


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar usuario",
    description="Cria um novo usuario na base de dados.",
    responses={
        201: {
            "description": "Usuario criado com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 11,
                        "nome": "Maria Oliveira",
                        "login": "maria.oliveira",
                        "email": "maria.oliveira@example.com",
                        "telefone": "11998887766",
                        "ativo": True,
                        "created_at": "2026-04-01T11:00:00Z",
                        "updated_at": "2026-04-01T11:00:00Z",
                    }
                }
            },
        },
        422: {"description": "Payload invalido."},
    },
)
async def create_user(
    payload: UserCreate,
    _: User = Depends(require_permission("usuarios", "create")),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.create_user(payload)


@router.put(
    "/{user_id}",
    response_model=UserRead,
    summary="Atualizar usuario",
    description="Atualiza os dados de um usuario existente.",
    responses={
        200: {
            "description": "Usuario atualizado com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "nome": "Ana Souza Atualizada",
                        "login": "ana.souza",
                        "email": "ana.souza@example.com",
                        "telefone": "11991112222",
                        "ativo": True,
                        "created_at": "2026-04-01T10:00:00Z",
                        "updated_at": "2026-04-01T12:00:00Z",
                    }
                }
            },
        },
        404: {"description": "Usuario nao encontrado."},
        422: {"description": "Payload invalido."},
    },
)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    _: User = Depends(require_permission("usuarios", "update")),
    service: UserService = Depends(get_user_service),
) -> UserRead:
    user = await service.update_user(user_id, payload)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado")
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir usuario",
    description="Remove um usuario existente pelo identificador.",
    responses={204: {"description": "Usuario removido com sucesso."}, 404: {"description": "Usuario nao encontrado."}},
)
async def delete_user(
    user_id: int,
    _: User = Depends(require_permission("usuarios", "delete")),
    service: UserService = Depends(get_user_service),
) -> Response:
    deleted = await service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{user_id}/api-key", response_model=UserApiKeyInfo, summary="Consultar metadados da chave de API do usuario")
async def get_user_api_key(
    user_id: int,
    _: User = Depends(require_permission("usuarios_api_keys", "read")),
    service: AccessControlService = Depends(get_access_control_service),
) -> UserApiKeyInfo:
    record = await service.get_user_api_key_info(user_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chave de API nao encontrada")
    return record


@router.post("/{user_id}/api-key", response_model=UserApiKeySecret, summary="Gerar ou rotacionar chave de API do usuario")
async def rotate_user_api_key(
    user_id: int,
    _: User = Depends(require_permission("usuarios_api_keys", "update")),
    service: AccessControlService = Depends(get_access_control_service),
) -> UserApiKeySecret:
    record = await service.rotate_user_api_key(user_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado")
    return record
