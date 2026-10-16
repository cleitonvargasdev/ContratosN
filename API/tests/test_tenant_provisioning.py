import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.secrets import decrypt_secret
from app.tenancy import admin as admin_module
from app.tenancy.provisioning import BootstrapInput, ProvisionJob, decode_payload, new_job
from app.tenancy.registry import secret_from_env
from scripts.tenant_host_worker import Worker, checked_domain, execute, verify_dns
from tests.test_tenant_admin import panel, authenticate


def template():
    return {"parameters": {"score_valor_inicial": 500, "usuario_api_whatsapp": "user@example.test",
            "token_api_whatsapp": "private-token", "pais_whatsapp": 55, "sufixo_whatsapp": "@s.whatsapp.net"},
            "profiles": [{"nome": "Administrador", "descricao": "Admin", "ativo": True, "permissions": []}],
            "apis": [{"nome_api": "quepasa", "funcionalidade": "mensagem", "value1": "secret-api-value"}]}


def test_snapshot_encryption_and_explicit_whatsapp_override():
    job = new_job("xyz", template(), BootstrapInput(usar_token_modelo=False, token_api_whatsapp="own-token"))
    assert "own-token" not in job.payload and "secret-api-value" not in job.payload
    snapshot = decode_payload(job.payload)
    assert snapshot["parameters"]["nome_fantasia"] == "Sua empresa"
    assert decrypt_secret(snapshot["parameters"]["token_api_whatsapp"]) == "own-token"
    assert snapshot["parameters"]["score_valor_inicial"] == 500
    assert template()["parameters"]["token_api_whatsapp"] == "private-token"


def test_queue_requires_admin_and_worker_and_reserves_domain(panel, monkeypatch):
    client, factory = panel
    payload = {"code": "xyz", "domains": ["xyz.example.test"], "public_base_url": "https://xyz.example.test",
               "provision": True, "bootstrap": {"usuario_api_whatsapp": "user@example.test"}}
    assert client.post("/api/platform/tenants", json=payload).status_code == 401
    headers = authenticate(client)
    monkeypatch.setattr(admin_module, "worker_available", lambda: False)
    assert client.post("/api/platform/tenants", headers=headers, json=payload).status_code == 503
    monkeypatch.setattr(admin_module, "worker_available", lambda: True)
    monkeypatch.setattr(admin_module, "read_initial_config", AsyncMock(return_value=template()))
    response = client.post("/api/platform/tenants", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    row = response.json()
    assert row["active"] is False and row["whatsapp_enabled"] is False
    assert "private-token" not in response.text
    assert row["database_url_env"].startswith("TENANT_AUTO_")
    assert client.post("/api/platform/tenants", headers=headers, json=payload).status_code == 409
    assert len(client.get("/api/platform/tenants", headers=headers).json()) == 1
    result = client.get("/api/platform/provision/defaults", headers=headers)
    assert result.status_code == 200
    assert "private-token" not in result.text and "secret-api-value" not in result.text
    job_id = row["provisioning"]["id"]
    assert client.post(f"/api/platform/provision/jobs/{job_id}/retry", headers=headers).status_code == 409

    async def mark_failed():
        async with factory() as session:
            job = await session.get(ProvisionJob, job_id)
            assert "private-token" not in job.payload
            job.state, job.error = "failed", "DNS inválido"
            await session.commit()
    asyncio.run(mark_failed())
    result = client.post(f"/api/platform/provision/jobs/{job_id}/retry", headers=headers)
    assert result.status_code == 200 and result.json()["state"] == "queued"
    assert result.json()["error"] is None


def test_managed_secrets_are_dynamic_and_existing_env_has_precedence(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "tenant_runtime_dir", str(tmp_path))
    path = tmp_path / "secrets"
    path.mkdir()
    value = path / "TENANT_AUTO_TEST_DATABASE_URL.secret"
    value.write_text("first", encoding="utf-8")
    assert secret_from_env("TENANT_AUTO_TEST_DATABASE_URL") == "first"
    value.write_text("second", encoding="utf-8")
    assert secret_from_env("TENANT_AUTO_TEST_DATABASE_URL") == "second"
    monkeypatch.setenv("TENANT_AUTO_TEST_DATABASE_URL", "explicit")
    assert secret_from_env("TENANT_AUTO_TEST_DATABASE_URL") == "explicit"
    with pytest.raises(Exception):
        secret_from_env("../../secret")


def test_dns_rejects_other_hosts_and_mixed_ipv6(monkeypatch):
    import socket
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(0, 0, 0, '', ('203.0.113.1', 443))])
    verify_dns("xyz.example.test", "203.0.113.1")
    with pytest.raises(ValueError):
        verify_dns("xyz.example.test", "203.0.113.2")
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(0, 0, 0, '', ('203.0.113.1', 443)), (0, 0, 0, '', ('::1', 443))])
    with pytest.raises(ValueError):
        verify_dns("xyz.example.test", "203.0.113.1")
    for invalid in ["localhost", "127.0.0.1", "x.test;echo hello", "x.test/../../etc", "-x.test", "https://x.test"]:
        with pytest.raises(ValueError):
            checked_domain(invalid)


