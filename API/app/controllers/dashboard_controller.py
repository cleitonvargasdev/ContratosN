from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session, get_current_active_user, require_permission
from app.schemas.dashboard import DashboardSummaryRead
from app.services.dashboard_service import DashboardService

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/resumo", response_model=DashboardSummaryRead, summary="Resumo do dashboard")
async def get_dashboard_summary(
    agrupamento: Literal["dia", "ano"] = "dia",
    referencia: date = Query(default_factory=date.today),
    dias_finalizacao: Annotated[int, Query(ge=1, le=10)] = 7,
    _: object = Depends(require_permission("dashboard", "read")),
    session: AsyncSession = Depends(get_db_session),
) -> DashboardSummaryRead:
    return await DashboardService(session).get_summary(
        agrupamento=agrupamento,
        referencia=referencia,
        dias_finalizacao=dias_finalizacao,
    )
