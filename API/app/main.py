import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.v1.router import api_router
from app.controllers.webhook_controller import router as webhook_router
from app.core.config import settings
from app.db.session import AsyncSessionLocal, dispose_engines
from app.tenancy.context import tenant_scope
from app.tenancy.middleware import TenantMiddleware
from app.tenancy.registry import registry
from app.tenancy.admin import router as tenant_admin_router
from app.services.parameter_service import ParameterService
from app.services.whatsapp_chatbot_session_cleanup_service import WhatsAppChatbotSessionCleanupService


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
        {"name": "marcas", "description": "Operacoes de cadastro, consulta, atualizacao e remocao de marcas de produtos."},
        {"name": "parametros", "description": "Cadastro unico da empresa, score de clientes e automacoes preparatorias."},
        {"name": "produtos", "description": "Operacoes de cadastro, consulta, atualizacao e remocao de produtos."},
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
app.add_middleware(TenantMiddleware)

logger = logging.getLogger(__name__)

app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(tenant_admin_router)
app.include_router(webhook_router, prefix="/webhooks", tags=["webhooks"])


async def _run_for_tenants(action, *, automation: bool = False) -> None:
    tenants = await registry.list_active() if settings.tenancy_enabled else [None]
    for tenant in tenants:
        if tenant is not None and automation and not tenant.automations_enabled:
            continue
        try:
            with tenant_scope(tenant):
                async with AsyncSessionLocal() as session:
                    await action(session)
        except Exception:
            logger.error("Rotina falhou para empresa %s", tenant.id if tenant else "legacy")


async def _parameter_scheduler_loop() -> None:
    while True:
        try:
            await _run_for_tenants(lambda session: ParameterService(session).run_due_scheduled_actions(), automation=True)
        except Exception:
            logger.error("Nao foi possivel consultar empresas para rotinas")
        await asyncio.sleep(60)


async def _chatbot_session_cleanup_loop() -> None:
    while True:
        try:
            await _run_for_tenants(lambda session: WhatsAppChatbotSessionCleanupService(session).close_inactive_sessions())
        except Exception:
            logger.error("Nao foi possivel consultar empresas para limpeza de sessoes")
        await asyncio.sleep(600)


@app.on_event("startup")
async def start_parameter_scheduler() -> None:
    if settings.tenancy_enabled or settings.tenant_provisioning_enabled:
        from app.tenancy.initial_config import initialize_config
        await initialize_config()
    app.state.parameter_scheduler_task = asyncio.create_task(_parameter_scheduler_loop())
    app.state.chatbot_session_cleanup_task = asyncio.create_task(_chatbot_session_cleanup_loop())


@app.on_event("shutdown")
async def stop_parameter_scheduler() -> None:
    task = getattr(app.state, "parameter_scheduler_task", None)
    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    chatbot_cleanup_task = getattr(app.state, "chatbot_session_cleanup_task", None)
    if chatbot_cleanup_task is not None:
        chatbot_cleanup_task.cancel()
        try:
            await chatbot_cleanup_task
        except asyncio.CancelledError:
            pass

    await dispose_engines()
    await registry.dispose()


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/swagger")


@app.get("/health", tags=["health"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
