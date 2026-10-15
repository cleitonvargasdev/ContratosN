import json
import logging
from urllib.parse import parse_qs

from fastapi import HTTPException
from jose import JWTError, jwt
from starlette.requests import HTTPConnection
from starlette.responses import JSONResponse

from app.core.config import settings
from app.tenancy.context import tenant_scope
from app.tenancy.registry import registry


logger = logging.getLogger(__name__)


async def resolve_tenant(connection, body: bytes = b"", tenant_registry=registry):
    # Only Host from our reverse proxy is used. Forwarded host headers are ignored.
    hostname = (connection.url.hostname or "").lower().rstrip(".")
    tenant = await tenant_registry.find(hostname=hostname)
    api_hosts = {host.strip().lower() for host in settings.tenant_api_hosts.split(",") if host.strip()}
    if tenant is None and hostname not in api_hosts:
        raise HTTPException(404, "Empresa nao encontrada")

    path = connection.url.path
    code = connection.headers.get("x-company-code") if connection.headers.get(settings.api_key_header_name) else None
    token = None
    authorization = connection.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        token = authorization[7:]
    if connection.scope["type"] == "websocket" or path.startswith(f"{settings.api_v1_prefix}/contratos/publico/"):
        token = connection.query_params.get("token") or token
    if path == f"{settings.api_v1_prefix}/auth/login":
        form = parse_qs(body.decode("utf-8"))
        code = (form.get("company_code", [None])[0] or connection.headers.get("x-company-code"))
    elif path == f"{settings.api_v1_prefix}/auth/refresh":
        try:
            payload = json.loads(body)
            token = payload.get("refresh_token") if isinstance(payload, dict) else None
        except (ValueError, UnicodeDecodeError):
            raise HTTPException(400, "Requisicao invalida")

    if code:
        selected = await tenant_registry.find(company_code=code.strip().lower())
        if selected is None:
            raise HTTPException(404, "Empresa nao encontrada")
        if tenant and selected.id != tenant.id:
            raise HTTPException(403, "Empresa nao corresponde ao dominio")
        tenant = selected

    if token:
        try:
            claims = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        except JWTError:
            raise HTTPException(401, "Token invalido")
        token_tenant = claims.get("tenant_id")
        if not isinstance(token_tenant, str) or not token_tenant:
            raise HTTPException(401, "Entre novamente para identificar a empresa")
        if tenant and tenant.id != token_tenant:
            raise HTTPException(401, "Token nao pertence a esta empresa")
        if tenant is None:
            tenant = await tenant_registry.find(tenant_id=token_tenant)

    if tenant is None:
        raise HTTPException(404, "Empresa nao encontrada")
    if not tenant.active:
        raise HTTPException(403, "Empresa inativa")
    return tenant


class TenantMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if not settings.tenancy_enabled or scope["type"] not in {"http", "websocket"}:
            return await self.app(scope, receive, send)
        path = scope.get("path", "")
        # Platform routes authenticate against cad_usuario, never a business tenant.
        if path.startswith("/api/platform/"):
            return await self.app(scope, receive, send)
        if path in {"/", "/health", "/swagger", "/swagger/oauth2-redirect", "/redoc", "/openapi.json"} or scope.get("method") == "OPTIONS":
            return await self.app(scope, receive, send)
        body = b""
        original_receive = receive
        try:
            if path in {f"{settings.api_v1_prefix}/auth/login", f"{settings.api_v1_prefix}/auth/refresh"} and scope["type"] == "http":
                while True:
                    message = await original_receive()
                    if message["type"] == "http.disconnect":
                        return
                    body += message.get("body", b"")
                    if len(body) > 16384:
                        raise HTTPException(413, "Requisicao muito grande")
                    if not message.get("more_body", False):
                        break
                replayed = False

                async def receive():
                    nonlocal replayed
                    if not replayed:
                        replayed = True
                        return {"type": "http.request", "body": body, "more_body": False}
                    return await original_receive()

            tenant = await resolve_tenant(HTTPConnection(scope), body)
        except HTTPException as exc:
            return await self.reject(scope, receive, send, exc.status_code, exc.detail)
        except Exception:
            # Connection errors can contain database names/credentials; do not log them.
            logger.error("Registro de empresas indisponivel")
            return await self.reject(scope, receive, send, 503, "Registro de empresas indisponivel")
        scope["tenant_id"] = tenant.id
        with tenant_scope(tenant):
            await self.app(scope, receive, send)

    @staticmethod
    async def reject(scope, receive, send, status, detail):
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
        else:
            await JSONResponse({"detail": detail}, status_code=status)(scope, receive, send)
