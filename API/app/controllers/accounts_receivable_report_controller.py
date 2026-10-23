from datetime import date

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission
from app.db.session import get_db_session
from app.models.user import User
from app.services.accounts_receivable_report_service import AccountsReceivableReportService


router = APIRouter()


@router.get("/relatorios/contas-a-receber/imprimir", summary="Imprimir relatório de contas a receber")
async def print_accounts_receivable(
    data_inicial: date,
    data_final: date,
    funcionario_id: int | None = None,
    cliente_id: int | None = None,
    comodato: bool | None = None,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_permission("contratos", "read")),
):
    pdf, filename = await AccountsReceivableReportService(session).generate(
        data_inicial, data_final, funcionario_id, cliente_id, comodato
    )
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{filename}"'})
