"""Carteira SQLite transportada como arquivo; nunca exporta o cadastro inteiro."""
import hashlib
import os
import sqlite3
import tempfile
import time
import zipfile
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select

from app.models.accounts_receivable import ContaReceber
from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.contract_commodato import ContratoComodato
from app.models.location import Bairro, Cidade

TTL_SECONDS = 24 * 60 * 60
MAX_ROWS = 200_000


def wallet_query(user_id: int):
    balance = func.coalesce(ContaReceber.valor_total, 0) - func.coalesce(ContaReceber.valor_recebido, 0)
    return select(
        Cliente.clientes_id.label('cliente_id'), Cliente.nome, Cliente.endereco,
        Cliente.nro, Cliente.complemento, Cliente.uf, Cliente.telefone,
        Cliente.celular01, Cliente.latitude, Cliente.longitude, Cliente.turno_cobranca,
        Bairro.bairro_nome.label('bairro'), Cidade.cidade,
        Contrato.contratos_id.label('contrato_id'), Contrato.obs,
        Contrato.contrato_status, Contrato.negociacao_id,
        ContratoComodato.comodato_id,
        ContaReceber.id.label('parcela_id'), ContaReceber.parcela_nro,
        ContaReceber.vencimentol.label('vencimento'),
        ContaReceber.valor_total, ContaReceber.valor_recebido,
    ).join(Contrato, Contrato.cliente_id == Cliente.clientes_id
    ).join(ContaReceber, ContaReceber.contratos_id == Contrato.contratos_id
    ).outerjoin(Bairro, Bairro.bairro_id == Cliente.bairro_id
    ).outerjoin(Cidade, Cidade.cidade_id == Cliente.cidade_id
    ).outerjoin(ContratoComodato, ContratoComodato.contrato_id == Contrato.contratos_id
    ).where(Cliente.usuario_id == user_id,
            ContaReceber.quitado.is_not(True), balance > 0
    ).order_by(Cliente.nome, Contrato.contratos_id, ContaReceber.vencimentol,
               ContaReceber.parcela_nro, ContaReceber.id).limit(MAX_ROWS + 1)


