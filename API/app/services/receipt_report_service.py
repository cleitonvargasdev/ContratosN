from datetime import UTC, date, datetime, time, timedelta
from io import BytesIO

from fastapi import HTTPException
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.accounts_receivable import ContaReceber
from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.receipt import Recebimento
from app.models.user import User


class ReceiptReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def generate(self, start: date, end: date, user_id: int | None, client_id: int | None, portfolio: bool, mode: str) -> tuple[bytes, str]:
        if end < start:
            raise HTTPException(400, 'A data final deve ser igual ou posterior à inicial.')
        limit = 3 if mode == 'analitico' else 366
        if (end - start).days + 1 > limit:
            label = '3 dias' if mode == 'analitico' else '1 ano'
            raise HTTPException(400, f'O período máximo para relatório {mode} é de {label}.')
        if mode not in {'analitico', 'sintetico'}:
            raise HTTPException(400, 'Tipo de relatório inválido.')
        selected_user = await self.session.get(User, user_id) if user_id else None
        if user_id and selected_user is None:
            raise HTTPException(404, 'Cobrador não encontrado.')
        if client_id and await self.session.get(Cliente, client_id) is None:
            raise HTTPException(404, 'Cliente não encontrado.')
        rows = await self._rows(start, end, user_id, client_id, portfolio, selected_user.nome if selected_user else None)
        title = 'RELATÓRIO DE RECEBIMENTOS POR PERÍODO'
        employee = selected_user.nome if selected_user else 'TODOS OS FUNCIONÁRIOS'
        data = self._analytic(rows) if mode == 'analitico' else self._synthetic(rows)
        return self._pdf(title, start, end, employee, data, mode), f'recebimentos-{mode}-{start:%Y%m%d}-{end:%Y%m%d}.pdf'

    async def _rows(self, start: date, end: date, user_id: int | None, client_id: int | None, portfolio: bool, selected_name: str | None) -> list[dict]:
        receipt_user = aliased(User)
        portfolio_user = aliased(User)
        stmt = select(Recebimento, Contrato, Cliente, ContaReceber, receipt_user.nome, portfolio_user.nome).join(
            Contrato, Contrato.contratos_id == Recebimento.contrato_id
        ).outerjoin(Cliente, Cliente.clientes_id == Contrato.cliente_id).outerjoin(
            ContaReceber, and_(ContaReceber.contratos_id == Recebimento.contrato_id, ContaReceber.parcela_nro == Recebimento.parcela_nro)
        ).outerjoin(receipt_user, receipt_user.id == Recebimento.usuario_id).outerjoin(
            portfolio_user, portfolio_user.id == Cliente.usuario_id
        ).where(
            Recebimento.data_recebimento >= datetime.combine(start, time.min, UTC),
            Recebimento.data_recebimento < datetime.combine(end + timedelta(days=1), time.min, UTC),
        )
        if user_id:
            if portfolio:
                stmt = stmt.where((Recebimento.usuario_id == user_id) | (Cliente.usuario_id == user_id))
            else:
                stmt = stmt.where(Recebimento.usuario_id == user_id)
        if client_id:
            stmt = stmt.where(Contrato.cliente_id == client_id)
        result = []
        for receipt, contract, client, installment, receipt_name, portfolio_name in (await self.session.execute(stmt)).all():
            value = float(receipt.valor_recebido or 0)
            installment_value = float(installment.valor_total or 0) if installment else value
            result.append({
                'date': receipt.data_recebimento, 'contract': contract.contratos_id,
                'installment': receipt.parcela_nro, 'client': client.nome if client else 'Cliente removido',
                'collector': selected_name or (portfolio_name if portfolio and portfolio_name else receipt_name or 'Não informado'),
                'value': value, 'missing': max(installment_value - value, 0),
            })
        return sorted(result, key=lambda row: (row['date'] or datetime.min.replace(tzinfo=UTC), row['collector']))

    def _analytic(self, rows: list[dict]) -> list:
        data = [['Data', 'Contrato / Parcela', 'Cliente', 'Cobrador', 'Valor recebido', 'Faltou']]
        for row in rows:
            moment = row['date']
            when = moment.astimezone(UTC).strftime('%d/%m/%Y\n%H:%M') if moment else '-'
            data.append([when, f"{row['contract']}  {row['installment'] or '-'}", row['client'], row['collector'], self._money(row['value']), self._money(row['missing']) if row['missing'] else ''])
        total = sum(row['value'] for row in rows); missing = sum(row['missing'] for row in rows)
        data += [
            ['*** Valor total recebido no período:', '', '', '', '', self._money(total)],
            ['*** Valor da diferença das parcelas:', '', '', '', '', self._money(missing)],
        ]
        return data

    def _synthetic(self, rows: list[dict]) -> list:
        totals: dict[str, tuple[float, float]] = {}
        for row in rows:
            value, missing = totals.get(row['collector'], (0, 0))
            totals[row['collector']] = (value + row['value'], missing + row['missing'])
        data = [['Cobrador', 'Valor recebido', 'Diferença das parcelas']]
        for name, (value, missing) in sorted(totals.items()): data.append([name, self._money(value), self._money(missing)])
        data.append(['*** Total geral:', self._money(sum(x[0] for x in totals.values())), self._money(sum(x[1] for x in totals.values()))])
        return data

    def _pdf(self, title: str, start: date, end: date, employee: str, data: list, mode: str) -> bytes:
        output = BytesIO(); doc = SimpleDocTemplate(output, pagesize=A4, leftMargin=7*mm, rightMargin=7*mm, topMargin=8*mm, bottomMargin=8*mm)
        styles = getSampleStyleSheet(); normal = ParagraphStyle('receipt', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9)
        heading = ParagraphStyle('heading', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=14, leading=16)
        elements = [Paragraph(title, heading), Paragraph(f'Período: {start:%d/%m/%Y} até {end:%d/%m/%Y}', normal), Paragraph(f'Funcionário: <b>{employee}</b>', normal), Spacer(1, 4*mm)]
        widths = [22*mm, 28*mm, 70*mm, 33*mm, 25*mm, 22*mm] if mode == 'analitico' else [90*mm, 45*mm, 45*mm]
        table = Table([[Paragraph(str(cell).replace('\n', '<br/>'), normal) for cell in row] for row in data], colWidths=widths, repeatRows=1)
        styles_table = [('LINEBELOW',(0,0),(-1,0),.5,colors.black),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('ALIGN',(-2,1),(-1,-1),'RIGHT'),('LINEBELOW',(0,1),(-1,-3),.15,colors.grey),('FONTNAME',(0,-2),(-1,-1),'Helvetica-Bold'),('TEXTCOLOR',(-1,-1),(-1,-1),colors.red),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]
        if mode == 'analitico':
            styles_table += [('SPAN',(0,-2),(4,-2)), ('SPAN',(0,-1),(4,-1)), ('ALIGN',(0,-2),(4,-1),'RIGHT')]
        table.setStyle(TableStyle(styles_table))
        elements.append(table)
        generated_at = datetime.now()
        def page_header(canvas, document):
            canvas.saveState()
            canvas.setFont('Helvetica', 7)
            right = A4[0] - 7 * mm
            canvas.drawRightString(right, A4[1] - 6 * mm, generated_at.strftime('%d/%m/%Y'))
            canvas.drawRightString(right, A4[1] - 10 * mm, generated_at.strftime('%H:%M'))
            canvas.drawRightString(right, A4[1] - 14 * mm, f'N. Pág. {canvas.getPageNumber()}')
            canvas.restoreState()
        doc.build(elements, onFirstPage=page_header, onLaterPages=page_header)
        return output.getvalue()

    @staticmethod
    def _money(value: float) -> str:
        return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
