from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, require_permission
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.location import AddressLookupResponse, BairroCreate, BairroRead, BairroUpdate, CidadeCreate, CidadeRead, CidadeUpdate, FeriadoCreate, FeriadoRead, FeriadoUpdate, UFCreate, UFRead, UFUpdate
from app.services.location_service import LocationService


router = APIRouter(dependencies=[Depends(get_current_active_user)])


def get_location_service(session: AsyncSession = Depends(get_db_session)) -> LocationService:
    return LocationService(session)


@router.get("/ufs", response_model=list[UFRead], summary="Listar UFs")
async def list_ufs(
    term: Annotated[str | None, Query(description="Filtro por sigla ou nome da UF.")] = None,
    _: User = Depends(require_permission("localidades_ufs", "read")),
    service: LocationService = Depends(get_location_service),
) -> list[UFRead]:
    return list(await service.list_ufs(term))


@router.get("/ufs/{uf_id}", response_model=UFRead, summary="Buscar UF")
async def get_uf(
    uf_id: int,
    _: User = Depends(require_permission("localidades_ufs", "read")),
    service: LocationService = Depends(get_location_service),
) -> UFRead:
    record = await service.get_uf(uf_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UF nao encontrada")
    return record


@router.post("/ufs", response_model=UFRead, status_code=status.HTTP_201_CREATED, summary="Criar UF")
async def create_uf(
    payload: UFCreate,
    _: User = Depends(require_permission("localidades_ufs", "create")),
    service: LocationService = Depends(get_location_service),
) -> UFRead:
    return await service.create_uf(payload)


@router.put("/ufs/{uf_id}", response_model=UFRead, summary="Atualizar UF")
async def update_uf(
    uf_id: int,
    payload: UFUpdate,
    _: User = Depends(require_permission("localidades_ufs", "update")),
    service: LocationService = Depends(get_location_service),
) -> UFRead:
    record = await service.update_uf(uf_id, payload)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UF nao encontrada")
    return record


@router.delete("/ufs/{uf_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir UF")
async def delete_uf(
    uf_id: int,
    _: User = Depends(require_permission("localidades_ufs", "delete")),
    service: LocationService = Depends(get_location_service),
) -> Response:
    deleted = await service.delete_uf(uf_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="UF nao encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/cidades", response_model=list[CidadeRead], summary="Listar cidades por UF")
async def list_cidades(
    uf: Annotated[str | None, Query(min_length=2, max_length=2)] = None,
    nome: Annotated[str | None, Query(description="Filtro por nome da cidade.")] = None,
    _: User = Depends(require_permission("localidades_cidades", "read")),
    service: LocationService = Depends(get_location_service),
) -> list[CidadeRead]:
    return list(await service.list_cidades(uf, nome))


@router.get("/cidades/{cidade_id}", response_model=CidadeRead, summary="Buscar cidade")
async def get_cidade(
    cidade_id: int,
    _: User = Depends(require_permission("localidades_cidades", "read")),
    service: LocationService = Depends(get_location_service),
) -> CidadeRead:
    record = await service.get_cidade(cidade_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cidade nao encontrada")
    return record


@router.post("/cidades", response_model=CidadeRead, status_code=status.HTTP_201_CREATED, summary="Criar cidade")
async def create_cidade(
    payload: CidadeCreate,
    _: User = Depends(require_permission("localidades_cidades", "create")),
    service: LocationService = Depends(get_location_service),
) -> CidadeRead:
    return await service.create_cidade_payload(payload)


@router.put("/cidades/{cidade_id}", response_model=CidadeRead, summary="Atualizar cidade")
async def update_cidade(
    cidade_id: int,
    payload: CidadeUpdate,
    _: User = Depends(require_permission("localidades_cidades", "update")),
    service: LocationService = Depends(get_location_service),
) -> CidadeRead:
    record = await service.update_cidade(cidade_id, payload)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cidade nao encontrada")
    return record


@router.delete("/cidades/{cidade_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir cidade")
async def delete_cidade(
    cidade_id: int,
    _: User = Depends(require_permission("localidades_cidades", "delete")),
    service: LocationService = Depends(get_location_service),
) -> Response:
    deleted = await service.delete_cidade(cidade_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cidade nao encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/bairros", response_model=list[BairroRead], summary="Listar bairros por cidade")
async def list_bairros(
    cidade_id: Annotated[int | None, Query(gt=0)] = None,
    nome: Annotated[str | None, Query(description="Filtro por nome do bairro.")] = None,
    _: User = Depends(require_permission("localidades_bairros", "read")),
    service: LocationService = Depends(get_location_service),
) -> list[BairroRead]:
    return list(await service.list_bairros(cidade_id, nome))


@router.get("/bairros/{bairro_id}", response_model=BairroRead, summary="Buscar bairro")
async def get_bairro(
    bairro_id: int,
    _: User = Depends(require_permission("localidades_bairros", "read")),
    service: LocationService = Depends(get_location_service),
) -> BairroRead:
    record = await service.get_bairro(bairro_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bairro nao encontrado")
    return record


@router.post("/bairros", response_model=BairroRead, status_code=status.HTTP_201_CREATED, summary="Criar bairro")
async def create_bairro(
    payload: BairroCreate,
    _: User = Depends(require_permission("localidades_bairros", "create")),
    service: LocationService = Depends(get_location_service),
) -> BairroRead:
    return await service.create_bairro_payload(payload)


@router.put("/bairros/{bairro_id}", response_model=BairroRead, summary="Atualizar bairro")
async def update_bairro(
    bairro_id: int,
    payload: BairroUpdate,
    _: User = Depends(require_permission("localidades_bairros", "update")),
    service: LocationService = Depends(get_location_service),
) -> BairroRead:
    record = await service.update_bairro(bairro_id, payload)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bairro nao encontrado")
    return record


@router.delete("/bairros/{bairro_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir bairro")
async def delete_bairro(
    bairro_id: int,
    _: User = Depends(require_permission("localidades_bairros", "delete")),
    service: LocationService = Depends(get_location_service),
) -> Response:
    deleted = await service.delete_bairro(bairro_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bairro nao encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/feriados", response_model=list[FeriadoRead], summary="Listar feriados")
async def list_feriados(
    nivel: Annotated[int | None, Query(ge=1, le=3)] = None,
    uf: Annotated[str | None, Query(min_length=2, max_length=2)] = None,
    cidade_id: Annotated[int | None, Query(gt=0)] = None,
    descricao: Annotated[str | None, Query(description="Filtro por descricao do feriado.")] = None,
    _: User = Depends(require_permission("localidades_feriados", "read")),
    service: LocationService = Depends(get_location_service),
) -> list[FeriadoRead]:
    return await service.list_feriados(nivel=nivel, uf=uf, cidade_id=cidade_id, descricao=descricao)


@router.get("/feriados/{feriado_id}", response_model=FeriadoRead, summary="Buscar feriado")
async def get_feriado(
    feriado_id: int,
    _: User = Depends(require_permission("localidades_feriados", "read")),
    service: LocationService = Depends(get_location_service),
) -> FeriadoRead:
    record = await service.get_feriado(feriado_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feriado nao encontrado")
    return record


@router.post("/feriados", response_model=FeriadoRead, status_code=status.HTTP_201_CREATED, summary="Criar feriado")
async def create_feriado(
    payload: FeriadoCreate,
    _: User = Depends(require_permission("localidades_feriados", "create")),
    service: LocationService = Depends(get_location_service),
) -> FeriadoRead:
    return await service.create_feriado(payload)


@router.put("/feriados/{feriado_id}", response_model=FeriadoRead, summary="Atualizar feriado")
async def update_feriado(
    feriado_id: int,
    payload: FeriadoUpdate,
    _: User = Depends(require_permission("localidades_feriados", "update")),
    service: LocationService = Depends(get_location_service),
) -> FeriadoRead:
    record = await service.update_feriado(feriado_id, payload)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feriado nao encontrado")
    return record


@router.delete("/feriados/{feriado_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir feriado")
async def delete_feriado(
    feriado_id: int,
    _: User = Depends(require_permission("localidades_feriados", "delete")),
    service: LocationService = Depends(get_location_service),
) -> Response:
    deleted = await service.delete_feriado(feriado_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feriado nao encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/consulta-cep/{cep}", response_model=AddressLookupResponse, summary="Consultar endereco por CEP")
async def lookup_by_cep(cep: str, service: LocationService = Depends(get_location_service)) -> AddressLookupResponse:
    return await service.lookup_by_cep(cep, ensure_localities=True)


@router.get("/consulta-endereco", response_model=AddressLookupResponse, summary="Consultar CEP por endereco")
async def lookup_by_address(
    uf: Annotated[str, Query(min_length=2, max_length=2)],
    cidade: Annotated[str, Query(min_length=2)],
    logradouro: Annotated[str, Query(min_length=3)],
    bairro: Annotated[str | None, Query()] = None,
    service: LocationService = Depends(get_location_service),
) -> AddressLookupResponse:
    return await service.lookup_by_address(
        uf=uf,
        cidade=cidade,
        logradouro=logradouro,
        bairro=bairro,
        ensure_localities=True,
    )