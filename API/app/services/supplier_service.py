from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.supplier import Fornecedor
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.supplier import SupplierCreate, SupplierListResponse, SupplierRead, SupplierUpdate


class SupplierService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = SupplierRepository(session)

    async def list_suppliers(
        self,
        *,
        nome: str | None,
        cpf_cnpj: str | None,
        ativo: bool | None,
        page: int,
        page_size: int,
    ) -> SupplierListResponse:
        items, total = await self.repository.list_suppliers(
            nome=nome,
            cpf_cnpj=cpf_cnpj,
            ativo=ativo,
            page=page,
            page_size=page_size,
        )
        return SupplierListResponse(
            items=[SupplierRead.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_supplier(self, supplier_id: int) -> SupplierRead | None:
        record = await self.repository.get_by_id(supplier_id)
        return None if record is None else SupplierRead.model_validate(record)

    async def create_supplier(self, payload: SupplierCreate) -> SupplierRead:
        record = Fornecedor(**payload.model_dump())
        return SupplierRead.model_validate(await self.repository.create(record))

    async def update_supplier(self, supplier_id: int, payload: SupplierUpdate) -> SupplierRead | None:
        record = await self.repository.get_by_id(supplier_id)
        if record is None:
            return None
        for field, value in payload.model_dump().items():
            setattr(record, field, value)
        return SupplierRead.model_validate(await self.repository.update(record))

    async def delete_supplier(self, supplier_id: int) -> bool:
        record = await self.repository.get_by_id(supplier_id)
        if record is None:
            return False
        try:
            await self.repository.delete(record)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fornecedor vinculado a outros registros e nao pode ser excluido.",
            ) from exc
        return True