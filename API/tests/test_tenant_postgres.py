"""Opt-in integration: isolated temporary PostgreSQL cluster, no project database access.

RUN_POSTGRES_INTEGRATION=1, POSTGRES_BIN and BASH_BIN must be set to local executables.
"""
import os
from pathlib import Path
import secrets
import socket
import subprocess
import tempfile

import psycopg2
import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from app.core.config import ROOT_DIR
from app.models.parameter import Parametro
from scripts.migrate_databases import migrate


pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_INTEGRATION") != "1", reason="Temporary PostgreSQL integration is opt-in")


@pytest.fixture
def pg_tmp_path():
    with tempfile.TemporaryDirectory(prefix="tenant-pg-") as directory:
        yield Path(directory)


def test_full_clone_migrations_and_original_preserved(pg_tmp_path, monkeypatch):
    tmp_path = pg_tmp_path
    pg_bin = Path(os.environ["POSTGRES_BIN"])
    bash = os.environ["BASH_BIN"]
    with socket.socket() as port_socket:
        port_socket.bind(("127.0.0.1", 0))
        port = port_socket.getsockname()[1]
    password = secrets.token_urlsafe(32)
    password_file = tmp_path / "password"
    password_file.write_text(password, encoding="utf-8")
    cluster = tmp_path / "cluster"
    env = {**os.environ, "PGHOST": "127.0.0.1", "PGPORT": str(port), "PGUSER": "tenant_test",
           "PGPASSWORD": password, "PGCONNECT_TIMEOUT": "5", "SOURCE_DB": "Contratos",
           "CV_DB": "cv_financeiro", "BC_DB": "bc_financeiro", "REGISTRY_DB": "tenant_registry",
           "BACKUP_DIR": (tmp_path / "backups").as_posix(), "PATH": str(pg_bin) + os.pathsep + os.environ["PATH"]}
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    def run(args, check=True):
        # pg_ctl's child may inherit pipe handles on Windows. Files let us wait
        # for pg_ctl itself without waiting for the database server to exit.
        with tempfile.TemporaryFile(mode="w+t") as output, tempfile.TemporaryFile(mode="w+t") as errors:
            result = subprocess.run([str(arg) for arg in args], env=env, cwd=ROOT_DIR,
                                    stdout=output, stderr=errors, text=True, timeout=120, creationflags=flags)
            output.seek(0)
            errors.seek(0)
            result.stdout, result.stderr = output.read(), errors.read()
        if check and result.returncode:
            pytest.fail(result.stdout + result.stderr)
        return result

    def connect(database):
        return psycopg2.connect(host="127.0.0.1", port=port, user="tenant_test", password=password, dbname=database)

    def url(database):
        return URL.create("postgresql+psycopg2", username="tenant_test", password=password,
                          host="127.0.0.1", port=port, database=database).render_as_string(hide_password=False)

    run([pg_bin / "initdb", "-D", cluster, "-U", "tenant_test", "--auth=scram-sha-256", "--pwfile", password_file,
         "--encoding=UTF8", "--no-locale"])
    try:
        run([pg_bin / "pg_ctl", "-D", cluster, "-l", tmp_path / "postgres.log", "-o", f"-h 127.0.0.1 -p {port}", "-w", "start"])
        admin = connect("postgres")
        try:
            admin.autocommit = True
            with admin.cursor() as cursor:
                cursor.execute('CREATE DATABASE "Contratos"')
        finally:
            admin.close()
        migrate(url("Contratos"))
        source_engine = create_engine(url("Contratos"))
        try:
            with source_engine.begin() as connection:
                connection.execute(Parametro.__table__.insert().values(
                    parametros_id=1, nome_fantasia="Origem de teste",
                    score_atualizacao_automatica=True, whatsapp_cobranca_automatica=True))
                connection.exec_driver_sql("CREATE TABLE tenant_probe (id serial PRIMARY KEY, value text NOT NULL)")
                connection.exec_driver_sql("INSERT INTO tenant_probe (value) VALUES ('original')")
        finally:
            source_engine.dispose()

        cloned = run([bash, "scripts/clone_tenant_databases.sh"])
        assert "Copia concluida" in cloned.stdout
        duplicate = run([bash, "scripts/clone_tenant_databases.sh"], check=False)
        assert duplicate.returncode != 0
        assert "ja existe" in duplicate.stderr

        for database in ("cv_financeiro", "bc_financeiro"):
            migrate(url(database))
            connection = connect(database)
            try:
                with connection, connection.cursor() as cursor:
                    cursor.execute("SELECT value FROM tenant_probe WHERE id=1")
                    assert cursor.fetchone() == ("original",)
                    cursor.execute("SELECT score_atualizacao_automatica, whatsapp_cobranca_automatica FROM parametros")
                    assert cursor.fetchone() == (False, False)
                    cursor.execute("SELECT version_num FROM alembic_version")
                    assert cursor.fetchone() == ("20261015_0050",)
                    cursor.execute("INSERT INTO tenant_probe (value) VALUES ('new') RETURNING id")
                    assert cursor.fetchone() == (2,)
            finally:
                connection.close()

        source = connect("Contratos")
        try:
            with source.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM tenant_probe")
                assert cursor.fetchone() == (1,)
                cursor.execute("SELECT score_atualizacao_automatica, whatsapp_cobranca_automatica FROM parametros")
                assert cursor.fetchone() == (True, True)
        finally:
            source.close()
        assert len(list((tmp_path / "backups").glob("*.dump"))) == 1

        # Provision a separate empty business database, never a copy of source business rows.
        from app.core.config import settings
        from app.core.secrets import encrypt_secret, decrypt_secret
        from app.core.security import verify_password
        from app.tenancy.bootstrap import seed_database
        from scripts.tenant_provision import create_owned_database
        for key, value in {"db_host": "127.0.0.1", "db_port": port, "db_user": "tenant_test", "db_password": password}.items():
            monkeypatch.setattr(settings, key, value)
        job_id = "b" * 32
        provision_url = create_owned_database(job_id, "isolated-test-password")
        migrate(provision_url.render_as_string(hide_password=False))
        snapshot = {"profiles": [{"nome": "Operacional", "descricao": "Modelo", "ativo": True, "permissions": []}],
                    "parameters": {"nome_fantasia": "Sua empresa", "razao_social": "Sua razão social",
                        "score_valor_inicial": 500, "score_pontos_atraso_parcela": -4,
                        "api_whatsapp": "quepasa", "usuario_api_whatsapp": "user@example.test",
                        "token_api_whatsapp": encrypt_secret("token-with-thirty-six-characters-long"),
                        "sufixo_whatsapp": "@s.whatsapp.net", "pais_whatsapp": 55},
                    "apis": [{"nome_api": "quepasa", "funcionalidade": "mensagem", "url": "https://example.test/send",
                              "key1": "X-TOKEN", "value1": "{token_api_whatsapp}"}]}
        seed_database(provision_url, job_id, "new.example.test", snapshot)
        target = create_engine(provision_url)
        try:
            with target.connect() as connection:
                from sqlalchemy import text
                row = connection.execute(text("SELECT login, funcao, senha_hash FROM usuarios")).one()
                assert row.login == "Admin" and row.funcao == "Administrador"
                assert verify_password("Admin", row.senha_hash)
                assert connection.scalar(text("SELECT count(*) FROM contratos")) == 0
                assert connection.scalar(text("SELECT count(*) FROM clientes")) == 0
                assert connection.scalar(text("SELECT count(*) FROM usuarios_perfis up JOIN perfis p ON p.id=up.perfil_id WHERE p.nome='Administrador'")) == 1
                params = connection.execute(text("SELECT * FROM parametros")).one()
                assert params.nome_fantasia == "Sua empresa" and params.score_valor_inicial == 500
                assert params.score_pontos_atraso_parcela == -4
                assert decrypt_secret(params.token_api_whatsapp) == "token-with-thirty-six-characters-long"
                assert params.whatsapp_cobranca_automatica is False
                assert connection.scalar(text("SELECT count(*) FROM apis")) == 1
                assert connection.scalar(text("SELECT count(*) FROM apis a JOIN usuarios u ON u.id=a.usuario_id WHERE u.login='Admin'")) == 1
            # Resume must preserve already initialized users, parameters and API rows.
            with target.begin() as connection:
                connection.execute(text("UPDATE parametros SET nome_fantasia='Empresa editada'"))
            assert create_owned_database(job_id, "isolated-test-password").database == provision_url.database
            seed_database(provision_url, job_id, "new.example.test", snapshot)
            with target.connect() as connection:
                assert connection.scalar(text("SELECT count(*) FROM usuarios")) == 1
                assert connection.scalar(text("SELECT nome_fantasia FROM parametros")) == "Empresa editada"
                assert connection.scalar(text("SELECT count(*) FROM apis")) == 1
        finally:
            target.dispose()

        # Exercise the durable queue/CLI on PostgreSQL, including secret files and state.
        from sqlalchemy.orm import Session
        from app.tenancy.registry import RegistryBase, TenantRecord, TenantDomain, secret_from_env
        from app.tenancy.provisioning import ProvisionJob, encode_payload
        from scripts.tenant_provision import run as provision_command
        monkeypatch.setattr(settings, "tenant_registry_db_name", "tenant_registry")
        monkeypatch.setattr(settings, "tenant_runtime_dir", str(tmp_path / "runtime"))
        monkeypatch.setattr(settings, "tenant_provisioning_enabled", True)
        monkeypatch.setattr(settings, "tenancy_enabled", True)
        registry_engine = create_engine(url("tenant_registry"))
        queue_id = "c" * 32
        try:
            RegistryBase.metadata.create_all(registry_engine)
            with Session(registry_engine) as session:
                session.add(TenantRecord(id="new", company_code="new", active=False,
                    database_url_env="TENANT_AUTO_TEST_DATABASE_URL", webhook_secret_env="TENANT_AUTO_TEST_WEBHOOK_SECRET",
                    public_base_url="https://new.example.test", automations_enabled=False, whatsapp_enabled=False))
                session.flush()
                session.add(TenantDomain(hostname="new.example.test", tenant_id="new"))
                session.add(ProvisionJob(id=queue_id, tenant_id="new", payload=encode_payload(snapshot)))
                session.commit()
            assert provision_command("next")["id"] == queue_id
            assert provision_command("prepare", queue_id)["state"] == "running"
            assert "tenant_" + queue_id in secret_from_env("TENANT_AUTO_TEST_DATABASE_URL")
            assert len(secret_from_env("TENANT_AUTO_TEST_WEBHOOK_SECRET")) >= 32
            provision_command("prepare", queue_id)  # Resume is idempotent through the real worker entry point.
            provision_command("fail", queue_id, "certificate")
            with Session(registry_engine) as session:
                assert session.get(TenantRecord, "new").active is False
                assert session.get(ProvisionJob, queue_id).state == "failed"
        finally:
            registry_engine.dispose()
    finally:
        run([pg_bin / "pg_ctl", "-D", cluster, "-m", "fast", "-w", "stop"], check=False)
