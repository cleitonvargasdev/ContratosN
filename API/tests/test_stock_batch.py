import asyncio
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy import select

from app.models.product import Produto
from app.schemas.stock import StockBatchItemWrite, StockBatchWrite
from app.services.stock_service import StockService
from tests.test_stock import database


def test_purchase_batch_updates_prices_and_is_atomic():
    async def scenario():
        async with database() as session:
            session.add(Produto(produto_id=2, descricao="Outro produto", estoque=0))
            await session.commit()
            data = StockBatchWrite(items=[
                StockBatchItemWrite(produto_id=1, operacao_id=uuid4(), quantidade=3, condicao="novo", valor_compra=12.5, valor_venda=19.9),
                StockBatchItemWrite(produto_id=2, operacao_id=uuid4(), quantidade=2, condicao="usado", valor_compra=8, valor_venda=15),
            ])
            result = await StockService(session).purchase_batch(data, SimpleNamespace(id=None, nome="Operador"))
            assert len(result.movements) == 2
            products = (await session.scalars(select(Produto).order_by(Produto.produto_id))).all()
            assert (products[0].estoque_novos, products[0].valor_compra, products[0].valor_venda) == (3, 12.5, 19.9)
            assert (products[1].estoque_usados, products[1].estoque) == (2, 2)
    asyncio.run(scenario())
