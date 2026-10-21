from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import require_permission
from app.db.session import get_db_session
from app.models.user import User
from app.models.mobile_batch import MobileBatch
from app.services.mobile_wallet_service import WalletArtifacts, wallet_query
from app.tenancy.context import current_tenant, tenant_key

router = APIRouter()
wallet_user = require_permission('acesso_web', 'read')


@router.post('/carteira', status_code=201)
async def create_wallet(user: User = Depends(wallet_user), db: AsyncSession = Depends(get_db_session)):
    blocked_batch = await db.scalar(
        select(MobileBatch.id).where(
            MobileBatch.user_id == user.id, MobileBatch.blocked.is_(True)
        ).limit(1)
    )
    if blocked_batch is not None:
        raise HTTPException(409, 'Existe lote bloqueado. Solicite o desbloqueio antes de baixar nova carteira.')
    rows = (await db.execute(wallet_query(user.id))).mappings().all()
    tenant = current_tenant.get()
    return await run_in_threadpool(WalletArtifacts().build, tenant_key(),
                                   tenant.company_code if tenant else 'legacy', user, rows)


@router.get('/carteira/{download_id}/arquivo')
async def download_wallet(download_id: UUID, user: User = Depends(wallet_user)):
    target = WalletArtifacts().get(tenant_key(), user.id, str(download_id))
    return FileResponse(target, media_type='application/zip', filename='carteira.zip',
                        headers={'Cache-Control': 'no-store'})


@router.post('/carteira/{download_id}/confirmar', status_code=204)
async def confirm_wallet(download_id: UUID, user: User = Depends(wallet_user)):
    await run_in_threadpool(WalletArtifacts().acknowledge, tenant_key(), user.id, str(download_id))
    return Response(status_code=204)
