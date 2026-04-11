from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db_session, get_pagination_params, require_permission
from app.models.user import User
from app.schemas.accounts_receivable import (
    ContractInstallmentGenerateRequest,
    ContractInstallmentRead,
    ContractReceiptRead,
    InstallmentWhatsAppSendResponse,
    InstallmentCreateRequest,
    InstallmentPaymentCreate,
    InstallmentSettleRequest,
    InstallmentUpdateRequest,
)
from app.schemas.contract import ContractCreate, ContractListParams, ContractListResponse, ContractRead, ContractUpdate
from app.schemas.pagination import PaginationParams
from app.services.accounts_receivable_service import AccountsReceivableService
from app.services.contract_service import ContractService


router = APIRouter(dependencies=[Depends(get_current_active_user)])


def get_contract_service(session: AsyncSession = Depends(get_db_session)) -> ContractService:
    return ContractService(session)


def get_accounts_receivable_service(session: AsyncSession = Depends(get_db_session)) -> AccountsReceivableService:
    return AccountsReceivableService(session)


@router.get("/", response_model=ContractListResponse, summary="Listar contratos")
async def list_contracts(
    pagination: PaginationParams = Depends(get_pagination_params),
    contratos_id: Annotated[int | None, Query(description="Filtra pelo ID do contrato.")] = None,
    cliente_nome: Annotated[str | None, Query(description="Filtra pelo nome do cliente ou empresa.")] = None,
    cobrador_nome: Annotated[str | None, Query(description="Filtra pelo nome do cobrador.")] = None,
    quitado: Annotated[bool | None, Query(description="Filtra contratos quitados ou em aberto.")] = None,
    _: User = Depends(require_permission("contratos", "read")),
    service: ContractService = Depends(get_contract_service),
) -> ContractListResponse:
    params = ContractListParams(
        page=pagination.page,
        page_size=pagination.page_size,
        contratos_id=contratos_id,
        cliente_nome=cliente_nome,
        cobrador_nome=cobrador_nome,
        quitado=quitado,
    )
    return await service.list_contracts(params)


@router.get("/{contract_id}", response_model=ContractRead, summary="Buscar contrato por ID")
async def get_contract(
    contract_id: int,
    _: User = Depends(require_permission("contratos", "read")),
    service: ContractService = Depends(get_contract_service),
) -> ContractRead:
    contract = await service.get_contract(contract_id)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato nao encontrado")
    return contract


@router.get("/{contract_id}/parcelas", response_model=list[ContractInstallmentRead], summary="Listar parcelas do contrato")
async def list_contract_installments(
    contract_id: int,
    _: User = Depends(require_permission("contratos", "read")),
    service: AccountsReceivableService = Depends(get_accounts_receivable_service),
) -> list[ContractInstallmentRead]:
    return await service.list_contract_installments(contract_id)


@router.post("/{contract_id}/parcelas/gerar", response_model=list[ContractInstallmentRead], summary="Gerar parcelas do contrato")
async def generate_contract_installments(
    contract_id: int,
    payload: ContractInstallmentGenerateRequest,
    current_user: User = Depends(require_permission("contratos", "update")),
    service: AccountsReceivableService = Depends(get_accounts_receivable_service),
) -> list[ContractInstallmentRead]:
    return await service.generate_contract_installments(contract_id, payload, current_user.id)


@router.post("/{contract_id}/parcelas", response_model=ContractInstallmentRead, summary="Incluir parcela do contrato")
async def create_contract_installment(
    contract_id: int,
    payload: InstallmentCreateRequest,
    current_user: User = Depends(require_permission("contratos", "update")),
    service: AccountsReceivableService = Depends(get_accounts_receivable_service),
) -> ContractInstallmentRead:
    return await service.create_installment(contract_id, payload, current_user.id)


@router.post("/parcelas/{installment_id}/receber", response_model=ContractInstallmentRead, summary="Receber parcela")
async def receive_installment(
    installment_id: int,
    payload: InstallmentPaymentCreate,
    current_user: User = Depends(require_permission("contratos", "update")),
    service: AccountsReceivableService = Depends(get_accounts_receivable_service),
) -> ContractInstallmentRead:
    return await service.receive_installment(installment_id, payload, current_user.id)


