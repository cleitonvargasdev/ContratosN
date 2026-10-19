import hashlib
import sqlite3
import zipfile
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine

from app.services.mobile_wallet_service import WalletArtifacts, money_units, wallet_query


def test_query_filters_collector_and_open_balance():
    engine = create_engine('sqlite://')
    with engine.begin() as db:
        db.exec_driver_sql('CREATE TABLE clientes (clientes_id INT, nome TEXT, endereco TEXT, nro TEXT, complemento TEXT, uf TEXT, telefone TEXT, celular01 TEXT, latitude TEXT, longitude TEXT, turno_cobranca TEXT, bairro_id INT, cidade_id INT)')
        db.exec_driver_sql('CREATE TABLE contratos (contratos_id INT, cliente_id INT, obs TEXT, contrato_status INT, negociacao_id INT, usuario_id_vendedor INT)')
        db.exec_driver_sql('CREATE TABLE contas_receber (id INT, contratos_id INT, parcela_nro INT, vencimentol DATETIME, valor_total FLOAT, valor_recebido FLOAT, quitado BOOLEAN)')
        db.exec_driver_sql('CREATE TABLE bairros (bairro_id INT, bairro_nome TEXT)')
        db.exec_driver_sql('CREATE TABLE cidades (cidade_id INT, cidade TEXT)')
        db.exec_driver_sql('CREATE TABLE contratos_comodatos (contrato_id INT, comodato_id INT)')
        db.exec_driver_sql("INSERT INTO clientes (clientes_id, nome) VALUES (1,'Cliente'), (2,'Outro')")
        db.exec_driver_sql("INSERT INTO contratos VALUES (10,1,'Observação',1,NULL,7), (20,2,'Outro cobrador',1,NULL,8)")
        db.exec_driver_sql('''INSERT INTO contas_receber VALUES
            (1,10,1,'2026-11-01',100,0,0), (2,10,2,'2026-10-01',100,25,NULL),
            (3,10,3,'2026-10-01',100,100,1), (4,10,4,'2026-10-01',100,100,0),
            (5,20,1,'2026-10-01',100,0,0), (6,10,5,'2026-10-01',100,0,1)''')
        rows = db.execute(wallet_query(7)).mappings().all()
        assert {row['parcela_id'] for row in rows} == {1, 2}


def sample_row():
    return dict(cliente_id=1, nome='Cliente', endereco='Rua', nro='2', complemento=None,
                bairro='Centro', cidade='Cidade', uf='MS', telefone=None, celular01='123',
                latitude='-20', longitude='-54', turno_cobranca='INTEGRAL', contrato_id=10,
                obs='Comodato / negociação', contrato_status=1, negociacao_id=4, comodato_id=9,
                parcela_id=22, parcela_nro=2, vencimento=datetime(2026, 11, 1, tzinfo=timezone.utc),
                valor_total=1050, valor_recebido=800)


def test_zip_schema_observation_precision_ownership_and_ack(tmp_path):
    artifacts = WalletArtifacts(tmp_path)
    user = SimpleNamespace(id=7, nome='Cobrador', login='cobrador', senha_hash='never export')
    manifest = artifacts.build('tenant-cv', 'cv', user, [sample_row()])
    artifact = artifacts.get('tenant-cv', 7, manifest['download_id'])
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == manifest['sha256']
    for tenant, uid in [('tenant-bc', 7), ('tenant-cv', 8)]:
        with pytest.raises(HTTPException):
            artifacts.get(tenant, uid, manifest['download_id'])
        artifacts.acknowledge(tenant, uid, manifest['download_id'])
        assert artifact.exists()
    with zipfile.ZipFile(artifact) as archive:
        assert archive.namelist() == ['carteira.sqlite']
        archive.extract('carteira.sqlite', tmp_path)
    with sqlite3.connect(tmp_path / 'carteira.sqlite') as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert db.execute('SELECT saldo_units FROM parcelas').fetchone()[0] == 2500000
        assert db.execute('SELECT observacao, comodato FROM contratos').fetchone() == ('Comodato / negociação', 1)
        assert dict(db.execute('SELECT key,value FROM metadata'))['user_id'] == '7'
        assert [row[1] for row in db.execute('PRAGMA table_info(usuario)')] == ['id', 'nome', 'login']
    artifacts.acknowledge('tenant-cv', 7, manifest['download_id'])
    artifacts.acknowledge('tenant-cv', 7, manifest['download_id'])
    assert not artifact.exists()


def test_empty_wallet_and_precision(tmp_path):
    artifacts = WalletArtifacts(tmp_path)
    result = artifacts.build('cv', 'cv', SimpleNamespace(id=1, nome='A', login='a'), [])
    assert result['parcelas'] == result['clientes'] == result['contratos'] == 0
    assert money_units('12.3456') == 123456
    with pytest.raises(HTTPException):
        artifacts.get('cv', 1, '../../private')


def test_expiration(tmp_path):
    import os
    artifacts = WalletArtifacts(tmp_path)
    result = artifacts.build('cv', 'cv', SimpleNamespace(id=1, nome='A', login='a'), [])
    target = artifacts.get('cv', 1, result['download_id'])
    os.utime(target, (1, 1))
    with pytest.raises(HTTPException):
        artifacts.get('cv', 1, result['download_id'])
    assert artifacts.cleanup() == 1
    assert not target.exists()


def test_routes_require_active_authorized_user(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.controllers.mobile_wallet_controller import router
    from app.api.dependencies import get_current_user
    monkeypatch.setenv('MOBILE_WALLET_DIR', str(tmp_path))
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    url = '/carteira/11111111-1111-4111-8111-111111111111/arquivo'
    assert client.get(url).status_code == 401
    user = SimpleNamespace(id=7, ativo=False, permissions=[])
    app.dependency_overrides[get_current_user] = lambda: user
    assert client.get(url).status_code == 403
    user.ativo = True
    assert client.get(url).status_code == 403
