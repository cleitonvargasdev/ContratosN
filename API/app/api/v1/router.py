from fastapi import APIRouter

from app.controllers.api_config_controller import router as api_config_router
from app.controllers.chat_controller import router as chat_router, ws_router as chat_ws_router
from app.controllers.access_control_controller import router as access_control_router
from app.controllers.auth_controller import router as auth_router
from app.controllers.client_controller import router as clients_router
from app.controllers.contract_controller import public_router as contracts_public_router, router as contracts_router
from app.controllers.location_controller import router as location_router
from app.controllers.parameter_controller import router as parameters_router
from app.controllers.payment_plan_controller import router as payment_plan_router
from app.controllers.user_controller import router as users_router, ws_router as users_ws_router
from app.controllers.whatsapp_controller import router as whatsapp_router


api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(access_control_router, prefix="/acesso", tags=["acesso"])
api_router.include_router(location_router, prefix="/localidades", tags=["localidades"])
api_router.include_router(api_config_router, prefix="/apis", tags=["apis"])
api_router.include_router(clients_router, prefix="/clientes", tags=["clientes"])
api_router.include_router(contracts_public_router, prefix="/contratos", tags=["contratos"])
api_router.include_router(contracts_router, prefix="/contratos", tags=["contratos"])
api_router.include_router(parameters_router, prefix="/parametros", tags=["parametros"])
api_router.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])
api_router.include_router(payment_plan_router, prefix="/financeiro", tags=["financeiro"])
api_router.include_router(chat_ws_router, prefix="/chat", tags=["chat"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(users_ws_router, prefix="/usuarios", tags=["usuarios"])
api_router.include_router(users_router, prefix="/usuarios", tags=["usuarios"])
