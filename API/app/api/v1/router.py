from fastapi import APIRouter

from app.controllers.access_control_controller import router as access_control_router
from app.controllers.auth_controller import router as auth_router
from app.controllers.location_controller import router as location_router
from app.controllers.payment_plan_controller import router as payment_plan_router
from app.controllers.user_controller import router as users_router, ws_router as users_ws_router


api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(access_control_router, prefix="/acesso", tags=["acesso"])
api_router.include_router(location_router, prefix="/localidades", tags=["localidades"])
api_router.include_router(payment_plan_router, prefix="/financeiro", tags=["financeiro"])
api_router.include_router(users_ws_router, prefix="/usuarios", tags=["usuarios"])
api_router.include_router(users_router, prefix="/usuarios", tags=["usuarios"])
