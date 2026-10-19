"""Stock migration and real row-lock concurrency against an isolated temporary cluster."""
import asyncio
import os
from pathlib import Path
import secrets
import socket
import subprocess
import tempfile
from types import SimpleNamespace
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from sqlalchemy import create_engine, select, func, text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import ROOT_DIR
from app.models.product import Produto
from app.models.stock import MovimentoEstoque
from app.models.contract_commodato import ContratoComodato
from app.schemas.stock import StockWrite
from app.services.stock_service import StockService

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_INTEGRATION") != "1", reason="Temporary PostgreSQL integration is opt-in")


def test_stock_migration_and_concurrent_sales():
    with tempfile.TemporaryDirectory(prefix="tenant-pg-stock-") as directory:
        root = Path(directory)
        pg_bin = Path(os.environ["POSTGRES_BIN"])
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        password = secrets.token_urlsafe(24)
        password_file = root / "password"
        password_file.write_text(password, encoding="utf-8")
        cluster = root / "cluster"
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

        def run(args):
            with tempfile.TemporaryFile(mode="w+t") as output:
                result = subprocess.run([str(arg) for arg in args], stdout=output, stderr=output, text=True, timeout=60, creationflags=flags)
                output.seek(0)
                assert result.returncode == 0, output.read()

        url = URL.create("postgresql+psycopg2", username="stock_test", password=password, host="127.0.0.1", port=port, database="postgres")
        run([pg_bin / "initdb", "-D", cluster, "-U", "stock_test", "--auth=scram-sha-256", "--pwfile", password_file, "--encoding=UTF8", "--no-locale"])
        try:
            run([pg_bin / "pg_ctl", "-D", cluster, "-l", root / "postgres.log", "-o", f"-h 127.0.0.1 -p {port}", "-w", "start"])
            config = Config(str(ROOT_DIR / "alembic.ini"))
            config.set_main_option("script_location", str(ROOT_DIR / "alembic"))
            config.attributes["database_url"] = url.render_as_string(hide_password=False)
            command.upgrade(config, "20261015_0050")
            engine = create_engine(url)
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO produtos (produto_id, descricao, estoque) VALUES (1, 'Última unidade', 1), (2, 'Legado', 7)"))
                conn.execute(text("INSERT INTO contratos (contratos_id, contrato_status) VALUES (1, 1), (2, 1), (3, 1)"))
                conn.execute(text("INSERT INTO contratos_comodatos (comodato_id, contrato_id) VALUES (3, 3)"))
                conn.execute(text("INSERT INTO contratos_comodato_itens (comodato_id, produto_id, descricao_produto, quantidade) VALUES (3, 2, 'Legado', 2)"))
            command.upgrade(config, "head")
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO contratos_comodatos (comodato_id, contrato_id) VALUES (1, 1), (2, 2)"))
                conn.execute(text("INSERT INTO contratos_comodato_itens (comodato_id, produto_id, descricao_produto, quantidade) VALUES (1, 1, 'Última unidade', 1), (2, 1, 'Última unidade', 1)"))
            engine.dispose()

            async def scenario():
                engine = create_async_engine(url.set(drivername="postgresql+asyncpg"))
                factory = async_sessionmaker(engine, expire_on_commit=False)
                user = SimpleNamespace(id=None, nome="Teste concorrente")
                try:
                    async def sell(contract_id):
                        async with factory() as session:
                            try:
                                await StockService(session).confirm_sale(contract_id, 0, user)
                                return contract_id
                            except HTTPException as exc:
                                assert exc.status_code == 409
                                return None

                    results = await asyncio.gather(sell(1), sell(2))
                    winners = [r for r in results if r]
                    assert len(winners) == 1
                    # Both retries must see the already-confirmed sale after locking the contract.
                    await asyncio.gather(sell(winners[0]), sell(winners[0]))
                    async with factory() as session:
                        product = await session.get(Produto, 1)
                        assert product.estoque_novos == 0
                        assert await session.scalar(select(func.count()).select_from(MovimentoEstoque).where(MovimentoEstoque.tipo == "venda")) == 1
                        legacy = await session.get(Produto, 2)
                        assert legacy.estoque_novos == 7
                        legacy_contract = await session.get(ContratoComodato, 3)
                        assert legacy_contract.venda_confirmada and legacy_contract.estoque_legado
                    payload = StockWrite(operacao_id=uuid4(), tipo="entrada", condicao="usado", quantidade=2, motivo="Compra", observacao="Teste simultâneo")

                    async def receive():
                        async with factory() as session:
                            return await StockService(session).move(1, payload, user)
                    receipts = await asyncio.gather(receive(), receive())
                    assert receipts[0].movimento_id == receipts[1].movimento_id
                    async with factory() as session:
                        product = await session.get(Produto, 1)
                        assert product.estoque_usados == 2 and product.estoque == 2
                finally:
                    await engine.dispose()
            asyncio.run(scenario())
        finally:
            if (cluster / "postmaster.pid").exists():
                run([pg_bin / "pg_ctl", "-D", cluster, "-m", "fast", "-w", "stop"])
