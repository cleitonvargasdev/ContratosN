import hashlib

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contract import Contrato
from app.models.contract_commodato import ContratoComodato, ContratoComodatoItem
from app.models.product import Produto
from app.models.stock import MovimentoEstoque
from app.models.user import User
from app.schemas.stock import StockHistory, StockMovementRead, StockWrite


class StockService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def lock_contract(self, contract_id: int):
        record = await self.session.scalar(select(Contrato).where(Contrato.contratos_id == contract_id).with_for_update().execution_options(populate_existing=True))
        if record is None:
            raise HTTPException(404, "Contrato não encontrado")
        return record

    async def lock_product(self, product_id: int):
        product = await self.session.scalar(select(Produto).where(Produto.produto_id == product_id).with_for_update().execution_options(populate_existing=True))
        if product is None:
            raise HTTPException(404, "Produto não encontrado")
        return product

    def record(self, product, *, condition, delta, kind, reason, note, key, signature, user, item_id=None):
        field = "estoque_novos" if condition == "novo" else "estoque_usados"
        before = getattr(product, field)
        after = before + delta
        if delta < 0 and kind in ("venda", "baixa") and after < 0:
            if kind != "venda" or not product.permite_vender_sem_estoque:
                raise HTTPException(409, f"Estoque insuficiente de {condition}: {product.descricao}. Saldo: {before}.")
        setattr(product, field, after)
        product.estoque = product.estoque_novos + product.estoque_usados
        product.estoque_versao += 1
        movement = MovimentoEstoque(
            produto_id=product.produto_id, item_id=item_id,
            usuario_id=user.id, usuario_nome=user.nome, tipo=kind, condicao=condition,
            quantidade=delta, saldo_antes=before, saldo_depois=after, motivo=reason,
            observacao=note, operacao_id=key, assinatura=signature,
        )
        self.session.add(movement)
        return movement

    async def move(self, product_id: int, payload: StockWrite, user: User):
        try:
            item = None
            if payload.item_id is not None:
                contract_id = await self.session.scalar(select(ContratoComodato.contrato_id).join(ContratoComodatoItem).where(ContratoComodatoItem.item_id == payload.item_id))
                if contract_id is None:
                    raise HTTPException(404, "Item da venda não encontrado")
                await self.lock_contract(contract_id)
                item = await self.session.get(ContratoComodatoItem, payload.item_id, populate_existing=True)
                if item is None:
                    raise HTTPException(409, "O item foi alterado. Reabra o comodato.")
                comodato = await self.session.get(ContratoComodato, item.comodato_id, populate_existing=True)
                if item.produto_id != product_id or not comodato.venda_confirmada:
                    raise HTTPException(409, "A devolução exige um item deste produto em uma venda confirmada")
            product = await self.lock_product(product_id)
            signature = hashlib.sha256(payload.model_dump_json().encode()).hexdigest()
            previous = await self.session.scalar(select(MovimentoEstoque).where(MovimentoEstoque.produto_id == product_id, MovimentoEstoque.operacao_id == str(payload.operacao_id)))
            if previous:
                if previous.assinatura != signature:
                    raise HTTPException(409, "Esta operação já foi utilizada com outros dados")
                result = StockMovementRead.model_validate(previous)
                await self.session.rollback()
                return result
            balance = product.estoque_novos if payload.condicao == "novo" else product.estoque_usados
            if payload.tipo == "ajuste":
                if product.estoque_versao != payload.versao_esperada:
                    raise HTTPException(409, "O estoque mudou durante a conferência. Atualize os saldos e confira novamente.")
                delta = payload.quantidade - balance
            else:
                delta = -payload.quantidade if payload.tipo == "baixa" else payload.quantidade
            if item is not None:
                if payload.quantidade > item.quantidade - item.quantidade_devolvida:
                    raise HTTPException(409, "Quantidade superior ao saldo pendente de devolução")
                item.quantidade_devolvida += payload.quantidade
            movement = self.record(product, condition=payload.condicao, delta=delta, kind=payload.tipo,
                                   reason=payload.motivo, note=payload.observacao, key=str(payload.operacao_id),
                                   signature=signature, user=user, item_id=payload.item_id)
            await self.session.flush()
            result = StockMovementRead.model_validate(movement)
            await self.session.commit()
            return result
        except Exception:
            await self.session.rollback()
            raise

    async def confirm_sale(self, contract_id: int, version: int, user: User):
        try:
            await self.lock_contract(contract_id)
            comodato = await self.session.scalar(select(ContratoComodato).where(ContratoComodato.contrato_id == contract_id).execution_options(populate_existing=True))
            if comodato is None or not comodato.items:
                raise HTTPException(409, "Salve os produtos do comodato antes de confirmar a venda")
            if comodato.venda_confirmada:
                await self.session.rollback()
                return
            if comodato.versao != version:
                raise HTTPException(409, "Os itens foram alterados. Reabra o comodato e confira antes de confirmar.")
            products = {}
            for product_id in sorted({item.produto_id for item in comodato.items}):
                products[product_id] = await self.lock_product(product_id)
            for item in comodato.items:
                product = products[item.produto_id]
                if not product.ativo:
                    raise HTTPException(409, f"Produto inativo: {product.descricao}")
                self.record(product, condition=item.condicao, delta=-item.quantidade, kind="venda",
                            reason="Venda", note=f"Venda do contrato {contract_id}",
                            key=f"venda-item-{item.item_id}", signature="venda", user=user, item_id=item.item_id)
            comodato.venda_confirmada = True
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def history(self, product_id: int, page: int, page_size: int):
        query = select(MovimentoEstoque).where(MovimentoEstoque.produto_id == product_id)
        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))
        rows = (await self.session.scalars(query.order_by(MovimentoEstoque.movimento_id.desc()).offset((page - 1) * page_size).limit(page_size))).all()
        return StockHistory(items=[StockMovementRead.model_validate(row) for row in rows], total=total, page=page, page_size=page_size)
