from fastapi import HTTPException, status

from app.repositories.api_config_repository import ApiConfigRepository
from app.repositories.user_repository import UserRepository
from app.schemas.api_config import ApiConfigCreate, ApiConfigListParams, ApiConfigListResponse, ApiConfigRead, ApiConfigUpdate


class ApiConfigService:
    def __init__(self, session) -> None:
        self.repository = ApiConfigRepository(session)
        self.user_repository = UserRepository(session)

    async def list_api_configs(self, params: ApiConfigListParams) -> ApiConfigListResponse:
        rows, total = await self.repository.list_all(params)
        items = [self._build_read_model(record, usuario_nome) for record, usuario_nome in rows]
        return ApiConfigListResponse(items=items, total=total, page=params.page, page_size=params.page_size)

    async def get_api_config(self, api_id: int) -> ApiConfigRead | None:
        record = await self.repository.get_by_id(api_id)
        if record is None:
            return None
        usuario_nome = None
        if record.usuario_id is not None:
            user = await self.user_repository.get_by_id(record.usuario_id)
            usuario_nome = user.nome if user else None
        return self._build_read_model(record, usuario_nome)

    async def create_api_config(self, payload: ApiConfigCreate) -> ApiConfigRead:
        data = await self._normalize_payload(payload.model_dump())
        record = await self.repository.create(data)
        return await self.get_api_config(record.api_id) or self._build_read_model(record, None)

    async def update_api_config(self, api_id: int, payload: ApiConfigUpdate) -> ApiConfigRead | None:
        record = await self.repository.get_by_id(api_id)
        if record is None:
            return None
        data = await self._normalize_payload(payload.model_dump(exclude_unset=True), partial=True)
        saved = await self.repository.update(record, data)
        return await self.get_api_config(saved.api_id)

    async def delete_api_config(self, api_id: int) -> bool:
        record = await self.repository.get_by_id(api_id)
        if record is None:
            return False
        await self.repository.delete(record)
        return True

    async def _normalize_payload(self, values: dict[str, object], partial: bool = False) -> dict[str, object]:
        nome_api = values.get("nome_api")
        if not partial and nome_api is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nome da API obrigatorio")
        if nome_api is not None and not str(nome_api).strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nome da API obrigatorio")

        usuario_id = values.get("usuario_id")
        if usuario_id is not None:
            user = await self.user_repository.get_by_id(int(usuario_id))
            if user is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario vinculado nao encontrado")

        return values

    @staticmethod
    def _build_read_model(record, usuario_nome: str | None) -> ApiConfigRead:
        return ApiConfigRead.model_validate({
            "api_id": record.api_id,
            "usuario_id": record.usuario_id,
            "usuario_nome": usuario_nome,
            "nome_api": record.nome_api,
            "funcionalidade": record.funcionalidade,
            "url": record.url,
            "key1": record.key1,
            "value1": record.value1,
            "key2": record.key2,
            "value2": record.value2,
            "key3": record.key3,
            "value3": record.value3,
            "key4": record.key4,
            "value4": record.value4,
            "key5": record.key5,
            "value5": record.value5,
            "body": record.body,
        })