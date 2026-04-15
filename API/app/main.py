import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.v1.router import api_router
from app.controllers.webhook_controller import router as webhook_router
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.parameter_service import ParameterService


app = FastAPI(
    title=settings.project_name,
    version=settings.project_version,
    description=(
        "API de teste para gerenciamento de usuarios do banco Contratos, "
        "implementada com FastAPI assincrona, SQLAlchemy e Alembic."
    ),
    summary="API assincrona de usuarios",
    docs_url="/swagger",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1, "displayRequestDuration": True},
    openapi_tags=[
        {"name": "health", "description": "Verificacao de disponibilidade da API."},
        {"name": "auth", "description": "Autenticacao com JWT e consulta do usuario autenticado."},
        {"name": "acesso", "description": "Perfis, permissoes parametrizadas e controle de acesso."},
        {"name": "chat", "description": "Chat interno com conversas entre usuarios e notificacoes em tempo real."},
        {"name": "localidades", "description": "Consultas de UF, cidade, bairro e resolucao de CEP/endereco."},
        {"name": "apis", "description": "Cadastro de APIs externas vinculadas aos usuarios."},
        {"name": "parametros", "description": "Cadastro unico da empresa, score de clientes e automacoes preparatorias."},
        {"name": "usuarios", "description": "Operacoes de cadastro, consulta, atualizacao e remocao de usuarios."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(webhook_router, prefix="/webhooks", tags=["webhooks"])


async def _parameter_scheduler_loop() -> None:
    while True:
        try:
            async with AsyncSessionLocal() as session:
                service = ParameterService(session)
                await service.run_due_scheduled_actions()
        except Exception:
            pass
        await asyncio.sleep(60)


@app.on_event("startup")
async def start_parameter_scheduler() -> None:
    app.state.parameter_scheduler_task = asyncio.create_task(_parameter_scheduler_loop())


@app.on_event("shutdown")
async def stop_parameter_scheduler() -> None:
    task = getattr(app.state, "parameter_scheduler_task", None)
    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/swagger")


@app.get("/health", tags=["health"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