@router.put("/parcelas/{installment_id}", response_model=ContractInstallmentRead, summary="Alterar parcela")
async def update_installment(
    installment_id: int,
    payload: InstallmentUpdateRequest,
    _: User = Depends(require_permission("contratos", "update")),
    service: AccountsReceivableService = Depends(get_accounts_receivable_service),
) -> ContractInstallmentRead:
    return await service.update_installment(installment_id, payload)


@router.get("/parcelas/{installment_id}/pagamentos", response_model=list[ContractReceiptRead], summary="Listar pagamentos da parcela")
async def list_installment_receipts(
    installment_id: int,
    _: User = Depends(require_permission("contratos", "read")),
    service: AccountsReceivableService = Depends(get_accounts_receivable_service),
) -> list[ContractReceiptRead]:
    return await service.list_installment_receipts(installment_id)


@router.post("/parcelas/{installment_id}/quitar", response_model=ContractInstallmentRead, summary="Quitar parcela")
async def settle_installment(
    installment_id: int,
    payload: InstallmentSettleRequest,
    _: User = Depends(require_permission("contratos", "update")),
    service: AccountsReceivableService = Depends(get_accounts_receivable_service),
) -> ContractInstallmentRead:
    return await service.settle_installment(installment_id, payload)


@router.post("/parcelas/{installment_id}/reabrir", response_model=ContractInstallmentRead, summary="Reabrir parcela")
async def reopen_installment(
    installment_id: int,
    _: User = Depends(require_permission("contratos", "update")),
    service: AccountsReceivableService = Depends(get_accounts_receivable_service),
) -> ContractInstallmentRead:
    return await service.reopen_installment(installment_id)


@router.delete("/parcelas/{installment_id}/pagamento", response_model=ContractInstallmentRead, summary="Excluir pagamento da parcela")
async def delete_installment_payment(
    installment_id: int,
    _: User = Depends(require_permission("contratos", "update")),
    service: AccountsReceivableService = Depends(get_accounts_receivable_service),
) -> ContractInstallmentRead:
    return await service.delete_installment_payment(installment_id)


@router.delete("/pagamentos/{receipt_id}", response_model=ContractInstallmentRead, summary="Excluir pagamento especifico da parcela")
async def delete_receipt_payment(
    receipt_id: int,
    _: User = Depends(require_permission("contratos", "update")),
    service: AccountsReceivableService = Depends(get_accounts_receivable_service),
) -> ContractInstallmentRead:
    return await service.delete_receipt_payment(receipt_id)


@router.post("/parcelas/{installment_id}/whatsapp", response_model=InstallmentWhatsAppSendResponse, summary="Enviar mensagem da parcela via WhatsApp")
async def send_installment_whatsapp_message(
    installment_id: int,
    _: User = Depends(require_permission("contratos", "update")),
    service: AccountsReceivableService = Depends(get_accounts_receivable_service),
) -> InstallmentWhatsAppSendResponse:
    return InstallmentWhatsAppSendResponse.model_validate(await service.send_installment_whatsapp_message(installment_id))


@router.post("/", response_model=ContractRead, status_code=status.HTTP_201_CREATED, summary="Criar contrato")
async def create_contract(
    payload: ContractCreate,
    current_user: User = Depends(require_permission("contratos", "create")),
    service: ContractService = Depends(get_contract_service),
) -> ContractRead:
    return await service.create_contract(payload, current_user_id=current_user.id)


@router.put("/{contract_id}", response_model=ContractRead, summary="Atualizar contrato")
async def update_contract(
    contract_id: int,
    payload: ContractUpdate,
    _: User = Depends(require_permission("contratos", "update")),
    service: ContractService = Depends(get_contract_service),
) -> ContractRead:
    contract = await service.update_contract(contract_id, payload)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato nao encontrado")
    return contract


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir contrato")
async def delete_contract(
    contract_id: int,
    _: User = Depends(require_permission("contratos", "delete")),
    service: ContractService = Depends(get_contract_service),
) -> Response:
    deleted = await service.delete_contract(contract_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato nao encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)