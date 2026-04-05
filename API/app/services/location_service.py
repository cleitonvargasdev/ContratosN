from dataclasses import dataclass
from datetime import date
from urllib.parse import quote

import httpx
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.models.location import Bairro, Cidade, Feriado, UF
from app.repositories.location_repository import LocationRepository
from app.schemas.location import AddressLookupResponse, BairroCreate, BairroRead, BairroUpdate, CidadeCreate, CidadeRead, CidadeUpdate, FeriadoCreate, FeriadoRead, FeriadoUpdate, UFCreate, UFRead, UFUpdate


@dataclass
class _LookupCandidate:
    source: str
    cep: str | None = None
    endereco: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    uf: str | None = None


class LocationService:
    def __init__(self, session) -> None:
        self.repository = LocationRepository(session)

    async def list_ufs(self, term: str | None = None) -> list[UFRead]:
        return [UFRead.model_validate(item) for item in await self.repository.list_ufs(term)]

    async def get_uf(self, uf_id: int) -> UFRead | None:
        record = await self.repository.get_uf_by_id(uf_id)
        return UFRead.model_validate(record) if record else None

    async def create_uf(self, payload: UFCreate) -> UFRead:
        if await self.repository.get_uf_by_sigla(payload.uf):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UF ja cadastrada")
        record = await self.repository.create_uf(payload.model_dump())
        return UFRead.model_validate(record)

    async def update_uf(self, uf_id: int, payload: UFUpdate) -> UFRead | None:
        record = await self.repository.get_uf_by_id(uf_id)
        if record is None:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        if update_data.get("uf") and update_data["uf"] != record.uf:
            existing = await self.repository.get_uf_by_sigla(str(update_data["uf"]))
            if existing is not None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UF ja cadastrada")

        try:
            updated = await self.repository.update_uf(record, update_data)
        except IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nao foi possivel atualizar UF") from exc
        return UFRead.model_validate(updated)

    async def delete_uf(self, uf_id: int) -> bool:
        record = await self.repository.get_uf_by_id(uf_id)
        if record is None:
            return False
        try:
            await self.repository.delete_uf(record)
        except IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UF vinculada a outros registros") from exc
        return True

    async def list_cidades(self, uf_sigla: str | None = None, nome: str | None = None) -> list[CidadeRead]:
        cidades = await self.repository.list_cidades(uf_sigla, nome)
        return [await self._serialize_cidade(item) for item in cidades]

    async def get_cidade(self, cidade_id: int) -> CidadeRead | None:
        record = await self.repository.get_cidade_by_id(cidade_id)
        if record is None:
            return None
        return await self._serialize_cidade(record)

    async def create_cidade_payload(self, payload: CidadeCreate) -> CidadeRead:
        uf_record = await self.repository.get_uf_by_id(payload.uf_id)
        if uf_record is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UF invalida")
        existing = await self.repository.get_cidade_by_name_and_uf(payload.cidade, payload.uf_id)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cidade ja cadastrada para esta UF")
        record = await self.repository.create_cidade(payload.uf_id, payload.cidade)
        return await self._serialize_cidade(record)

    async def update_cidade(self, cidade_id: int, payload: CidadeUpdate) -> CidadeRead | None:
        record = await self.repository.get_cidade_by_id(cidade_id)
        if record is None:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        uf_id = int(update_data.get("uf_id", record.uf_id))
        cidade_nome = str(update_data.get("cidade", record.cidade))

        uf_record = await self.repository.get_uf_by_id(uf_id)
        if uf_record is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UF invalida")

        existing = await self.repository.get_cidade_by_name_and_uf(cidade_nome, uf_id)
        if existing is not None and existing.cidade_id != record.cidade_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cidade ja cadastrada para esta UF")

        try:
            updated = await self.repository.update_cidade(record, update_data)
        except IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nao foi possivel atualizar cidade") from exc
        return await self._serialize_cidade(updated)

    async def delete_cidade(self, cidade_id: int) -> bool:
        record = await self.repository.get_cidade_by_id(cidade_id)
        if record is None:
            return False
        try:
            await self.repository.delete_cidade(record)
        except IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cidade vinculada a outros registros") from exc
        return True

    async def list_bairros(self, cidade_id: int | None = None, nome: str | None = None) -> list[BairroRead]:
        bairros = await self.repository.list_bairros(cidade_id, nome)
        return [await self._serialize_bairro(item) for item in bairros]

    async def get_bairro(self, bairro_id: int) -> BairroRead | None:
        record = await self.repository.get_bairro_by_id(bairro_id)
        if record is None:
            return None
        return await self._serialize_bairro(record)

    async def create_bairro_payload(self, payload: BairroCreate) -> BairroRead:
        cidade_record = await self.repository.get_cidade_by_id(payload.cidade_id)
        if cidade_record is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cidade invalida")
        existing = await self.repository.get_bairro_by_name_and_cidade(payload.bairro_nome, payload.cidade_id)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bairro ja cadastrado para esta cidade")
        record = await self.repository.create_bairro(payload.cidade_id, payload.bairro_nome)
        return await self._serialize_bairro(record)

    async def update_bairro(self, bairro_id: int, payload: BairroUpdate) -> BairroRead | None:
        record = await self.repository.get_bairro_by_id(bairro_id)
        if record is None:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        cidade_id = int(update_data.get("cidade_id", record.cidade_id))
        bairro_nome = str(update_data.get("bairro_nome", record.bairro_nome))

        cidade_record = await self.repository.get_cidade_by_id(cidade_id)
        if cidade_record is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cidade invalida")

        existing = await self.repository.get_bairro_by_name_and_cidade(bairro_nome, cidade_id)
        if existing is not None and existing.bairro_id != record.bairro_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bairro ja cadastrado para esta cidade")

        try:
            updated = await self.repository.update_bairro(record, update_data)
        except IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nao foi possivel atualizar bairro") from exc
        return await self._serialize_bairro(updated)

    async def delete_bairro(self, bairro_id: int) -> bool:
        record = await self.repository.get_bairro_by_id(bairro_id)
        if record is None:
            return False
        try:
            await self.repository.delete_bairro(record)
        except IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bairro vinculado a outros registros") from exc
        return True

    async def list_feriados(
        self,
        nivel: int | None = None,
        uf: str | None = None,
        cidade_id: int | None = None,
        descricao: str | None = None,
    ) -> list[FeriadoRead]:
        feriados = await self.repository.list_feriados(nivel, uf, cidade_id, descricao)
        return [await self._serialize_feriado(item) for item in feriados]

    async def get_feriado(self, feriado_id: int) -> FeriadoRead | None:
        record = await self.repository.get_feriado_by_id(feriado_id)
        if record is None:
            return None
        return await self._serialize_feriado(record)

    async def create_feriado(self, payload: FeriadoCreate) -> FeriadoRead:
        data = await self._normalize_feriado_payload(payload.model_dump())
        existing = await self.repository.get_feriado_conflict(**data)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Feriado ja cadastrado com a mesma abrangencia")
        record = await self.repository.create_feriado(data)
        return await self._serialize_feriado(record)

    async def update_feriado(self, feriado_id: int, payload: FeriadoUpdate) -> FeriadoRead | None:
        record = await self.repository.get_feriado_by_id(feriado_id)
        if record is None:
            return None

        base_data = {
            "data": record.data,
            "cidade_id": record.cidade_id,
            "uf": record.uf,
            "descricao": record.descricao,
            "nivel": record.nivel,
        }
        base_data.update(payload.model_dump(exclude_unset=True))
        normalized = await self._normalize_feriado_payload(base_data)
        existing = await self.repository.get_feriado_conflict(**normalized)
        if existing is not None and existing.feriado_id != record.feriado_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Feriado ja cadastrado com a mesma abrangencia")
        updated = await self.repository.update_feriado(record, normalized)
        return await self._serialize_feriado(updated)

    async def delete_feriado(self, feriado_id: int) -> bool:
        record = await self.repository.get_feriado_by_id(feriado_id)
        if record is None:
            return False
        await self.repository.delete_feriado(record)
        return True

    async def lookup_by_cep(self, cep: str, *, ensure_localities: bool = False) -> AddressLookupResponse:
        normalized_cep = self._normalize_digits(cep)
        if len(normalized_cep) != 8:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CEP invalido")

        candidate = await self._lookup_via_cep_services(normalized_cep)
        if candidate is None:
            return AddressLookupResponse(found=False)

        return await self._hydrate_lookup(candidate, ensure_localities=ensure_localities)

    async def lookup_by_address(
        self,
        *,
        uf: str,
        cidade: str,
        logradouro: str,
        bairro: str | None = None,
        ensure_localities: bool = False,
    ) -> AddressLookupResponse:
        uf_sigla = (uf or "").strip().upper()
        cidade_nome = (cidade or "").strip()
        logradouro_nome = (logradouro or "").strip()
        bairro_nome = (bairro or "").strip() or None

        if not uf_sigla or not cidade_nome or not logradouro_nome:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Informe UF, cidade e endereco")

        candidate = await self._lookup_by_address_services(
            uf=uf_sigla,
            cidade=cidade_nome,
            logradouro=logradouro_nome,
            bairro=bairro_nome,
        )
        if candidate is None:
            return AddressLookupResponse(found=False)

        return await self._hydrate_lookup(candidate, ensure_localities=ensure_localities)

    async def normalize_user_location_fields(self, values: dict[str, object]) -> dict[str, object]:
        uf = self._normalize_optional_text(values.get("uf"))
        cidade_id = self._normalize_int(values.get("cidade_id"))
        bairro_id = self._normalize_int(values.get("bairro_id"))
        cep = self._normalize_digits(values.get("cep")) or None

        values["uf"] = uf.upper() if uf else None
        values["cidade_id"] = cidade_id
        values["bairro_id"] = bairro_id
        values["cep"] = cep

        uf_record = None
        cidade_record = None

        if uf:
            uf_record = await self.repository.get_uf_by_sigla(uf)
            if uf_record is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UF invalida")

        if cidade_id is not None:
            cidade_record = await self.repository.get_cidade_by_id(cidade_id)
            if cidade_record is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cidade invalida")

            cidade_uf = await self.repository.get_uf_by_id(cidade_record.uf_id)
            if cidade_uf is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cidade sem UF associada")

            if uf_record and cidade_record.uf_id != uf_record.uf_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cidade nao pertence a UF selecionada")

            values["uf"] = cidade_uf.uf
            uf_record = cidade_uf

        if bairro_id is not None:
            bairro_record = await self.repository.get_bairro_by_id(bairro_id)
            if bairro_record is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bairro invalido")

            if cidade_record and bairro_record.cidade_id != cidade_record.cidade_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bairro nao pertence a cidade selecionada")

            if cidade_record is None:
                cidade_record = await self.repository.get_cidade_by_id(bairro_record.cidade_id)
                values["cidade_id"] = bairro_record.cidade_id

            if cidade_record is not None:
                cidade_uf = await self.repository.get_uf_by_id(cidade_record.uf_id)
                if cidade_uf is not None:
                    values["uf"] = cidade_uf.uf

        if values.get("cep"):
            lookup = await self.lookup_by_cep(str(values["cep"]), ensure_localities=True)
            if lookup.found:
                self._merge_lookup(values, lookup)
        elif values.get("uf") and values.get("cidade_id") and values.get("endereco"):
            cidade_record = cidade_record or await self.repository.get_cidade_by_id(int(values["cidade_id"]))
            bairro_nome = None
            if values.get("bairro_id"):
                bairro_record = await self.repository.get_bairro_by_id(int(values["bairro_id"]))
                bairro_nome = bairro_record.bairro_nome if bairro_record else None

            if cidade_record is not None:
                lookup = await self.lookup_by_address(
                    uf=str(values["uf"]),
                    cidade=cidade_record.cidade,
                    logradouro=str(values["endereco"]),
                    bairro=bairro_nome,
                    ensure_localities=True,
                )
                if lookup.found:
                    self._merge_lookup(values, lookup, preserve_existing=True)

        return values

    async def backfill_user_cep(self, user) -> object:
        if user.cep or not user.uf or not user.cidade_id or not user.endereco:
            return user

        cidade_record = await self.repository.get_cidade_by_id(int(user.cidade_id))
        if cidade_record is None:
            return user

        bairro_nome = None
        if user.bairro_id:
            bairro_record = await self.repository.get_bairro_by_id(int(user.bairro_id))
            bairro_nome = bairro_record.bairro_nome if bairro_record else None

        lookup = await self.lookup_by_address(
            uf=user.uf,
            cidade=cidade_record.cidade,
            logradouro=user.endereco,
            bairro=bairro_nome,
            ensure_localities=True,
        )
        if not lookup.found or not lookup.cep:
            return user

        from app.repositories.user_repository import UserRepository

        repository = UserRepository(self.repository.session)
        update_data = {"cep": lookup.cep}
        if lookup.cidade_id and user.cidade_id is None:
            update_data["cidade_id"] = lookup.cidade_id
        if lookup.bairro_id and user.bairro_id is None:
            update_data["bairro_id"] = lookup.bairro_id
        if lookup.uf and not user.uf:
            update_data["uf"] = lookup.uf
        return await repository.update_fields(user, update_data)

    async def _lookup_via_cep_services(self, cep: str) -> _LookupCandidate | None:
        async with httpx.AsyncClient(timeout=5.0) as client:
            for fetcher in (
                self._fetch_viacep_by_cep,
                self._fetch_brasilapi_by_cep,
                self._fetch_cepaberto_by_cep,
            ):
                candidate = await fetcher(client, cep)
                if candidate is not None:
                    return candidate
        return None

    async def _lookup_by_address_services(
        self,
        *,
        uf: str,
        cidade: str,
        logradouro: str,
        bairro: str | None,
    ) -> _LookupCandidate | None:
        async with httpx.AsyncClient(timeout=5.0) as client:
            for fetcher in (self._fetch_cepaberto_by_address, self._fetch_viacep_by_address):
                candidate = await fetcher(client, uf=uf, cidade=cidade, logradouro=logradouro, bairro=bairro)
                if candidate is not None:
                    return candidate
        return None

    async def _fetch_viacep_by_cep(self, client: httpx.AsyncClient, cep: str) -> _LookupCandidate | None:
        try:
            response = await client.get(f"https://viacep.com.br/ws/{cep}/json/")
            response.raise_for_status()
            data = response.json()
        except Exception:
            return None

        if data.get("erro"):
            return None

        return _LookupCandidate(
            source="viacep",
            cep=self._normalize_digits(data.get("cep")),
            endereco=self._normalize_optional_text(data.get("logradouro")),
            complemento=self._normalize_optional_text(data.get("complemento")),
            bairro=self._normalize_optional_text(data.get("bairro")),
            cidade=self._normalize_optional_text(data.get("localidade")),
            uf=self._normalize_optional_text(data.get("uf")),
        )

    async def _fetch_brasilapi_by_cep(self, client: httpx.AsyncClient, cep: str) -> _LookupCandidate | None:
        try:
            response = await client.get(f"https://brasilapi.com.br/api/cep/v2/{cep}")
            response.raise_for_status()
            data = response.json()
        except Exception:
            return None

        return _LookupCandidate(
            source="brasilapi",
            cep=self._normalize_digits(data.get("cep")),
            endereco=self._normalize_optional_text(data.get("street")),
            bairro=self._normalize_optional_text(data.get("neighborhood")),
            cidade=self._normalize_optional_text(data.get("city")),
            uf=self._normalize_optional_text(data.get("state")),
        )

    async def _fetch_cepaberto_by_cep(self, client: httpx.AsyncClient, cep: str) -> _LookupCandidate | None:
        try:
            if settings.cepaberto_token:
                response = await client.get(
                    "https://www.cepaberto.com/api/v3/cep",
                    params={"cep": cep},
                    headers={"Authorization": f"Token token={settings.cepaberto_token}"},
                )
            else:
                response = await client.get(f"https://www.cepaberto.com/ceps/{cep}.json")
            response.raise_for_status()
            data = response.json()
        except Exception:
            return None

        return self._normalize_cepaberto_payload(data, source="cepaberto")

    async def _normalize_feriado_payload(self, values: dict[str, object]) -> dict[str, object]:
        nivel = self._normalize_int(values.get("nivel"))
        uf = self._normalize_optional_text(values.get("uf"))
        uf = uf.upper() if uf else None
        cidade_id = self._normalize_int(values.get("cidade_id"))
        data = values.get("data")
        descricao = str(values.get("descricao") or "").strip()

        if not isinstance(data, date):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data do feriado invalida")
        if not descricao:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Descricao obrigatoria")

        if nivel == 1:
            values["uf"] = None
            values["cidade_id"] = None
        elif nivel == 2:
            if not uf:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selecione a UF para feriado estadual")
            if await self.repository.get_uf_by_sigla(uf) is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UF invalida")
            values["uf"] = uf
            values["cidade_id"] = None
        elif nivel == 3:
            if not uf:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selecione a UF para feriado municipal")
            uf_record = await self.repository.get_uf_by_sigla(uf)
            if uf_record is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="UF invalida")
            if cidade_id is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selecione a cidade para feriado municipal")
            cidade = await self.repository.get_cidade_by_id(cidade_id)
            if cidade is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cidade invalida")
            if cidade.uf_id != uf_record.uf_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cidade nao pertence a UF selecionada")
            values["cidade_id"] = cidade_id
            values["uf"] = uf
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nivel de feriado invalido")

        values["nivel"] = nivel
        values["data"] = data
        values["descricao"] = descricao
        return values

    async def _serialize_feriado(self, record: Feriado) -> FeriadoRead:
        cidade = await self.repository.get_cidade_by_id(record.cidade_id) if record.cidade_id else None
        return FeriadoRead(
            feriado_id=record.feriado_id,
            data=record.data,
            cidade_id=record.cidade_id,
            cidade=cidade.cidade if cidade else None,
            uf=record.uf,
            descricao=record.descricao,
            nivel=record.nivel,
        )

    async def _fetch_viacep_by_address(
        self,
        client: httpx.AsyncClient,
        *,
        uf: str,
        cidade: str,
        logradouro: str,
        bairro: str | None,
    ) -> _LookupCandidate | None:
        try:
            city_segment = quote(cidade)
            street_segment = quote(logradouro)
            response = await client.get(f"https://viacep.com.br/ws/{uf}/{city_segment}/{street_segment}/json/")
            response.raise_for_status()
            data = response.json()
        except Exception:
            return None

        if not isinstance(data, list):
            return None

        for item in data:
            candidate = _LookupCandidate(
                source="viacep",
                cep=self._normalize_digits(item.get("cep")),
                endereco=self._normalize_optional_text(item.get("logradouro")),
                complemento=self._normalize_optional_text(item.get("complemento")),
                bairro=self._normalize_optional_text(item.get("bairro")),
                cidade=self._normalize_optional_text(item.get("localidade")),
                uf=self._normalize_optional_text(item.get("uf")),
            )
            if bairro and candidate.bairro and self._normalize_optional_text(candidate.bairro) != self._normalize_optional_text(bairro):
                continue
            return candidate

        return None

    async def _fetch_cepaberto_by_address(
        self,
        client: httpx.AsyncClient,
        *,
        uf: str,
        cidade: str,
        logradouro: str,
        bairro: str | None,
    ) -> _LookupCandidate | None:
        params = {"estado": uf, "cidade": cidade, "logradouro": logradouro}
        if bairro:
            params["bairro"] = bairro

        urls: list[tuple[str, dict[str, str]]] = []
        if settings.cepaberto_token:
            urls.append(
                (
                    "https://www.cepaberto.com/api/v3/ceps",
                    {"Authorization": f"Token token={settings.cepaberto_token}"},
                )
            )
        urls.append(("https://www.cepaberto.com/ceps.json", {}))

        for url, headers in urls:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
            except Exception:
                continue

            if isinstance(data, list):
                if not data:
                    continue
                normalized = self._normalize_cepaberto_payload(data[0], source="cepaberto")
                if normalized is not None:
                    return normalized
            elif isinstance(data, dict):
                normalized = self._normalize_cepaberto_payload(data, source="cepaberto")
                if normalized is not None:
                    return normalized

        return None

    def _normalize_cepaberto_payload(self, payload: dict[str, object], *, source: str) -> _LookupCandidate | None:
        if not isinstance(payload, dict):
            return None

        cidade = payload.get("cidade")
        estado = payload.get("estado")
        return _LookupCandidate(
            source=source,
            cep=self._normalize_digits(payload.get("cep")),
            endereco=self._normalize_optional_text(payload.get("logradouro")),
            complemento=self._normalize_optional_text(payload.get("complemento")),
            bairro=self._normalize_optional_text(payload.get("bairro")),
            cidade=self._normalize_optional_text(cidade.get("nome") if isinstance(cidade, dict) else cidade),
            uf=self._normalize_optional_text(estado.get("sigla") if isinstance(estado, dict) else estado),
        )

    async def _hydrate_lookup(self, candidate: _LookupCandidate, *, ensure_localities: bool) -> AddressLookupResponse:
        uf_record = await self.repository.get_uf_by_sigla(candidate.uf) if candidate.uf else None
        cidade_id = None
        bairro_id = None

        if uf_record and candidate.cidade:
            cidade_record = await self.repository.get_cidade_by_name_and_uf(candidate.cidade, uf_record.uf_id)
            if cidade_record is None and ensure_localities:
                cidade_record = await self.repository.create_cidade(uf_record.uf_id, candidate.cidade)

            if cidade_record is not None:
                cidade_id = cidade_record.cidade_id
                if candidate.bairro:
                    bairro_record = await self.repository.get_bairro_by_name_and_cidade(candidate.bairro, cidade_record.cidade_id)
                    if bairro_record is None and ensure_localities:
                        bairro_record = await self.repository.create_bairro(cidade_record.cidade_id, candidate.bairro)
                    if bairro_record is not None:
                        bairro_id = bairro_record.bairro_id

        return AddressLookupResponse(
            found=True,
            source=candidate.source,
            cep=candidate.cep,
            endereco=candidate.endereco,
            complemento=candidate.complemento,
            bairro=candidate.bairro,
            bairro_id=bairro_id,
            cidade=candidate.cidade,
            cidade_id=cidade_id,
            uf=uf_record.uf if uf_record else candidate.uf,
        )

    async def _serialize_cidade(self, record: Cidade) -> CidadeRead:
        uf_record = await self.repository.get_uf_by_id(record.uf_id)
        return CidadeRead(
            cidade_id=record.cidade_id,
            uf_id=record.uf_id,
            cidade=record.cidade,
            uf=uf_record.uf if uf_record else None,
            uf_nome=uf_record.uf_nome if uf_record else None,
        )

    async def _serialize_bairro(self, record: Bairro) -> BairroRead:
        cidade_record = await self.repository.get_cidade_by_id(record.cidade_id)
        uf_sigla = None
        if cidade_record is not None:
            uf_record = await self.repository.get_uf_by_id(cidade_record.uf_id)
            uf_sigla = uf_record.uf if uf_record else None
        return BairroRead(
            bairro_id=record.bairro_id,
            cidade_id=record.cidade_id,
            bairro_nome=record.bairro_nome,
            cidade=cidade_record.cidade if cidade_record else None,
            uf=uf_sigla,
        )

    def _merge_lookup(self, values: dict[str, object], lookup: AddressLookupResponse, *, preserve_existing: bool = False) -> None:
        if lookup.cep and (not preserve_existing or not values.get("cep")):
            values["cep"] = lookup.cep
        if lookup.endereco and (not preserve_existing or not values.get("endereco")):
            values["endereco"] = lookup.endereco
        if lookup.complemento and (not preserve_existing or not values.get("complemento")):
            values["complemento"] = lookup.complemento
        if lookup.uf and (not preserve_existing or not values.get("uf")):
            values["uf"] = lookup.uf
        if lookup.cidade_id and (not preserve_existing or not values.get("cidade_id")):
            values["cidade_id"] = lookup.cidade_id
        if lookup.bairro_id and (not preserve_existing or not values.get("bairro_id")):
            values["bairro_id"] = lookup.bairro_id

    def _normalize_optional_text(self, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _normalize_digits(self, value: object) -> str:
        if value is None:
            return ""
        return "".join(char for char in str(value) if char.isdigit())

    def _normalize_int(self, value: object) -> int | None:
        if value is None or value == "":
            return None
        return int(value)