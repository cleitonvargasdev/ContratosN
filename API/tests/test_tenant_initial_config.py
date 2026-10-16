import asyncio
from copy import deepcopy

import pytest

from app.tenancy import initial_config
from app.tenancy.initial_config import ConfigData, InitialConfig, initialize_config
from app.tenancy.provisioning import BootstrapInput, ProvisionJob, decode_payload, new_job
from tests.test_tenant_admin import panel, authenticate


def sample():
    return ConfigData.model_validate({"parameters": {"nome_fantasia": "Empresa padrão",
        "score_pontos_atraso_parcela": -4, "token_api_whatsapp": "private-token"},
        "profiles": [{"nome": "Administrador", "permissions": []}],
        "apis": [{"nome_api": "API teste", "value1": "private-value"}]}).snapshot()


@pytest.fixture(autouse=True)
def config_file(monkeypatch):
    monkeypatch.setattr(initial_config, "bundled_config", sample)


def update_payload(result):
    return {key: deepcopy(result[key]) for key in ("version", "parameters", "profiles", "apis")}


def test_initialize_once_preserves_edits_and_encrypts(panel):
    client, factory = panel
    asyncio.run(initialize_config())
    headers = authenticate(client)
    assert client.get('/api/platform/provision/config').status_code == 401
    assert client.put('/api/platform/provision/config', json={}).status_code == 401
    response = client.get('/api/platform/provision/config', headers=headers)
    assert response.headers['cache-control'] == 'no-store'
    result = response.json()
    assert result['version'] == 1 and result['has_token']
    assert result['parameters']['token_api_whatsapp'] is None
    assert 'private-token' not in response.text
    payload = update_payload(result)
    payload['parameters']['nome_fantasia'] = 'Novo padrão'
    response = client.put('/api/platform/provision/config', headers=headers, json=payload)
    assert response.status_code == 200, response.text
    assert response.json()['version'] == 2
    assert response.json()['updated_by'] == 'ADMIN'
    assert client.put('/api/platform/provision/config', headers=headers, json=payload).status_code == 409
    asyncio.run(initialize_config())

    async def inspect():
        async with factory() as db:
            row = await db.get(InitialConfig, 1)
            assert row.version == 2
            assert 'private-token' not in row.payload and 'private-value' not in row.payload
            snapshot = decode_payload(row.payload)
            assert snapshot['parameters']['nome_fantasia'] == 'Novo padrão'
            assert snapshot['parameters']['token_api_whatsapp'] == 'private-token'
    asyncio.run(inspect())


def test_saved_config_is_used_and_jobs_keep_their_snapshot(panel, monkeypatch):
    from app.tenancy import admin
    client, factory = panel
    headers = authenticate(client)
    monkeypatch.setattr(admin, 'worker_available', lambda: True)
    result = client.get('/api/platform/provision/config', headers=headers).json()
    payload = update_payload(result)
    payload['parameters']['score_valor_inicial'] = 742
    payload['parameters']['nome_fantasia'] = 'Nome salvo'
    assert client.put('/api/platform/provision/config', headers=headers, json=payload).status_code == 200
    defaults = client.get('/api/platform/provision/defaults', headers=headers)
    assert defaults.json()['bootstrap']['nome_fantasia'] == 'Nome salvo'
    assert 'private-token' not in defaults.text and 'private-value' not in defaults.text
    response = client.post('/api/platform/tenants', headers=headers, json={
        'code': 'new', 'domains': ['new.example.test'], 'public_base_url': 'https://new.example.test',
        'provision': True, 'bootstrap': {}})
    assert response.status_code == 201, response.text
    job_id = response.json()['provisioning']['id']
    result = client.get('/api/platform/provision/config', headers=headers).json()
    payload = update_payload(result)
    payload['parameters']['score_valor_inicial'] = 999
    assert client.put('/api/platform/provision/config', headers=headers, json=payload).status_code == 200

    async def inspect():
        async with factory() as db:
            job = await db.get(ProvisionJob, job_id)
            snapshot = decode_payload(job.payload)
            assert snapshot['config_version'] == 2
            assert snapshot['parameters']['score_valor_inicial'] == 742
            assert snapshot['parameters']['nome_fantasia'] == 'Nome salvo'
            assert snapshot['apis'][0]['value1'] == 'private-value'
    asyncio.run(inspect())


@pytest.mark.parametrize('token,expected', [('replacement', True), ('', False), (None, True)])
def test_token_replace_clear_keep(panel, token, expected):
    client, _ = panel
    headers = authenticate(client)
    payload = update_payload(client.get('/api/platform/provision/config', headers=headers).json())
    payload['parameters']['token_api_whatsapp'] = token
    result = client.put('/api/platform/provision/config', headers=headers, json=payload)
    assert result.status_code == 200, result.text
    assert result.json()['has_token'] is expected
    assert result.json()['parameters']['token_api_whatsapp'] is None


@pytest.mark.parametrize('change', ['extra', 'duplicate', 'length', 'resource'])
def test_invalid_config_rejected_without_overwriting(panel, change):
    client, _ = panel
    headers = authenticate(client)
    payload = update_payload(client.get('/api/platform/provision/config', headers=headers).json())
    if change == 'extra':
        payload['parameters']['whatsapp_cobranca_automatica'] = True
    elif change == 'duplicate':
        payload['profiles'] *= 2
    elif change == 'length':
        payload['apis'][0]['url'] = 'a' * 256
    else:
        payload['profiles'][0]['permissions'] = [{'resource_key': 'unknown'}]
    assert client.put('/api/platform/provision/config', headers=headers, json=payload).status_code == 422
    assert client.get('/api/platform/provision/config', headers=headers).json()['version'] == 1
