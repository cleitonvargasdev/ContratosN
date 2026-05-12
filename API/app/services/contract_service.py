from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contrato
from app.repositories.accounts_receivable_repository import AccountsReceivableRepository
from app.repositories.contract_repository import ContractRepository
from app.schemas.contract import ContractCreate, ContractListParams, ContractListResponse, ContractUpdate
from app.schemas.contract_commodato import ContractComodatoRead, ContractComodatoWrite


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
    "aluguel",
    "recorrencia",
    "cobranca_segunda",
    "cobranca_terca",
    "cobranca_quarta",
    "cobranca_quinta",
    "cobranca_sexta",
    "cobranca_sabado",
    "cobranca_domingo",
    "cobranca_feriado",
    "cobranca_mensal",
    "cobranca_quinzenal",
}

SCHEDULE_RULE_FIELDS = (
    "aluguel",
    "recorrencia",
    "cobranca_segunda",
    "cobranca_terca",
    "cobranca_quarta",
    "cobranca_quinta",
    "cobranca_sexta",
    "cobranca_sabado",
    "cobranca_domingo",
    "cobranca_feriado",
    "cobranca_mensal",
    "cobranca_quinzenal",
)

CONTRACT_BOOLEAN_DEFAULTS = {
    "aluguel": False,
    "recorrencia": False,
    "cobranca_segunda": True,
    "cobranca_terca": True,
    "cobranca_quarta": True,
    "cobranca_quinta": True,
    "cobranca_sexta": True,
    "cobranca_sabado": False,
    "cobranca_domingo": False,
    "cobranca_feriado": False,
    "cobranca_mensal": False,
    "cobranca_quinzenal": False,
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
        self._validate_contract_rules(payload_data)
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
            self._validate_contract_rules(self._resolve_rule_state(update_data, contract))

        if update_data:
            installments = await self.accounts_repository.list_by_contract(contract.contratos_id)
            has_locked_installments = any((float(item.valor_recebido or 0) > 0) or bool(item.quitado) for item in installments)
            if has_locked_installments:
                blocked_fields = sorted(
                    field
                    for field in LOCKED_CONTRACT_FIELDS
                    if field in update_data and update_data[field] != getattr(contract, field)
                )
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

    async def get_contract_commodato(self, contract_id: int) -> ContractComodatoRead:
        contract = await self.repository.get_by_id(contract_id)
        if contract is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato nao encontrado")

        record = await self.repository.get_commodato_by_contract_id(contract_id)
        return self._build_commodato_read(contract_id, record)

    async def save_contract_commodato(self, contract_id: int, payload: ContractComodatoWrite) -> ContractComodatoRead:
        contract = await self.repository.get_by_id(contract_id)
        if contract is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato nao encontrado")

        avalista_id = payload.avalista_id
        if avalista_id is not None:
            avalista = await self.repository.get_client_by_id(avalista_id)
            if avalista is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Avalista nao encontrado")

        product_ids = [int(item.produto_id) for item in payload.items if item.produto_id is not None]
        unique_product_ids = list(dict.fromkeys(product_ids))
        products = {item.produto_id: item for item in await self.repository.list_products_by_ids(unique_product_ids)}
        if len(products) != len(unique_product_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Um ou mais produtos informados nao foram encontrados")

        normalized_items: list[dict[str, object]] = []
        for item in payload.items:
            if item.produto_id is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Produto do comodato obrigatorio")
            product = products.get(item.produto_id)
            if product is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Um ou mais produtos informados nao foram encontrados")
            normalized_items.append(
                {
                    "produto_id": item.produto_id,
                    "descricao_produto": product.descricao,
                    "quantidade": item.quantidade,
                    "valor_unitario": item.valor_unitario if item.valor_unitario is not None else product.valor_venda,
                    "observacao": item.observacao,
                }
            )

        saved = await self.repository.save_commodato(contract_id, avalista_id, normalized_items)
        return self._build_commodato_read(contract_id, saved)

    async def delete_contract_commodato(self, contract_id: int) -> bool:
        contract = await self.repository.get_by_id(contract_id)
        if contract is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato nao encontrado")

        return await self.repository.delete_commodato_by_contract_id(contract_id)

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
        for field, default_value in CONTRACT_BOOLEAN_DEFAULTS.items():
            if getattr(contract, field) is None:
                setattr(contract, field, default_value)
                has_changes = True

        for field in ("valor_final", "valor_recebido", "valor_em_aberto", "valor_em_atraso", "quitado"):
            new_value = totals[field]
            if getattr(contract, field) != new_value:
                setattr(contract, field, new_value)
                has_changes = True

        if has_changes and commit:
            await self.accounts_repository.commit()

        return has_changes

    @staticmethod
    def _validate_contract_rules(values: dict[str, object]) -> None:
        if bool(values.get("aluguel")) and bool(values.get("recorrencia")):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contrato nao pode ser aluguel e recorrente ao mesmo tempo")

        if bool(values.get("cobranca_mensal")) and bool(values.get("cobranca_quinzenal")):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selecione apenas uma frequencia: mensal ou quinzenal")

    @staticmethod
    def _resolve_rule_state(update_data: dict[str, object], contract: Contrato) -> dict[str, object]:
        return {
            field: update_data.get(field, getattr(contract, field))
            for field in SCHEDULE_RULE_FIELDS
        }

    def _build_commodato_read(self, contract_id: int, record: object | None) -> ContractComodatoRead:
        if record is None:
            return ContractComodatoRead(contrato_id=contract_id)

        avalista_nome = None
        avalista_id = getattr(record, "avalista_cliente_id", None)
        if avalista_id is not None:
            avalista = getattr(record, "avalista", None)
            avalista_nome = getattr(avalista, "nome", None) if avalista is not None else None

        items = [
            {
                "item_id": item.item_id,
                "produto_id": item.produto_id,
                "produto_descricao": item.descricao_produto,
                "quantidade": item.quantidade,
                "valor_unitario": item.valor_unitario,
                "observacao": item.observacao,
            }
            for item in getattr(record, "items", [])
        ]
        total_quantidade = sum(int(item["quantidade"]) for item in items)
        return ContractComodatoRead(
            contrato_id=contract_id,
            avalista_id=avalista_id,
            avalista_nome=avalista_nome,
            items=items,
            total_itens=len(items),
            total_quantidade=total_quantidade,
            pode_imprimir=len(items) > 0,
        )