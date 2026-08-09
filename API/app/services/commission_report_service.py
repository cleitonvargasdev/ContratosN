from io import BytesIO

from fastapi import HTTPException, status
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Cliente
from app.models.commission import ComissaoLancamento, ComissaoLote
from app.models.contract import Contrato
from app.models.receipt import Recebimento
from app.models.user import User


class CommissionReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def generate_batch_pdf(self, lote_id: int) -> tuple[bytes, str]:
        header = await self.session.execute(
            select(ComissaoLote, User.nome)
            .join(User, User.id == ComissaoLote.funcionario_id)
            .where(ComissaoLote.lote_id == lote_id)
        )
        batch_row = header.one_or_none()
        if batch_row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Lote de comissoes nao encontrado.')
        batch, employee_name = batch_row
        rows = (await self.session.execute(
            select(ComissaoLancamento, Cliente.nome, Recebimento.parcela_nro)
            .outerjoin(Contrato, Contrato.contratos_id == ComissaoLancamento.contrato_id)
            .outerjoin(Cliente, Cliente.clientes_id == Contrato.cliente_id)
            .outerjoin(Recebimento, Recebimento.recebimento_id == ComissaoLancamento.recebimento_id)
            .where(ComissaoLancamento.lote_id == lote_id)
            .order_by(ComissaoLancamento.competencia.asc(), ComissaoLancamento.comissao_id.asc())
        )).all()
        return self._build_pdf(batch, employee_name, rows), f'lote-comissoes-{lote_id:05d}.pdf'

    def _build_pdf(self, batch: ComissaoLote, employee_name: str, rows: list[tuple[ComissaoLancamento, str | None, int | None]]) -> bytes:
        buffer = BytesIO()
        document = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=8 * mm, rightMargin=8 * mm, topMargin=9 * mm, bottomMargin=9 * mm)
        styles = getSampleStyleSheet()
        title = ParagraphStyle('commissionTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=15, leading=18, textColor=colors.HexColor('#24303b'))
        normal = ParagraphStyle('commissionNormal', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10)
        story = [Paragraph('Lista de Comissoes', title), Spacer(1, 3 * mm)]
        story.append(Paragraph(f'<b>Lote:</b> {batch.lote_id:05d} &nbsp;&nbsp; <b>Funcionario:</b> {employee_name} &nbsp;&nbsp; <b>Periodo:</b> {batch.data_inicial.strftime("%d/%m/%Y")} a {batch.data_final.strftime("%d/%m/%Y")}', normal))
        story.append(Spacer(1, 4 * mm))
        data = [['Data', 'Contrato', 'Parcela', 'Tipo', 'Cliente', 'Taxa %', 'Valor comissao']]
        total = 0.0
        for item, client_name, parcela_nro in rows:
            value = float(item.valor_comissao or 0)
            total += value
            data.append([
                item.competencia.strftime('%d/%m/%Y'),
                f'{int(item.contrato_id or 0):08d}' if item.contrato_id else '-',
                '-' if parcela_nro is None else str(parcela_nro),
                'Recebimento' if item.tipo == 'cobranca' else 'Venda',
                Paragraph(client_name or '-', normal),
                self._number(item.percentual),
                self._currency(value),
            ])
        data.append(['', '', '', '', Paragraph('<b>Total</b>', normal), '', self._currency(total)])
        table = Table(data, colWidths=[24*mm, 22*mm, 17*mm, 25*mm, 62*mm, 19*mm, 25*mm], repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#64748b')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -2), 0.25, colors.HexColor('#e2e8f0')),
            ('LINEABOVE', (0, -1), (-1, -1), 0.7, colors.HexColor('#94a3b8')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (5, 1), (6, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(table)
        document.build(story)
        return buffer.getvalue()

    @staticmethod
    def _number(value: float | None) -> str:
        return f'{float(value or 0):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    @classmethod
    def _currency(cls, value: float) -> str:
        return f'R$ {cls._number(value)}'
