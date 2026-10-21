from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session, require_permission
from app.models.user import User
from app.schemas.mobile_batch import MobileBatchCreate, MobileBatchRead, MobileBatchUnlock
from app.services.mobile_batch_service import MobileBatchService

router = APIRouter()
mobile_user = require_permission("acesso_web", "read")
unlock_read_user = require_permission("contratos", "read")
unlock_user = require_permission("contratos", "update")


def service(session: AsyncSession = Depends(get_db_session)) -> MobileBatchService:
    return MobileBatchService(session)


@router.post("/lotes", status_code=status.HTTP_201_CREATED, response_model=MobileBatchRead)
async def create_batch(payload: MobileBatchCreate, user: User = Depends(mobile_user), svc: MobileBatchService = Depends(service)):
    return await svc.create(user, payload)


@router.get("/lotes/bloqueados", response_model=list[MobileBatchRead])
async def list_blocked_batches(admin: User = Depends(unlock_read_user), svc: MobileBatchService = Depends(service)):
    return await svc.list_blocked()


@router.get("/lotes/{batch_id}", response_model=MobileBatchRead)
async def get_batch(batch_id: int, user: User = Depends(mobile_user), svc: MobileBatchService = Depends(service)):
    return await svc.get(batch_id, user)


@router.post("/lotes/{batch_id}/executar", response_model=MobileBatchRead)
async def execute_batch(batch_id: int, user: User = Depends(mobile_user), svc: MobileBatchService = Depends(service)):
    return await svc.execute(batch_id, user)


@router.post("/lotes/{batch_id}/desbloquear", response_model=MobileBatchRead)
async def unlock_batch(batch_id: int, payload: MobileBatchUnlock, admin: User = Depends(unlock_user), svc: MobileBatchService = Depends(service)):
    return await svc.unlock(batch_id, admin, payload.reason)
