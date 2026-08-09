from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, require_permission
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.accounts_payable import (
    AccountsPayableAddInstallmentsRequest,
    AccountsPayableCreate,
    AccountsPayableInstallmentRead,
    AccountsPayableListParams,
    AccountsPayableListResponse,
    AccountsPayablePaymentCreate,
    AccountsPayablePersonSearchItem,
    AccountsPayableRead,
    AccountsPayableUpdate,
)
from app.services.accounts_payable_service import AccountsPayableService


router = APIRouter(dependencies=[Depends(get_current_active_user)])


def get_accounts_payable_service(session: AsyncSession = Depends(get_db_session)) -> AccountsPayableService:
    return AccountsPayableService(session)


@router.get("/contas-pagar", response_model=AccountsPayableListResponse, summary="Listar contas a pagar")
async def list_accounts_payable(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    quitado: Annotated[bool | None, Query(description="Filtro por quitacao.")] = None,
    pessoa_query: Annotated[str | None, Query(description="Filtro por nome ou CPF/CNPJ.")] = None,
    tipo_pessoa: Annotated[str | None, Query(description="Filtro por tipo de pessoa.")] = None,
    data_vencimento_inicial: Annotated[str | None, Query()] = None,
    data_vencimento_final: Annotated[str | None, Query()] = None,
    data_referencia_inicial: Annotated[str | None, Query()] = None,
    data_referencia_final: Annotated[str | None, Query()] = None,
    _: User = Depends(require_permission("contas_pagar", "read")),
    service: AccountsPayableService = Depends(get_accounts_payable_service),
) -> AccountsPayableListResponse:
    params = AccountsPayableListParams(
        page=page,
        page_size=page_size,
        quitado=quitado,
        pessoa_query=pessoa_query,
        tipo_pessoa=tipo_pessoa,
        data_vencimento_inicial=data_vencimento_inicial,
        data_vencimento_final=data_vencimento_final,
        data_referencia_inicial=data_referencia_inicial,
        data_referencia_final=data_referencia_final,
    )
    return await service.list_accounts_payable(params)


@router.get("/contas-pagar/pessoas", response_model=list[AccountsPayablePersonSearchItem], summary="Pesquisar pessoas para contas a pagar")
async def search_accounts_payable_people(
    query: Annotated[str, Query(min_length=3, description="Nome ou CPF/CNPJ.")],
    _: User = Depends(require_permission("contas_pagar", "read")),
    service: AccountsPayableService = Depends(get_accounts_payable_service),
) -> list[AccountsPayablePersonSearchItem]:
    return await service.search_people(query)


@router.get("/contas-pagar/{conta_pagar_id}", response_model=AccountsPayableRead, summary="Buscar conta a pagar")
async def get_account_payable(
    conta_pagar_id: int,
    _: User = Depends(require_permission("contas_pagar", "read")),
    service: AccountsPayableService = Depends(get_accounts_payable_service),
) -> AccountsPayableRead:
    record = await service.get_account(conta_pagar_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta a pagar nao encontrada")
    return record


@router.post("/contas-pagar", response_model=AccountsPayableRead, status_code=status.HTTP_201_CREATED, summary="Criar conta a pagar")
async def create_account_payable(
    payload: AccountsPayableCreate,
    current_user: User = Depends(require_permission("contas_pagar", "create")),
    service: AccountsPayableService = Depends(get_accounts_payable_service),
) -> AccountsPayableRead:
    return await service.create_account(payload, current_user.id)


@router.put("/contas-pagar/{conta_pagar_id}", response_model=AccountsPayableRead, summary="Atualizar conta a pagar")
async def update_account_payable(
    conta_pagar_id: int,
    payload: AccountsPayableUpdate,
    _: User = Depends(require_permission("contas_pagar", "update")),
    service: AccountsPayableService = Depends(get_accounts_payable_service),
) -> AccountsPayableRead:
    record = await service.update_account(conta_pagar_id, payload)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta a pagar nao encontrada")
    return record


@router.post("/contas-pagar/{conta_pagar_id}/parcelas", response_model=AccountsPayableRead, summary="Adicionar parcelas a conta a pagar")
async def add_accounts_payable_installments(
    conta_pagar_id: int,
    payload: AccountsPayableAddInstallmentsRequest,
    _: User = Depends(require_permission("contas_pagar", "update")),
    service: AccountsPayableService = Depends(get_accounts_payable_service),
) -> AccountsPayableRead:
    return await service.add_installments(conta_pagar_id, payload)


@router.post("/contas-pagar/parcelas/{parcela_id}/pagamentos", response_model=AccountsPayableInstallmentRead, summary="Registrar pagamento de parcela")
async def register_accounts_payable_payment(
    parcela_id: int,
    payload: AccountsPayablePaymentCreate,
    current_user: User = Depends(require_permission("contas_pagar", "update")),
    service: AccountsPayableService = Depends(get_accounts_payable_service),
) -> AccountsPayableInstallmentRead:
    return await service.register_payment(parcela_id, payload, current_user.id)


@router.delete("/contas-pagar/parcelas/{parcela_id}/pagamentos", response_model=AccountsPayableInstallmentRead, summary="Remover pagamentos da parcela")
async def remove_accounts_payable_installment_payments(
    parcela_id: int,
    _: User = Depends(require_permission("contas_pagar", "update")),
    service: AccountsPayableService = Depends(get_accounts_payable_service),
) -> AccountsPayableInstallmentRead:
    return await service.remove_installment_payments(parcela_id)


@router.delete("/contas-pagar/parcelas/{parcela_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir parcela")
async def delete_accounts_payable_installment(
    parcela_id: int,
    _: User = Depends(require_permission("contas_pagar", "delete")),
    service: AccountsPayableService = Depends(get_accounts_payable_service),
) -> Response:
    if not await service.delete_installment(parcela_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela nao encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/contas-pagar/{conta_pagar_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir conta a pagar")
async def delete_account_payable(
    conta_pagar_id: int,
    _: User = Depends(require_permission("contas_pagar", "delete")),
    service: AccountsPayableService = Depends(get_accounts_payable_service),
) -> Response:
    deleted = await service.delete_account(conta_pagar_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta a pagar nao encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
