from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contrato
from app.repositories.accounts_receivable_repository import AccountsReceivableRepository
from app.repositories.contract_repository import ContractRepository
from app.schemas.contract import ContractCreate, ContractListParams, ContractListResponse, ContractUpdate


LOCKED_CONTRACT_FIELDS = {
    "plano_id",
    "valor_empretismo",
    "qtde_dias",
    "percent_juros",
    "valor_final",
    "data_contrato",
    "data_final",
    "valor_parcela",
    "obs",
    "usuario_id_vendedor",
}


class ContractService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = ContractRepository(session)
        self.accounts_repository = AccountsReceivableRepository(session)

    async def list_contracts(self, params: ContractListParams) -> ContractListResponse:
        contracts, total = await self.repository.list_all(params)
        await self._sync_contract_financials_for_many(list(contracts))
        return ContractListResponse(items=list(contracts), total=total, page=params.page, page_size=params.page_size)

    async def get_contract(self, contract_id: int) -> Contrato | None:
        contract = await self.repository.get_by_id(contract_id)
        if contract is not None:
            await self._sync_contract_financials(contract)
        return contract

    async def create_contract(self, payload: ContractCreate, current_user_id: int | None = None) -> Contrato:
        payload_data = payload.model_dump()
        if current_user_id is not None and payload_data.get("user_add") is None:
            payload_data["user_add"] = current_user_id
        contract = Contrato(**payload_data)
        return await self.repository.create(contract)

    async def update_contract(self, contract_id: int, payload: ContractUpdate) -> Contrato | None:
        contract = await self.repository.get_by_id(contract_id)
        if contract is None:
            return None

        await self._sync_contract_financials(contract)

        update_data = payload.model_dump(exclude_unset=True)
        update_data.pop("user_add", None)

        if update_data:
            installments = await self.accounts_repository.list_by_contract(contract.contratos_id)
            has_locked_installments = any((float(item.valor_recebido or 0) > 0) or bool(item.quitado) for item in installments)
            if has_locked_installments:
                blocked_fields = sorted(field for field in LOCKED_CONTRACT_FIELDS if field in update_data)
                if blocked_fields:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Contrato com recebimentos ou parcelas quitadas nao permite alterar plano, valores, dias, juros, datas, valor da parcela, observacao ou vendedor.",
                    )

        return await self.repository.update_fields(contract, update_data)

    async def delete_contract(self, contract_id: int) -> bool:
        contract = await self.repository.get_by_id(contract_id)
        if contract is None:
            return False
        try:
            await self.repository.delete(contract)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contrato vinculado a outros registros") from exc
        return True

    async def _sync_contract_financials_for_many(self, contracts: list[Contrato]) -> None:
        changed = False
        for contract in contracts:
            changed = await self._sync_contract_financials(contract, commit=False) or changed

        if changed:
            await self.accounts_repository.commit()

    async def _sync_contract_financials(self, contract: Contrato, commit: bool = True) -> bool:
        installments = await self.accounts_repository.list_by_contract(contract.contratos_id)
        totals = self.accounts_repository.build_contract_totals(installments)

        has_changes = False
        for field in ("valor_final", "valor_recebido", "valor_em_aberto", "valor_em_atraso", "quitado"):
            new_value = totals[field]
            if getattr(contract, field) != new_value:
                setattr(contract, field, new_value)
                has_changes = True

        if has_changes and commit:
            await self.accounts_repository.commit()

        return has_changes