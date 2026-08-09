from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import String, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_active_user, require_permission
from app.db.session import get_db_session
from app.models.commission import ComissaoLancamento, ComissaoLote
from app.models.contract import Contrato
from app.models.client import Cliente
from app.models.parameter import Parametro
from app.models.receipt import Recebimento
from app.models.accounts_payable import ContaPagar, ContaPagarParcela
from app.models.user import User
from app.schemas.commission import CommissionCloseRequest, CommissionRead, CommissionReprocessRequest
from app.services.commission_report_service import CommissionReportService

router = APIRouter(dependencies=[Depends(get_current_active_user)])

def read(item: ComissaoLancamento, nome: str) -> CommissionRead:
    return CommissionRead(**{key: getattr(item, key) for key in CommissionRead.model_fields if key != "funcionario_nome"}, funcionario_nome=nome)

@router.get('/comissoes/lotes')
async def list_batches(funcionario_id: int | None = None, ano_mes: str | None = None, situacao: int | None = None, pago: bool | None = None, session: AsyncSession = Depends(get_db_session), _: User = Depends(require_permission('contas_pagar','read'))):
    stmt=select(ComissaoLote, User.nome).join(User, User.id == ComissaoLote.funcionario_id)
    if funcionario_id: stmt=stmt.where(ComissaoLote.funcionario_id==funcionario_id)
    if ano_mes: stmt=stmt.where(ComissaoLote.data_final.cast(String).like(f'{ano_mes}%'))
    if situacao in (1, 2, 3): stmt=stmt.where(ComissaoLote.situacao==situacao)
    if pago is True: stmt=stmt.where(ComissaoLote.situacao==3)
    if pago is False: stmt=stmt.where(ComissaoLote.situacao.in_([1,2]))
    rows=(await session.execute(stmt.order_by(ComissaoLote.lote_id.desc()))).all()
    return [{'lote_id':x.lote_id,'data_lote':x.criado_em.date(),'funcionario_id':x.funcionario_id,'funcionario_nome':n,'data_inicial':x.data_inicial,'data_final':x.data_final,'situacao':x.situacao,'conta_pagar_id':x.conta_pagar_id,'valor_lote':float((await session.scalar(select(func.coalesce(func.sum(ComissaoLancamento.valor_comissao),0)).where(ComissaoLancamento.lote_id==x.lote_id))) or 0)} for x,n in rows]

@router.delete('/comissoes/lotes/{lote_id}', status_code=204)
async def delete_batch(lote_id: int, session: AsyncSession = Depends(get_db_session), _: User = Depends(require_permission('contas_pagar','delete'))):
    lote = await session.get(ComissaoLote, lote_id)
    if lote is None:
        raise HTTPException(404, 'Lote de comissoes nao encontrado.')
    if lote.situacao == 3:
        raise HTTPException(400, 'Nao e possivel excluir um lote de comissoes ja pago.')
    account = await session.get(ContaPagar, lote.conta_pagar_id) if lote.conta_pagar_id else None
    if account is not None and (account.quitado or any(parcela.pagamentos for parcela in account.parcelas)):
        raise HTTPException(400, 'Nao e possivel excluir um lote cuja conta a pagar tenha pagamentos.')
    items = (await session.execute(select(ComissaoLancamento).where(ComissaoLancamento.lote_id == lote_id))).scalars().all()
    for item in items:
        item.lote_id = None
        item.conta_pagar_id = None
        item.situacao = 'pendente'
    if account is not None:
        await session.delete(account)
    await session.delete(lote)
    await session.commit()

@router.get('/comissoes/lotes/{lote_id}/imprimir')
async def print_batch(lote_id: int, session: AsyncSession = Depends(get_db_session), _: User = Depends(require_permission('contas_pagar','read'))):
    pdf_bytes, filename = await CommissionReportService(session).generate_batch_pdf(lote_id)
    return Response(content=pdf_bytes, media_type='application/pdf', headers={'Content-Disposition': f'inline; filename="{filename}"'})

@router.get('/comissoes', response_model=list[CommissionRead])
async def list_commissions(funcionario_id: int, data_final: date | None = None, session: AsyncSession = Depends(get_db_session), _: User = Depends(require_permission('contas_pagar','read'))):
    stmt=select(ComissaoLancamento, User.nome).join(User, User.id == ComissaoLancamento.funcionario_id)
    stmt=stmt.where(ComissaoLancamento.funcionario_id == funcionario_id)
    if data_final: stmt=stmt.where(ComissaoLancamento.competencia <= data_final)
    rows = (await session.execute(stmt.order_by(ComissaoLancamento.competencia.desc()))).all()
    return [read(item, nome) for item, nome in rows]

