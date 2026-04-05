from datetime import date

import unicodedata
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Bairro, Cidade, Feriado, UF


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_value.lower().split())


class LocationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_ufs(self, term: str | None = None) -> Sequence[UF]:
        stmt = select(UF)
        if term:
            stmt = stmt.where((UF.uf.ilike(f"%{term}%")) | (UF.uf_nome.ilike(f"%{term}%")))

        result = await self.session.execute(stmt.order_by(UF.uf))
        return result.scalars().all()

    async def list_cidades(self, uf_sigla: str | None = None, nome: str | None = None) -> Sequence[Cidade]:
        stmt = select(Cidade)

        if uf_sigla:
            uf_record = await self.get_uf_by_sigla(uf_sigla)
            if uf_record is None:
                return []
            stmt = stmt.where(Cidade.uf_id == uf_record.uf_id)

        if nome:
            stmt = stmt.where(Cidade.cidade.ilike(f"%{nome}%"))

        result = await self.session.execute(stmt.order_by(Cidade.cidade))
        return result.scalars().all()

    async def list_bairros(self, cidade_id: int | None = None, nome: str | None = None) -> Sequence[Bairro]:
        stmt = select(Bairro)

        if cidade_id is not None:
            stmt = stmt.where(Bairro.cidade_id == cidade_id)

        if nome:
            stmt = stmt.where(Bairro.bairro_nome.ilike(f"%{nome}%"))

        result = await self.session.execute(stmt.order_by(Bairro.bairro_nome))
        return result.scalars().all()

    async def get_uf_by_id(self, uf_id: int) -> UF | None:
        return await self.session.get(UF, uf_id)

    async def get_uf_by_sigla(self, uf_sigla: str) -> UF | None:
        result = await self.session.execute(select(UF).where(UF.uf == uf_sigla.upper()))
        return result.scalar_one_or_none()

    async def create_uf(self, payload: dict[str, object]) -> UF:
        record = UF(**payload)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def update_uf(self, record: UF, payload: dict[str, object]) -> UF:
        for field, value in payload.items():
            setattr(record, field, value)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def delete_uf(self, record: UF) -> None:
        await self.session.delete(record)
        await self.session.commit()

    async def get_cidade_by_id(self, cidade_id: int) -> Cidade | None:
        return await self.session.get(Cidade, cidade_id)

    async def get_cidade_by_name_and_uf(self, cidade_nome: str, uf_id: int) -> Cidade | None:
        cidades = await self.list_cidades((await self.get_uf_by_id(uf_id)).uf)
        wanted = normalize_name(cidade_nome)
        return next((cidade for cidade in cidades if normalize_name(cidade.cidade) == wanted), None)

    async def create_cidade(self, uf_id: int, cidade_nome: str) -> Cidade:
        cidade = Cidade(uf_id=uf_id, cidade=cidade_nome)
        self.session.add(cidade)
        await self.session.commit()
        await self.session.refresh(cidade)
        return cidade

    async def update_cidade(self, record: Cidade, payload: dict[str, object]) -> Cidade:
        for field, value in payload.items():
            setattr(record, field, value)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def delete_cidade(self, record: Cidade) -> None:
        await self.session.delete(record)
        await self.session.commit()

    async def get_bairro_by_id(self, bairro_id: int) -> Bairro | None:
        return await self.session.get(Bairro, bairro_id)

    async def get_bairro_by_name_and_cidade(self, bairro_nome: str, cidade_id: int) -> Bairro | None:
        bairros = await self.list_bairros(cidade_id)
        wanted = normalize_name(bairro_nome)
        return next((bairro for bairro in bairros if normalize_name(bairro.bairro_nome) == wanted), None)

    async def create_bairro(self, cidade_id: int, bairro_nome: str) -> Bairro:
        bairro = Bairro(cidade_id=cidade_id, bairro_nome=bairro_nome)
        self.session.add(bairro)
        await self.session.commit()
        await self.session.refresh(bairro)
        return bairro

    async def update_bairro(self, record: Bairro, payload: dict[str, object]) -> Bairro:
        for field, value in payload.items():
            setattr(record, field, value)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def delete_bairro(self, record: Bairro) -> None:
        await self.session.delete(record)
        await self.session.commit()

    async def list_feriados(
        self,
        nivel: int | None = None,
        uf: str | None = None,
        cidade_id: int | None = None,
        descricao: str | None = None,
    ) -> Sequence[Feriado]:
        stmt = select(Feriado)

        if nivel:
            stmt = stmt.where(Feriado.nivel == nivel)
        if uf:
            stmt = stmt.where(Feriado.uf == uf.upper())
        if cidade_id is not None:
            stmt = stmt.where(Feriado.cidade_id == cidade_id)
        if descricao:
            stmt = stmt.where(Feriado.descricao.ilike(f"%{descricao}%"))

        result = await self.session.execute(stmt.order_by(Feriado.data, Feriado.descricao))
        return result.scalars().all()

    async def get_feriado_by_id(self, feriado_id: int) -> Feriado | None:
        return await self.session.get(Feriado, feriado_id)

    async def get_feriado_conflict(
        self,
        *,
        data: date,
        descricao: str,
        nivel: int,
        uf: str | None,
        cidade_id: int | None,
    ) -> Feriado | None:
        stmt = select(Feriado).where(
            Feriado.data == data,
            Feriado.descricao.ilike(descricao),
            Feriado.nivel == nivel,
            Feriado.uf == uf,
            Feriado.cidade_id == cidade_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_feriado(self, payload: dict[str, object]) -> Feriado:
        record = Feriado(**payload)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def update_feriado(self, record: Feriado, payload: dict[str, object]) -> Feriado:
        for field, value in payload.items():
            setattr(record, field, value)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def delete_feriado(self, record: Feriado) -> None:
        await self.session.delete(record)
        await self.session.commit()