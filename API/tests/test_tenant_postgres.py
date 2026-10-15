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


def test_full_clone_migrations_and_original_preserved(pg_tmp_path):
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
                    assert cursor.fetchone() == ("20260810_0049",)
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
    finally:
        run([pg_bin / "pg_ctl", "-D", cluster, "-m", "fast", "-w", "stop"], check=False)
