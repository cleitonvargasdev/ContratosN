"""Container-side provisioning operations. Called only by the Ubuntu service, never HTTP."""
import argparse
import json
import os
import secrets
import sys
import time
from pathlib import Path

import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tenancy.admin import AdminUser  # Register all registry models.
from app.tenancy.bootstrap import seed_database
from app.tenancy.provisioning import ProvisionJob, decode_payload, encode_payload
from app.tenancy.registry import TenantDomain, TenantRecord, secret_from_env
from scripts.migrate_databases import migrate


STEPS = {"dns", "database", "nginx", "certificate", "verification"}
ERRORS = {
    "dns": "Domínio não aponta exclusivamente para os IPs configurados no provisionador.",
    "database": "Não foi possível preparar o banco. Confira permissões PostgreSQL, migrações e variáveis no servidor.",
    "nginx": "Não foi possível configurar o Nginx. Confira conflito de domínio e nginx -t.",
    "certificate": "Falha na emissão do certificado. Confira DNS, porta 80 e logs do Certbot no Ubuntu.",
    "verification": "A verificação HTTPS ou o login inicial falhou. Confira o proxy e a API.",
}


def atomic_secret(name, value):
    directory = Path(settings.tenant_runtime_dir) / "secrets"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = directory / f"{name}.secret"
    temporary = directory / f".{name}.{secrets.token_hex(6)}"
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            output.write(value)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def create_owned_database(job_id, password):
    name = f"tenant_{job_id}"
    marker = f"tenant-provision:{job_id}"
    connection = psycopg2.connect(host=settings.db_host, port=settings.db_port, user=settings.db_user,
                                 password=settings.db_password, dbname="postgres", connect_timeout=15)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT shobj_description(oid, 'pg_authid') FROM pg_roles WHERE rolname=%s", (name,))
            role = cursor.fetchone()
            if role:
                if role[0] != marker:
                    raise ValueError("Role existente não pertence a esta criação")
            else:
                # Both statements are transactional: never adopt an existing role on retry.
                cursor.execute("BEGIN")
                cursor.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD %s NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION").format(sql.Identifier(name)), (password,))
                cursor.execute(sql.SQL("COMMENT ON ROLE {} IS %s").format(sql.Identifier(name)), (marker,))
                cursor.execute("COMMIT")
            cursor.execute("SELECT shobj_description(oid, 'pg_database') FROM pg_database WHERE datname=%s", (name,))
            existing = cursor.fetchone()
            if existing:
                if existing[0] != marker:
                    raise ValueError("Banco existente não pertence a esta criação")
            else:
                cursor.execute(sql.SQL("CREATE DATABASE {} OWNER {} TEMPLATE template0").format(sql.Identifier(name), sql.Identifier(name)))
                cursor.execute(sql.SQL("COMMENT ON DATABASE {} IS %s").format(sql.Identifier(name)), (marker,))
            cursor.execute(sql.SQL("REVOKE CONNECT ON DATABASE {} FROM PUBLIC").format(sql.Identifier(name)))
        return make_url(settings.database_url("postgresql+psycopg2", name)).set(username=name, password=password)
    finally:
        connection.close()


def prepare(session, job, tenant, domain):
    snapshot = decode_payload(job.payload)
    if "database_password" not in snapshot:
        snapshot["database_password"] = secrets.token_urlsafe(36)
        snapshot["webhook_secret"] = secrets.token_urlsafe(48)
        job.payload = encode_payload(snapshot)
        session.commit()  # Persist before any infrastructure mutation so retries keep credentials.
    url = create_owned_database(job.id, snapshot["database_password"])
    migrate(url.render_as_string(hide_password=False))
    seed_database(url, job.id, domain, snapshot)
    atomic_secret(tenant.database_url_env, url.set(drivername="postgresql+asyncpg").render_as_string(hide_password=False))
    atomic_secret(tenant.webhook_secret_env, snapshot["webhook_secret"])
    # Environment overrides must not silently route to another database.
    if make_url(secret_from_env(tenant.database_url_env)) != url.set(drivername="postgresql+asyncpg"):
        raise ValueError("Referência de conexão foi sobrescrita pelo ambiente")


def run(action, job_id=None, step=None):
    if not settings.tenant_provisioning_enabled or not settings.tenancy_enabled or not settings.tenant_runtime_dir:
        raise ValueError("Provisionamento não configurado")
    runtime = Path(settings.tenant_runtime_dir)
    runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    (runtime / "worker-heartbeat").touch()
    engine = create_engine(settings.database_url("postgresql+psycopg2", settings.tenant_registry_db_name))
    try:
        # Keep one physical registry connection across commits. A job lock protects
        # against a Docker exec still finishing after its host service was restarted.
        with engine.connect() as connection, Session(connection, expire_on_commit=False) as session:
            if action == "next":
                job = session.scalar(select(ProvisionJob).where(ProvisionJob.state.in_(["queued", "running"]))
                                     .order_by(ProvisionJob.created_at).with_for_update(skip_locked=True).limit(1))
                if not job:
                    return None
                job.state, job.updated_at, job.error = "running", int(time.time()), None
                session.commit()
            else:
                job = session.get(ProvisionJob, job_id)
                if job is None or job.state != "running":
                    raise ValueError("Criação não está em execução")
            tenant = session.get(TenantRecord, job.tenant_id)
            if action == "next":
                # A process interrupted during final verification must close access on resume.
                tenant.active = False
            domains = list(session.scalars(select(TenantDomain.hostname).where(TenantDomain.tenant_id == tenant.id)))
            if len(domains) != 1:
                raise ValueError("Criação automática exige um domínio")
            if action == "prepare":
                session.execute(text("SELECT pg_advisory_lock(hashtext(:job_id))"), {"job_id": job.id})
                prepare(session, job, tenant, domains[0])
            elif action == "activate":
                tenant.active = True
            elif action == "finish":
                if not tenant.active:
                    raise ValueError("Tenant ainda não foi validado")
                job.state, job.step = "ready", "ready"
            elif action == "fail":
                tenant.active = False
                job.state, job.step, job.error = "failed", step, ERRORS[step]
            elif action == "step":
                job.step = step
            job.updated_at = int(time.time())
            session.commit()
            return {"id": job.id, "tenant_id": tenant.id, "domain": domains[0], "state": job.state}
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["next", "step", "prepare", "activate", "finish", "fail"])
    parser.add_argument("job_id", nargs="?")
    parser.add_argument("--step", choices=sorted(STEPS))
    args = parser.parse_args()
    if args.action in {"step", "fail"} and args.step is None:
        parser.error("--step é obrigatório")
    try:
        print(json.dumps(run(args.action, args.job_id, args.step)))
    except Exception as exc:
        # Driver exception messages may include connection strings. Keep logs credential-free.
        print(f"Operação de provisionamento falhou ({type(exc).__name__}).", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
