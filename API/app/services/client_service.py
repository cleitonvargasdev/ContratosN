from sqlalchemy import func, select
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Cliente
from app.models.client_score_log import ClientScoreLog
from app.models.parameter import Parametro
from app.models.user import User
from app.repositories.client_repository import ClientRepository
from app.schemas.client import ClientCobradorOptionRead, ClientCreate, ClientListParams, ClientListResponse, ClientScoreLogListResponse, ClientScoreLogRead, ClientUpdate
from app.services.client_metrics_service import ClientMetricsService
from app.services.location_service import LocationService


class ClientService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = ClientRepository(session)
        self.location_service = LocationService(session)
        self.client_metrics_service = ClientMetricsService(session)

    async def list_clients(self, params: ClientListParams) -> ClientListResponse:
        clients, total = await self.repository.list_all(params)
        return ClientListResponse(items=list(clients), total=total, page=params.page, page_size=params.page_size)

    async def get_client(self, client_id: int) -> Cliente | None:
        return await self.repository.get_by_id(client_id)

    async def list_client_score_logs(self, client_id: int, *, page: int, page_size: int) -> ClientScoreLogListResponse:
        total = await self.repository.session.scalar(
            select(func.count())
            .select_from(ClientScoreLog)
            .where(ClientScoreLog.cliente_id == client_id)
        )
        result = await self.repository.session.execute(
            select(ClientScoreLog)
            .where(ClientScoreLog.cliente_id == client_id)
            .order_by(ClientScoreLog.data_hora_evento.desc(), ClientScoreLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [ClientScoreLogRead.model_validate(item) for item in result.scalars().all()]
        return ClientScoreLogListResponse(items=items, total=int(total or 0), page=page, page_size=page_size)

    async def reprocess_client_score(self, client_id: int) -> Cliente | None:
        client = await self.client_metrics_service.reprocess_client_score(client_id)
        if client is None:
            return None
        await self.repository.session.commit()
        return await self.repository.get_by_id(client_id)

    async def list_active_cobradores(self) -> list[ClientCobradorOptionRead]:
        result = await self.repository.session.execute(
            select(User)
            .where(User.ativo.is_(True), func.trim(func.lower(User.funcao)) == "cobrador")
            .order_by(User.nome)
        )
        return [ClientCobradorOptionRead.model_validate(item) for item in result.scalars().all()]

    async def create_client(self, payload: ClientCreate, current_user_id: int | None = None) -> Cliente:
        payload_data = await self._normalize_payload(payload.model_dump())
        payload_data.setdefault("score", await self._resolve_default_score())
        payload_data.setdefault("ativo", True)
        payload_data.setdefault("bloqueado", False)
        payload_data.setdefault("data_add", datetime.now(UTC))
        if current_user_id is not None:
            payload_data.setdefault("user_add", current_user_id)

        client = Cliente(**payload_data)
        return await self.repository.create(client)

    async def update_client(self, client_id: int, payload: ClientUpdate) -> Cliente | None:
        client = await self.repository.get_by_id(client_id)
        if client is None:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        normalized = await self._normalize_payload(update_data)
        return await self.repository.update_fields(client, normalized)

    async def delete_client(self, client_id: int) -> bool:
        client = await self.repository.get_by_id(client_id)
        if client is None:
            return False
        try:
            await self.repository.delete(client)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cliente vinculado a outros registros") from exc
        return True

    async def _normalize_payload(self, values: dict[str, object]) -> dict[str, object]:
        values = await self._normalize_company_location(values)
        values = await self._normalize_responsible_location(values)
        return values

    async def _normalize_company_location(self, values: dict[str, object]) -> dict[str, object]:
        location_payload = {
            "uf": values.get("uf"),
            "cidade_id": values.get("cidade_id"),
            "bairro_id": values.get("bairro_id"),
            "cep": values.get("cep"),
            "endereco": values.get("endereco"),
        }
        normalized = await self.location_service.normalize_user_location_fields(location_payload)
        values["uf"] = normalized.get("uf")
        values["cidade_id"] = normalized.get("cidade_id")
        values["bairro_id"] = normalized.get("bairro_id")
        values["cep"] = normalized.get("cep")
        return values

    async def _normalize_responsible_location(self, values: dict[str, object]) -> dict[str, object]:
        location_payload = {
            "uf": values.get("uf_responsavel"),
            "cidade_id": values.get("cidade_responsavel_id"),
            "bairro_id": values.get("bairro_id_responsavel"),
            "cep": values.get("cep_responsavel"),
            "endereco": values.get("endereco_responsavel"),
        }
        normalized = await self.location_service.normalize_user_location_fields(location_payload)
        values["uf_responsavel"] = normalized.get("uf")
        values["cidade_responsavel_id"] = normalized.get("cidade_id")
        values["bairro_id_responsavel"] = normalized.get("bairro_id")
        values["cep_responsavel"] = normalized.get("cep")
        return values

    async def _resolve_default_score(self) -> int:
        result = await self.repository.session.execute(select(Parametro).order_by(Parametro.parametros_id.asc()).limit(1))
        parameter = result.scalar_one_or_none()
        if parameter is None or parameter.score_valor_inicial is None:
            return 1000
        return int(parameter.score_valor_inicial)