@router.get('/comissoes/previa', response_model=list[CommissionRead])
async def preview_commissions(funcionario_id: int, data_final: date, todos_carteira: bool = False, session: AsyncSession = Depends(get_db_session), _: User = Depends(require_permission('contas_pagar','read'))):
    user = await session.get(User, funcionario_id)
    if user is None: return []
    parameter = (await session.execute(select(Parametro).limit(1))).scalar_one_or_none()
    existing_rows = (await session.execute(
        select(ComissaoLancamento.contrato_id, ComissaoLancamento.recebimento_id).where(
            ComissaoLancamento.lote_id.is_not(None),
        )
    )).all()
    existing = {(contract_id, receipt_id) for contract_id, receipt_id in existing_rows}
    output = []
    for contract in (await session.execute(select(Contrato))).scalars().all():
        if contract.pagar_comissao_venda and contract.usuario_id_vendedor == funcionario_id and user.recebe_comissao_venda and (not parameter or not parameter.comissao_apos_quitacao_venda or contract.quitado) and (contract.contratos_id, None) not in existing:
            base=float(contract.valor_empretismo or 0); pct=float(user.taxa_venda or 0)
            output.append(CommissionRead(comissao_id=-contract.contratos_id,tipo='venda',situacao='pendente',funcionario_id=funcionario_id,funcionario_nome=user.nome,contrato_id=contract.contratos_id,recebimento_id=None,competencia=data_final,base_calculo=base,percentual=pct,valor_comissao=round(base*pct/100,4),conta_pagar_id=None,motivo=None))
        if not contract.pagar_comissao_cobranca or (parameter and parameter.comissao_apos_quitacao_cobranca and not contract.quitado): continue
        client=await session.get(Cliente, contract.cliente_id) if contract.cliente_id else None
        receipt_stmt = select(Recebimento).where(Recebimento.contrato_id == contract.contratos_id)
        if not todos_carteira:
            receipt_stmt = receipt_stmt.where(Recebimento.usuario_id == funcionario_id)
        for receipt in (await session.execute(receipt_stmt)).scalars().all():
            belongs_to_portfolio = bool(client and client.usuario_id == funcionario_id)
            if receipt.usuario_id != funcionario_id and not (todos_carteira and belongs_to_portfolio):
                continue
            if receipt.data_recebimento and receipt.data_recebimento.date()<=data_final and user.recebe_comissao_cob and (contract.contratos_id, receipt.recebimento_id) not in existing:
                base=float(receipt.valor_recebido or 0); pct=float(client.percent_comissao if client and client.comissao_diferente else user.taxa_cob or 0)
                output.append(CommissionRead(comissao_id=-(100000000+receipt.recebimento_id),tipo='cobranca',situacao='pendente',funcionario_id=funcionario_id,funcionario_nome=user.nome,contrato_id=contract.contratos_id,recebimento_id=receipt.recebimento_id,parcela_nro=receipt.parcela_nro,competencia=receipt.data_recebimento.date(),base_calculo=base,percentual=pct,valor_comissao=round(base*pct/100,4),conta_pagar_id=None,motivo=None))
    return output

