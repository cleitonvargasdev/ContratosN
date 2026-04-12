from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db_session
from app.schemas.parameter import ParameterAutomationRunResponse, ParameterRead, ParameterUpdate
from app.services.parameter_service import ParameterService


router = APIRouter(dependencies=[Depends(get_current_active_user)])


def get_parameter_service(session: AsyncSession = Depends(get_db_session)) -> ParameterService:
    return ParameterService(session)


@router.get("/", response_model=ParameterRead, summary="Consultar parametros da empresa")
async def get_parameters(service: ParameterService = Depends(get_parameter_service)) -> ParameterRead:
    parameter = await service.get_parameters()
    return ParameterRead.model_validate(parameter)


@router.get("/whatsapp-apis", response_model=list[str], summary="Listar APIs disponiveis para WhatsApp")
async def list_whatsapp_api_names(service: ParameterService = Depends(get_parameter_service)) -> list[str]:
    return await service.list_whatsapp_api_names()


@router.put("/", response_model=ParameterRead, summary="Salvar parametros da empresa")
async def update_parameters(
    payload: ParameterUpdate,
    service: ParameterService = Depends(get_parameter_service),
) -> ParameterRead:
    parameter = await service.update_parameters(payload)
    return ParameterRead.model_validate(parameter)


@router.post("/executar-rotinas", response_model=ParameterAutomationRunResponse, summary="Executar rotinas preparatorias")
async def run_parameter_automations(
    service: ParameterService = Depends(get_parameter_service),
) -> ParameterAutomationRunResponse:
    return await service.run_scheduled_actions()