def money_units(value) -> int:
    # Preserva a precisão de quatro casas utilizada na API, sem REAL no SQLite.
    return int((Decimal(str(value or 0)) * 10000).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


class WalletArtifacts:
    def __init__(self, root: Path | None = None):
        self.root = root or Path(os.environ.get('MOBILE_WALLET_DIR',
                                                str(Path(tempfile.gettempdir()) / 'contratos-mobile-wallets')))

    def owner_dir(self, tenant: str, user_id: int) -> Path:
        key = hashlib.sha256(f'{tenant}:{user_id}'.encode()).hexdigest()
        return self.root / key

    def path(self, tenant: str, user_id: int, download_id: str) -> Path:
        from uuid import UUID
        try:
            canonical = str(UUID(download_id))
        except (ValueError, AttributeError):
            raise HTTPException(404, 'Carga nao encontrada')
        return self.owner_dir(tenant, user_id) / f'{canonical}.zip'

    def cleanup(self) -> int:
        """Somente artefatos gerados por este serviço; invocável também pelo agendador."""
        removed = 0
        for candidate in self.root.glob('*/*.zip'):
            try:
                if candidate.stat().st_mtime < time.time() - TTL_SECONDS:
                    candidate.unlink(missing_ok=True)
                    removed += 1
            except FileNotFoundError:
                pass
        return removed

    def get(self, tenant: str, user_id: int, download_id: str) -> Path:
        target = self.path(tenant, user_id, download_id)
        if not target.is_file() or target.stat().st_mtime < time.time() - TTL_SECONDS:
            raise HTTPException(404, 'Carga expirada ou nao encontrada. Gere uma nova carteira.')
        return target

    def acknowledge(self, tenant: str, user_id: int, download_id: str):
        self.path(tenant, user_id, download_id).unlink(missing_ok=True)

    def build(self, tenant: str, company: str, user, rows) -> dict:
        if len(rows) > MAX_ROWS:
            raise HTTPException(413, 'Carteira excede o limite de exportacao; contate o suporte.')
        self.cleanup()
        directory = self.owner_dir(tenant, user.id)
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        download_id = str(uuid4())
        target = self.path(tenant, user.id, download_id)
        created_at = datetime.now(timezone.utc).isoformat()
        with tempfile.TemporaryDirectory(prefix='wallet-', dir=directory) as temp:
            db_path = Path(temp) / 'carteira.sqlite'
            with closing(sqlite3.connect(db_path)) as db, db:
                db.executescript('''
                    PRAGMA user_version=1;
                    CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                    CREATE TABLE usuario (id INTEGER PRIMARY KEY, nome TEXT NOT NULL, login TEXT NOT NULL);
                    CREATE TABLE clientes (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, numero TEXT,
                      complemento TEXT, bairro TEXT, cidade TEXT, uf TEXT, telefone TEXT, celular TEXT,
                      latitude TEXT, longitude TEXT, turno_cobranca TEXT);
                    CREATE TABLE contratos (id INTEGER PRIMARY KEY, cliente_id INTEGER NOT NULL,
                      observacao TEXT, status INTEGER, negociacao_id INTEGER, comodato INTEGER NOT NULL);
                    CREATE TABLE parcelas (id INTEGER PRIMARY KEY, contrato_id INTEGER NOT NULL,
                      numero INTEGER, vencimento TEXT, total_units INTEGER NOT NULL,
                      recebido_units INTEGER NOT NULL, saldo_units INTEGER NOT NULL);
                    CREATE INDEX ix_contratos_cliente ON contratos(cliente_id);
                    CREATE INDEX ix_parcelas_contrato ON parcelas(contrato_id);
                ''')
                db.executemany('INSERT INTO metadata VALUES (?, ?)', {
                    'schema_version': '1', 'money_scale': '10000', 'tenant_id': tenant,
                    'company_code': company, 'user_id': str(user.id),
                    'download_id': download_id, 'created_at': created_at,
                }.items())
                db.execute('INSERT INTO usuario VALUES (?, ?, ?)', (user.id, user.nome, user.login))
                for row in rows:
                    db.execute('INSERT OR IGNORE INTO clientes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (
                        row['cliente_id'], row['nome'], row['endereco'], row['nro'], row['complemento'],
                        row['bairro'], row['cidade'], row['uf'], row['telefone'], row['celular01'],
                        row['latitude'], row['longitude'], row['turno_cobranca']))
                    db.execute('INSERT OR IGNORE INTO contratos VALUES (?,?,?,?,?,?)', (
                        row['contrato_id'], row['cliente_id'], row['obs'], row['contrato_status'],
                        row['negociacao_id'], int(row['comodato_id'] is not None)))
                    total, received = money_units(row['valor_total']), money_units(row['valor_recebido'])
                    due = row['vencimento'].isoformat() if row['vencimento'] else None
                    db.execute('INSERT INTO parcelas VALUES (?,?,?,?,?,?,?)', (
                        row['parcela_id'], row['contrato_id'], row['parcela_nro'], due,
                        total, received, max(total - received, 0)))
                counts = {name: db.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]
                          for name in ('clientes', 'contratos', 'parcelas')}
            # Fechar SQLite antes de compactar: sem WAL ou journal pendente.
            pending_zip = Path(temp) / 'carteira.zip'
            with zipfile.ZipFile(pending_zip, 'w', zipfile.ZIP_DEFLATED) as archive:
                archive.write(db_path, 'carteira.sqlite')
            with pending_zip.open('rb') as source:
                digest = hashlib.file_digest(source, 'sha256').hexdigest()
            size = pending_zip.stat().st_size
            sqlite_size = db_path.stat().st_size
            pending_zip.replace(target)
        return {'download_id': download_id, 'schema_version': 1, 'sha256': digest,
                'size_bytes': size, 'sqlite_size_bytes': sqlite_size, 'created_at': created_at,
                'expires_in_seconds': TTL_SECONDS, **counts}
