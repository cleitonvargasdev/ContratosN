from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, require_permission
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.payment_plan import PaymentPlanCreate, PaymentPlanRead, PaymentPlanUpdate
from app.services.payment_plan_service import PaymentPlanService


router = APIRouter(dependencies=[Depends(get_current_active_user)])


def get_payment_plan_service(session: AsyncSession = Depends(get_db_session)) -> PaymentPlanService:
    return PaymentPlanService(session)


@router.get("/planos-pagamentos", response_model=list[PaymentPlanRead], summary="Listar planos de pagamento")
async def list_payment_plans(
    descricao: Annotated[str | None, Query(description="Filtro por descricao do plano.")] = None,
    _: User = Depends(require_permission("planos_pagamentos", "read")),
    service: PaymentPlanService = Depends(get_payment_plan_service),
) -> list[PaymentPlanRead]:
    return await service.list_payment_plans(descricao)


@router.get("/planos-pagamentos/{plano_id}", response_model=PaymentPlanRead, summary="Buscar plano de pagamento")
async def get_payment_plan(
    plano_id: int,
    _: User = Depends(require_permission("planos_pagamentos", "read")),
    service: PaymentPlanService = Depends(get_payment_plan_service),
) -> PaymentPlanRead:
    record = await service.get_payment_plan(plano_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano de pagamento nao encontrado")
    return record


@router.post("/planos-pagamentos", response_model=PaymentPlanRead, status_code=status.HTTP_201_CREATED, summary="Criar plano de pagamento")
async def create_payment_plan(
    payload: PaymentPlanCreate,
    _: User = Depends(require_permission("planos_pagamentos", "create")),
    service: PaymentPlanService = Depends(get_payment_plan_service),
) -> PaymentPlanRead:
    return await service.create_payment_plan(payload)


@router.put("/planos-pagamentos/{plano_id}", response_model=PaymentPlanRead, summary="Atualizar plano de pagamento")
async def update_payment_plan(
    plano_id: int,
    payload: PaymentPlanUpdate,
    _: User = Depends(require_permission("planos_pagamentos", "update")),
    service: PaymentPlanService = Depends(get_payment_plan_service),
) -> PaymentPlanRead:
    record = await service.update_payment_plan(plano_id, payload)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano de pagamento nao encontrado")
    return record


@router.delete("/planos-pagamentos/{plano_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir plano de pagamento")
async def delete_payment_plan(
    plano_id: int,
    _: User = Depends(require_permission("planos_pagamentos", "delete")),
    service: PaymentPlanService = Depends(get_payment_plan_service),
) -> Response:
    deleted = await service.delete_payment_plan(plano_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano de pagamento nao encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)