"""Platform administration: independent identities and opaque sessions in the registry."""
import hashlib
import secrets
import time
from typing import Annotated
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import Boolean, ForeignKey, Integer, String, delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.tenancy.registry import RegistryBase, TenantDomain, TenantRecord, registry, secret_from_env
from app.tenancy.provisioning import BootstrapInput, ProvisionJob, job_output, new_job, read_template, worker_available


class AdminUser(RegistryBase):
    __tablename__ = "cad_usuario"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    login: Mapped[str] = mapped_column(String(64), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[int] = mapped_column(Integer, default=0)


class AdminSession(RegistryBase):
    __tablename__ = "tenant_admin_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("cad_usuario.id"), index=True)
    expires_at: Mapped[int] = mapped_column(Integer)


async def session_dependency():
    async with registry.session_factory()() as session:
        yield session


DB = Annotated[AsyncSession, Depends(session_dependency)]
bearer = HTTPBearer(auto_error=False)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def current_admin(db: DB, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if credentials is None:
        raise HTTPException(401, "Entre no painel Tenant")
    session = await db.get(AdminSession, token_hash(credentials.credentials))
    user = await db.get(AdminUser, session.user_id) if session and session.expires_at > int(time.time()) else None
    if user is None or not user.ativo:
        raise HTTPException(401, "Sessão expirada ou usuário inativo")
    return user


Admin = Annotated[AdminUser, Depends(current_admin)]
router = APIRouter(prefix="/api/platform", tags=["Administração Tenant"])


class LoginInput(BaseModel):
    login: str = Field(min_length=1, max_length=64)
    senha: str = Field(min_length=1, max_length=128)

    @field_validator("login")
    @classmethod
    def normalize_login(cls, value):
        return value.strip().upper()


class UserInput(LoginInput):
    nome: str = Field(min_length=1, max_length=120)
    ativo: bool = True

    @field_validator("nome")
    @classmethod
    def nonblank_name(cls, value):
        if not value.strip():
            raise ValueError("Informe o nome")
        return value.strip()


class UserUpdate(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    ativo: bool
    senha: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("nome")
    @classmethod
    def nonblank_name(cls, value):
        if not value.strip():
            raise ValueError("Informe o nome")
        return value.strip()


class UserOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    login: str
    ativo: bool


@router.post("/auth/login")
async def login(data: LoginInput, db: DB):
    user = await db.scalar(select(AdminUser).where(AdminUser.login == data.login).with_for_update())
    now = int(time.time())
    if user and user.locked_until > now:
        raise HTTPException(429, "Muitas tentativas. Tente novamente em 5 minutos")
    if user is None or not user.ativo or not verify_password(data.senha, user.senha_hash):
        if user:
            user.failed_attempts += 1
            if user.failed_attempts >= 5:
                user.locked_until = now + 300
                user.failed_attempts = 0
            await db.commit()
        raise HTTPException(401, "Usuário ou senha inválidos")
    user.failed_attempts = user.locked_until = 0
    token = secrets.token_urlsafe(48)
    await db.execute(delete(AdminSession).where(AdminSession.expires_at <= now))
    db.add(AdminSession(token_hash=token_hash(token), user_id=user.id, expires_at=now + 3600))
    await db.commit()
    return {"access_token": token, "token_type": "bearer", "user": UserOutput.model_validate(user)}


@router.get("/auth/me", response_model=UserOutput)
async def me(admin: Admin):
    return admin


@router.post("/auth/logout", status_code=204)
async def logout(db: DB, admin: Admin, credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]):
    await db.execute(delete(AdminSession).where(AdminSession.token_hash == token_hash(credentials.credentials)))
    await db.commit()


@router.get("/usuarios", response_model=list[UserOutput])
async def users(db: DB, admin: Admin):
    return (await db.scalars(select(AdminUser).order_by(AdminUser.login))).all()


async def commit(db):
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Já existe cadastro com este login, código, domínio ou referência")


@router.post("/usuarios", response_model=UserOutput, status_code=201)
async def create_user(data: UserInput, db: DB, admin: Admin):
    if not data.login:
        raise HTTPException(422, "Informe o login")
    user = AdminUser(nome=data.nome, login=data.login, ativo=data.ativo, senha_hash=hash_password(data.senha))
    db.add(user)
    await commit(db)
    return user


@router.put("/usuarios/{user_id}", response_model=UserOutput)
async def update_user(user_id: int, data: UserUpdate, db: DB, admin: Admin):
    user = await db.get(AdminUser, user_id)
    if user is None:
        raise HTTPException(404, "Usuário não encontrado")
    if user.id == admin.id and not data.ativo:
        raise HTTPException(422, "Você não pode desativar seu próprio acesso")
    user.nome, user.ativo = data.nome, data.ativo
    if data.senha:
        user.senha_hash = hash_password(data.senha)
        user.failed_attempts = user.locked_until = 0
    if data.senha or not data.ativo:
        await db.execute(delete(AdminSession).where(AdminSession.user_id == user.id))
    await commit(db)
    return user


class TenantInput(BaseModel):
    code: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,62}$")
    domains: list[str] = Field(min_length=1, max_length=20)
    public_base_url: str = Field(max_length=255)
    database_url_env: str = Field(default="", pattern=r"^TENANT_[A-Z0-9_]+$", max_length=128)
    webhook_secret_env: str = Field(default="", pattern=r"^TENANT_[A-Z0-9_]+$", max_length=128)
    provision: bool = False
    bootstrap: BootstrapInput | None = None
    active: bool = True
    automations_enabled: bool = False
    whatsapp_enabled: bool = False

    @field_validator("domains")
    @classmethod
    def validate_domains(cls, values):
        import re
        domains = list(dict.fromkeys(value.strip().lower().rstrip(".") for value in values))
        for domain in domains:
            if len(domain) > 253 or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*", domain):
                raise ValueError("Informe domínios sem protocolo, porta ou caminho")
        return domains

    @model_validator(mode="after")
    def validate_url(self):
        parsed = urlparse(self.public_base_url)
        if (parsed.scheme not in {"http", "https"} or parsed.hostname not in self.domains
                or parsed.path not in {"", "/"} or parsed.query or parsed.fragment or parsed.username):
            raise ValueError("A URL pública deve corresponder a um domínio cadastrado")
        self.public_base_url = self.public_base_url.rstrip("/")
        if self.provision:
            if parsed.scheme != "https" or parsed.port is not None or len(self.domains) != 1 or "." not in self.domains[0]:
                raise ValueError("Criação automática exige um único domínio público e HTTPS sem porta")
            if self.bootstrap is None:
                raise ValueError("Preencha a configuração inicial da empresa")
        elif not self.database_url_env or not self.webhook_secret_env:
            raise ValueError("Informe as referências de conexão e webhook")
        return self


async def validate_connection(data, db, tenant_id=None):
    try:
        url = make_url(secret_from_env(data.database_url_env))
        if url.get_backend_name() != "postgresql" or not url.database:
            raise ValueError()
        if url.database in {settings.db_name, settings.tenant_registry_db_name}:
            raise HTTPException(422, "Use um banco exclusivo da empresa, diferente da origem e do registro")
        if len(secret_from_env(data.webhook_secret_env)) < 32:
            raise HTTPException(422, "Configure no servidor um segredo de webhook com pelo menos 32 caracteres")
        for other in (await db.scalars(select(TenantRecord))).all():
            if other.id == tenant_id:
                continue
            other_url = make_url(secret_from_env(other.database_url_env))
            if (url.host, url.port or 5432, url.database) == (other_url.host, other_url.port or 5432, other_url.database):
                raise HTTPException(409, "Banco já utilizado por outra empresa")
    except HTTPException:
        raise
    except (ValueError, TypeError):
        raise HTTPException(422, "Configure uma conexão PostgreSQL válida na variável indicada")


def tenant_output(row, domains):
    return {"code": row.company_code, "id": row.id, "domains": domains,
            **{key: getattr(row, key) for key in ("public_base_url", "database_url_env", "webhook_secret_env", "active", "automations_enabled", "whatsapp_enabled")}}


@router.get("/tenants")
async def tenants(db: DB, admin: Admin):
    domains = (await db.scalars(select(TenantDomain).order_by(TenantDomain.hostname))).all()
    rows = (await db.scalars(select(TenantRecord).order_by(TenantRecord.company_code))).all()
    return [tenant_output(row, [d.hostname for d in domains if d.tenant_id == row.id]) for row in rows]


@router.post("/tenants", status_code=201)
async def create_tenant(data: TenantInput, db: DB, admin: Admin):
    # Serialize administrative registrations on PostgreSQL to protect database identity checks.
    if db.bind.dialect.name == "postgresql":
        from sqlalchemy import text
        await db.execute(text("SELECT pg_advisory_xact_lock(72419631)"))
    job = None
    if data.provision:
        if not worker_available():
            raise HTTPException(503, "Serviço de criação indisponível. Configure o provisionador no Ubuntu e ative o modo multitenant")
        job = new_job(data.code, await read_template(), data.bootstrap)
        data.database_url_env = f"TENANT_AUTO_{job.id.upper()}_DATABASE_URL"
        data.webhook_secret_env = f"TENANT_AUTO_{job.id.upper()}_WEBHOOK_SECRET"
        data.active = data.automations_enabled = data.whatsapp_enabled = False
    else:
        await validate_connection(data, db)
    row = TenantRecord(id=data.code, company_code=data.code, **data.model_dump(exclude={"code", "domains", "provision", "bootstrap"}))
    db.add(row)
    try:
        await db.flush()
        db.add_all(TenantDomain(hostname=domain, tenant_id=row.id) for domain in data.domains)
        if job:
            db.add(job)
        await commit(db)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Código ou referência já cadastrado")
    return {**tenant_output(row, data.domains), "provisioning": job_output(job) if job else None}


@router.put("/tenants/{tenant_id}")
async def update_tenant(tenant_id: str, data: TenantInput, db: DB, admin: Admin):
    row = await db.get(TenantRecord, tenant_id)
    if row is None:
        raise HTTPException(404, "Tenant não encontrado")
    job = await db.scalar(select(ProvisionJob).where(ProvisionJob.tenant_id == tenant_id))
    if job and job.state != "ready":
        raise HTTPException(409, "Aguarde a criação ou retome a etapa que falhou antes de editar")
    if job:
        current_domains = set(await db.scalars(select(TenantDomain.hostname).where(TenantDomain.tenant_id == tenant_id)))
        if current_domains != set(data.domains) or data.public_base_url != row.public_base_url:
            raise HTTPException(422, "Alterar o domínio de um site provisionado exige atualizar o Nginx e o certificado no servidor")
    if data.provision:
        raise HTTPException(422, "Um tenant existente não pode ser reprovisionado")
    if data.code != row.company_code or data.database_url_env != row.database_url_env:
        raise HTTPException(422, "Código e referência de banco são fixos; migrações exigem manutenção no servidor")
    if data.whatsapp_enabled or data.automations_enabled:
        await validate_connection(data, db, tenant_id)
    for key, value in data.model_dump(exclude={"code", "domains", "database_url_env", "provision", "bootstrap"}).items():
        setattr(row, key, value)
    await db.execute(delete(TenantDomain).where(TenantDomain.tenant_id == row.id))
    db.add_all(TenantDomain(hostname=domain, tenant_id=row.id) for domain in data.domains)
    await commit(db)
    return tenant_output(row, data.domains)


@router.get("/provision/defaults")
async def provisioning_defaults(admin: Admin):
    snapshot = await read_template()
    parameters = snapshot["parameters"]
    return {"available": worker_available(), "bootstrap": {
        "nome_fantasia": "Sua empresa", "razao_social": "Sua razão social", "usar_token_modelo": True,
        **{key: parameters.get(key) or (55 if key == "pais_whatsapp" else "") for key in (
            "usuario_api_whatsapp", "sufixo_whatsapp", "pais_whatsapp", "msg_renovacao", "msg_negociacao", "msg_campanha")}},
        "has_token": bool(parameters.get("token_api_whatsapp")),
        "score": {key: value for key, value in parameters.items() if key.startswith("score_")},
        "profiles": [p["nome"] for p in snapshot["profiles"]], "api_count": len(snapshot["apis"])}


@router.get("/provision/jobs")
async def provisioning_jobs(db: DB, admin: Admin):
    return [job_output(job) for job in (await db.scalars(select(ProvisionJob).order_by(ProvisionJob.created_at.desc()))).all()]


@router.post("/provision/jobs/{job_id}/retry")
async def retry_provisioning(job_id: str, db: DB, admin: Admin):
    job = await db.scalar(select(ProvisionJob).where(ProvisionJob.id == job_id).with_for_update())
    if job is None:
        raise HTTPException(404, "Criação não encontrada")
    if job.state != "failed":
        raise HTTPException(409, "Somente uma criação com falha pode ser retomada")
    if not worker_available():
        raise HTTPException(503, "O provisionador está indisponível")
    job.state, job.error, job.updated_at = "queued", None, int(time.time())
    await db.commit()
    return job_output(job)