@router.post('/comissoes/reprocessar')
async def reprocess_commissions(payload: CommissionReprocessRequest, session: AsyncSession = Depends(get_db_session), _: User = Depends(require_permission('contas_pagar','create'))):
    if not payload.funcionario_id: raise HTTPException(400, 'Informe o funcionário.')
    contracts = (await session.execute(select(Contrato).where(Contrato.contratos_id == payload.contrato_id) if payload.contrato_id else select(Contrato))).scalars().all()
    parameter = (await session.execute(select(Parametro).limit(1))).scalar_one_or_none()
    generated = 0
    for contract in contracts:
        client = await session.get(Cliente, contract.cliente_id) if contract.cliente_id else None
        if contract.pagar_comissao_venda and contract.usuario_id_vendedor:
            user = await session.get(User, contract.usuario_id_vendedor)
            eligible = not (parameter and parameter.comissao_apos_quitacao_venda) or bool(contract.quitado)
            existing_sale = await session.scalar(select(ComissaoLancamento).where(ComissaoLancamento.tipo=='venda', ComissaoLancamento.contrato_id==contract.contratos_id))
            if user and user.id == payload.funcionario_id and user.recebe_comissao_venda and eligible and (existing_sale is None or (existing_sale.situacao == 'pendente' and existing_sale.lote_id is None)):
                pct=float(user.taxa_venda or 0); base=float(contract.valor_empretismo or 0)
                if existing_sale is None:
                    session.add(ComissaoLancamento(tipo='venda', funcionario_id=user.id, contrato_id=contract.contratos_id, competencia=date.today(), base_calculo=base, percentual=pct, valor_comissao=round(base*pct/100,4)))
                else:
                    existing_sale.funcionario_id=user.id; existing_sale.base_calculo=base; existing_sale.percentual=pct; existing_sale.valor_comissao=round(base*pct/100,4)
                generated += 1
        if contract.pagar_comissao_cobranca:
            receipts=(await session.execute(select(Recebimento).where(Recebimento.contrato_id==contract.contratos_id))).scalars().all()
            eligible = not (parameter and parameter.comissao_apos_quitacao_cobranca) or bool(contract.quitado)
            for receipt in receipts:
                employee = await session.get(User, payload.funcionario_id)
                belongs_to_portfolio = bool(client and client.usuario_id == payload.funcionario_id)
                existing_receipt=await session.scalar(select(ComissaoLancamento).where(ComissaoLancamento.tipo=='cobranca', ComissaoLancamento.recebimento_id==receipt.recebimento_id))
                can_receive = receipt.usuario_id == payload.funcionario_id or (payload.todos_carteira and belongs_to_portfolio)
                if employee and can_receive and employee.recebe_comissao_cob and eligible and (existing_receipt is None or (existing_receipt.situacao == 'pendente' and existing_receipt.lote_id is None)):
                    pct=float(client.percent_comissao if client and client.comissao_diferente else employee.taxa_cob or 0); base=float(receipt.valor_recebido or 0)
                    if existing_receipt is None:
                        session.add(ComissaoLancamento(tipo='cobranca', funcionario_id=employee.id, contrato_id=contract.contratos_id, recebimento_id=receipt.recebimento_id, competencia=(receipt.data_recebimento or date.today()).date() if hasattr(receipt.data_recebimento,'date') else date.today(), base_calculo=base, percentual=pct, valor_comissao=round(base*pct/100,4)))
                    else:
                        existing_receipt.funcionario_id=employee.id; existing_receipt.base_calculo=base; existing_receipt.percentual=pct; existing_receipt.valor_comissao=round(base*pct/100,4)
                    generated += 1
    await session.flush()
    pending = (await session.execute(select(ComissaoLancamento).where(ComissaoLancamento.funcionario_id == payload.funcionario_id, ComissaoLancamento.situacao == 'pendente', ComissaoLancamento.lote_id.is_(None), ComissaoLancamento.competencia <= (payload.data_final or date.today())))).scalars().all()
    if not pending:
        await session.commit()
        return {'geradas': generated, 'lote_id': None}
    lote = ComissaoLote(funcionario_id=payload.funcionario_id, data_inicial=min(x.competencia for x in pending), data_final=payload.data_final or date.today(), situacao=1)
    session.add(lote); await session.flush()
    total = round(sum(float(item.valor_comissao or 0) for item in pending), 4)
    employee = await session.get(User, payload.funcionario_id)
    final_date = payload.data_final or date.today()
    observation = f'Lote nº {lote.lote_id:05d} de Comissões do Funcionário {employee.nome if employee else payload.funcionario_id}, no período avaliado entre {lote.data_inicial.strftime("%d/%m/%Y")} e {final_date.strftime("%d/%m/%Y")}.'
    account = ContaPagar(descricao=f'Comissões - lote {lote.lote_id}', tipo_pessoa='funcionario', usuario_id=payload.funcionario_id, valor_total=total, valor_pago=0, saldo_pagar=total, quitado=False, observacao=observation, parcelas=[ContaPagarParcela(numero_parcela=1, descricao='Parcela de Comissões', vencimento=final_date, valor_original=total, valor_total=total, valor_pago=0, saldo_pagar=total, quitado=False)])
    session.add(account); await session.flush()
    lote.conta_pagar_id = account.conta_pagar_id
    lote.situacao = 2
    for item in pending:
        item.lote_id=lote.lote_id
        item.conta_pagar_id=account.conta_pagar_id
        item.situacao='em_lote'
    await session.commit()
    return {'geradas': generated, 'lote_id': lote.lote_id}

@router.post('/comissoes/fechar')
async def close_commissions(payload: CommissionCloseRequest, session: AsyncSession = Depends(get_db_session), current: User = Depends(require_permission('contas_pagar','create'))):
    if not payload.comissao_ids: raise HTTPException(400, 'Selecione ao menos uma comissão.')
    items=(await session.execute(select(ComissaoLancamento).where(ComissaoLancamento.comissao_id.in_(payload.comissao_ids), ComissaoLancamento.situacao=='pendente'))).scalars().all()
    if not items: raise HTTPException(400, 'Não há comissões pendentes selecionadas.')
    users={item.funcionario_id for item in items}
    if len(users)!=1: raise HTTPException(400, 'Feche comissões de apenas um funcionário por vez.')
    total=round(sum(float(item.valor_comissao) for item in items),4)
    account=ContaPagar(descricao='Comissões', tipo_pessoa='funcionario', usuario_id=next(iter(users)), valor_total=total, valor_pago=0, saldo_pagar=total, quitado=False, usuario_lancamento_id=current.id, parcelas=[ContaPagarParcela(numero_parcela=1, vencimento=payload.vencimento, valor_original=total, valor_total=total, valor_pago=0, saldo_pagar=total, quitado=False)])
    session.add(account); await session.flush()
    for item in items: item.situacao='em_lote'; item.conta_pagar_id=account.conta_pagar_id
    await session.commit()
    return {'conta_pagar_id': account.conta_pagar_id, 'total': total}
