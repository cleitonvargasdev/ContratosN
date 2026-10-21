from datetime import date
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import require_permission
from app.db.session import get_db_session
from app.models.user import User
from app.services.occurrence_report_service import OccurrenceReportService

router = APIRouter()
@router.get('/relatorios/ocorrencias/imprimir')
async def print_occurrences(data_inicial: date, data_final: date, cobrador_id: int | None = None, session: AsyncSession = Depends(get_db_session), _: User = Depends(require_permission('contratos','read'))):
    pdf, filename = await OccurrenceReportService(session).generate(data_inicial, data_final, cobrador_id)
    return Response(content=pdf, media_type='application/pdf', headers={'Content-Disposition': f'inline; filename="{filename}"'})
