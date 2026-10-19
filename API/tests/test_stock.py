import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # Register all referenced tables.
from app.db.base import Base
from app.models.contract import Contrato
from app.models.contract_commodato import ContratoComodato, ContratoComodatoItem
from app.models.product import Produto
from app.models.stock import MovimentoEstoque
from app.schemas.stock import StockWrite
from app.schemas.product import ProductUpdate
from app.schemas.contract_commodato import ContractComodatoWrite, ContractComodatoItemWrite
from app.services.stock_service import StockService
from app.services.product_service import ProductService
from app.services.contract_service import ContractService

USER = SimpleNamespace(id=None, nome="Operador de teste")


@asynccontextmanager
async def database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as session:
            session.add(Produto(produto_id=1, descricao="Produto teste", estoque=0))
            session.add_all([Contrato(contratos_id=i, contrato_status=1) for i in (1, 2)])
            await session.commit()
            yield session
    finally:
        await engine.dispose()


def operation(kind="entrada", quantity=5, condition="novo", **kwargs):
    reasons = {"entrada": "Compra", "baixa": "Quebra", "ajuste": "Inventário", "devolucao": "Devolução de cliente"}
    return StockWrite(operacao_id=uuid4(), tipo=kind, quantidade=quantity, condicao=condition,
                      motivo=reasons[kind], observacao="Conferência de teste", **kwargs)


async def sale(session, quantity, contract_id=1, condition="novo"):
    service = ContractService(session)
    result = await service.save_contract_commodato(contract_id, ContractComodatoWrite(items=[ContractComodatoItemWrite(produto_id=1, quantidade=quantity, condicao=condition)]))
    await StockService(session).confirm_sale(contract_id, result.versao, USER)
    return (await service.get_contract_commodato(contract_id)).items[0].item_id


def test_movements_idempotency_adjustment_and_history():
    async def scenario():
        async with database() as session:
            service = StockService(session)
            request = operation()
            first = await service.move(1, request, USER)
            repeated = await service.move(1, request, USER)
            assert first.movimento_id == repeated.movimento_id
            with pytest.raises(HTTPException) as exc:
                await service.move(1, request.model_copy(update={"quantidade": 6}), USER)
            assert exc.value.status_code == 409
            await service.move(1, operation(quantity=3, condition="usado"), USER)
            await service.move(1, operation("baixa", 2), USER)
            product = await service.lock_product(1)
            assert (product.estoque_novos, product.estoque_usados, product.estoque) == (3, 3, 6)
            version = product.estoque_versao
            await session.rollback()
            await service.move(1, operation("ajuste", 1, versao_esperada=version), USER)
            with pytest.raises(HTTPException) as exc:
                await service.move(1, operation("ajuste", 0, versao_esperada=version), USER)
            assert exc.value.status_code == 409
            history = await service.history(1, 1, 2)
            assert history.total == 4 and len(history.items) == 2
            assert history.items[0].quantidade == -2
            totals = dict((await session.execute(select(MovimentoEstoque.condicao, func.sum(MovimentoEstoque.quantidade)).group_by(MovimentoEstoque.condicao))).all())
            product = await service.lock_product(1)
            assert totals == {"novo": product.estoque_novos, "usado": product.estoque_usados}
    asyncio.run(scenario())


def test_sale_negative_flag_return_limits_and_no_second_outgoing():
    async def scenario():
        async with database() as session:
            service = StockService(session)
            await service.move(1, operation(quantity=2), USER)
            with pytest.raises(HTTPException) as exc:
                await sale(session, 3)
            assert exc.value.status_code == 409
            product = await service.lock_product(1)
            assert product.estoque == 2
            product.permite_vender_sem_estoque = True
            await session.commit()
            draft = await ContractService(session).get_contract_commodato(1)
            await service.confirm_sale(1, draft.versao, USER)
            await service.confirm_sale(1, draft.versao, USER)
            item = (await ContractService(session).get_contract_commodato(1)).items[0]
            product = await service.lock_product(1)
            assert product.estoque_novos == -1
            with pytest.raises(HTTPException):
                await service.move(1, operation("baixa", 1), USER)
            request = operation("devolucao", 2, "usado", item_id=item.item_id)
            await service.move(1, request, USER)
            await service.move(1, request, USER)
            with pytest.raises(HTTPException):
                await service.move(1, operation("devolucao", 2, "usado", item_id=item.item_id), USER)
            product = await service.lock_product(1)
            assert (product.estoque_novos, product.estoque_usados, product.estoque) == (-1, 2, 1)
            assert await session.scalar(select(func.count()).select_from(MovimentoEstoque).where(MovimentoEstoque.tipo == "venda")) == 1
            for action in (ContractService(session).delete_contract_commodato, ContractService(session).delete_contract):
                with pytest.raises(HTTPException):
                    await action(1)
                await session.rollback()
            with pytest.raises(HTTPException):
                await ProductService(session).update_product(1, ProductUpdate(estoque=100))
    asyncio.run(scenario())


def test_sale_atomic_when_later_item_has_insufficient_stock():
    async def scenario():
        async with database() as session:
            service = StockService(session)
            await service.move(1, operation(quantity=2), USER)
            draft = await ContractService(session).save_contract_commodato(1, ContractComodatoWrite(items=[
                ContractComodatoItemWrite(produto_id=1, quantidade=1, condicao="novo"),
                ContractComodatoItemWrite(produto_id=1, quantidade=1, condicao="usado"),
            ]))
            with pytest.raises(HTTPException):
                await service.confirm_sale(1, draft.versao, USER)
            product = await service.lock_product(1)
            assert product.estoque_novos == 2
            assert await session.scalar(select(func.count()).select_from(MovimentoEstoque)) == 1
            assert not (await ContractService(session).get_contract_commodato(1)).venda_confirmada
            with pytest.raises(HTTPException):
                await service.confirm_sale(1, draft.versao - 1, USER)
    asyncio.run(scenario())


@pytest.mark.parametrize("overrides", [
    {"quantidade": -1}, {"quantidade": 1.5}, {"quantidade": 0}, {"condicao": "quebrado"},
    {"motivo": "Inválido"}, {"tipo": "venda"}, {"observacao": " "},
    {"tipo": "ajuste", "motivo": "Inventário"},
    {"tipo": "devolucao", "motivo": "Devolução de cliente"},
])
def test_reject_invalid_stock_requests(overrides):
    data = operation().model_dump()
    data.update(overrides)
    with pytest.raises(ValidationError):
        StockWrite.model_validate(data)