def test_worker_failure_never_marks_ready(monkeypatch):
    worker = object.__new__(Worker)
    worker.allowed_ips = "203.0.113.1"
    calls = []
    worker.api = lambda action, job_id=None, step=None: calls.append((action, step))
    monkeypatch.setattr("scripts.tenant_host_worker.verify_dns", lambda *a: None)
    worker.configure_nginx = lambda job: None
    worker.certificate = lambda job: (_ for _ in ()).throw(RuntimeError("simulated"))
    worker.verify = lambda job: pytest.fail("Verification cannot run without certificate")
    worker.process({"id": "a" * 32, "tenant_id": "xyz", "domain": "xyz.example.test"})
    assert calls[-1] == ("fail", "certificate")
    assert not any(action in {"finish", "activate"} for action, _ in calls)


@pytest.mark.parametrize("comment", [b"# ASCII comment\n", b"# Configura\xe7\xe3o SSL\n"])
def test_nginx_is_owned_idempotent_and_preserves_certbot_changes(tmp_path, monkeypatch, comment):
    # Model symlinks for this Ubuntu worker test without requiring Windows symlink privilege.
    links = {}
    original_resolve, original_is_symlink = Path.resolve, Path.is_symlink
    monkeypatch.setattr(Path, "symlink_to", lambda path, target: links.update({str(path): Path(target)}))
    monkeypatch.setattr(Path, "is_symlink", lambda path: str(path) in links or original_is_symlink(path))
    monkeypatch.setattr(Path, "resolve", lambda path, *a, **kw: original_resolve(links.get(str(path), path), *a, **kw))
    worker = object.__new__(Worker)
    worker.nginx_root = tmp_path
    (tmp_path / "sites-available").mkdir()
    (tmp_path / "sites-enabled").mkdir()
    existing = tmp_path / "sites-enabled" / "existing.conf"
    existing_bytes = comment + b"server { server_name existing.example.test; }"
    existing.write_bytes(existing_bytes)
    job = {"id": "a" * 32, "domain": "new.example.test"}
    calls = []
    monkeypatch.setattr("scripts.tenant_host_worker.execute", lambda cmd, **kw: calls.append(cmd))
    worker.configure_nginx(job)
    target = tmp_path / "sites-available" / f"tenant-auto-{job['id']}.conf"
    text = target.read_text()
    assert "server_name new.example.test;" in text and "http://127.0.0.1:8080" in text
    certbot_bytes = text.encode("utf-8") + b"\n# Certbot-managed SSL configuration\n" + comment
    target.write_bytes(certbot_bytes)
    worker.configure_nginx(job)
    assert target.read_bytes() == certbot_bytes
    assert existing.read_bytes() == existing_bytes
    assert calls[-1] == ["systemctl", "reload", "nginx"]
    conflict = tmp_path / "sites-enabled" / "other.conf"
    conflict.write_bytes(comment + b"server { server_name new.example.test; }")
    with pytest.raises(ValueError):
        worker.configure_nginx(job)
    assert target.read_bytes() == certbot_bytes


def test_execute_handles_non_utf8_output_without_hiding_command_failure():
    script = "import sys; sys.stdout.buffer.write(b'ok\\xff'); sys.stderr.buffer.write(b'private\\xe7')"
    result = execute([sys.executable, "-c", script])
    assert result.encode("utf-8", errors="surrogateescape") == b"ok\xff"
    with pytest.raises(RuntimeError) as error:
        execute([sys.executable, "-c", script + "; sys.exit(1)"])
    assert str(error.value) == f"Comando falhou: {sys.executable}"


def test_provisioning_allows_first_start_without_active_tenants(monkeypatch):
    from scripts import migrate_databases
    monkeypatch.setattr(settings, "tenancy_enabled", True)
    monkeypatch.setattr(settings, "tenant_provisioning_enabled", True)
    monkeypatch.setattr(migrate_databases, "tenant_urls", AsyncMock(return_value=[]))
    migrate_databases.main()
    monkeypatch.setattr(settings, "tenant_provisioning_enabled", False)
    with pytest.raises(SystemExit):
        migrate_databases.main()
