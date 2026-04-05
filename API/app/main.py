from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.v1.router import api_router
from app.core.config import settings


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
        {"name": "usuarios", "description": "Operacoes de cadastro, consulta, atualizacao e remocao de usuarios."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5174",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/swagger")


@app.get("/health", tags=["health"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
