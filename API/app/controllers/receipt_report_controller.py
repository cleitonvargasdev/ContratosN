from datetime import date
from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import require_permission
from app.db.session import get_db_session
from app.models.user import User
from app.services.receipt_report_service import ReceiptReportService

router = APIRouter()

@router.get('/relatorios/recebimentos/cobradores')
async def list_collectors(session: AsyncSession = Depends(get_db_session), _: User = Depends(require_permission('contratos', 'read'))):
    rows = (await session.execute(select(User.id, User.nome, User.ativo).order_by(User.nome, User.id))).all()
    return [{'id': user_id, 'nome': name, 'ativo': active} for user_id, name, active in rows]

@router.get('/relatorios/recebimentos/imprimir')
async def print_receipts(data_inicial: date, data_final: date, tipo: str = 'analitico', cobrador_id: int | None = None, todos_carteira: bool = False, session: AsyncSession = Depends(get_db_session), _: User = Depends(require_permission('contratos', 'read'))):
    pdf, filename = await ReceiptReportService(session).generate(data_inicial, data_final, cobrador_id, todos_carteira, tipo)
    return Response(content=pdf, media_type='application/pdf', headers={'Content-Disposition': f'inline; filename="{filename}"'})
