from datetime import UTC, date, datetime, time, timedelta
from io import BytesIO
from urllib.parse import quote

from fastapi import HTTPException
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.mobile_batch import MobileOccurrence
from app.models.user import User


class OccurrenceReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def generate(self, start: date, end: date, collector_id: int | None) -> tuple[bytes, str]:
        if end < start or (end - start).days + 1 > 366:
            raise HTTPException(400, 'Informe um período de até 1 ano.')
        stmt = select(MobileOccurrence, Contrato, Cliente, User.nome).outerjoin(
            Contrato, Contrato.contratos_id == MobileOccurrence.contract_id
        ).outerjoin(Cliente, Cliente.clientes_id == MobileOccurrence.client_id).join(
            User, User.id == MobileOccurrence.user_id
        ).where(
            MobileOccurrence.created_at >= datetime.combine(start, time.min, UTC),
            MobileOccurrence.created_at < datetime.combine(end + timedelta(days=1), time.min, UTC),
        )
        if collector_id:
            stmt = stmt.where(MobileOccurrence.user_id == collector_id)
        rows = (await self.session.execute(stmt.order_by(MobileOccurrence.created_at, User.nome))).all()
        return self._pdf(start, end, rows), f'ocorrencias-{start:%Y%m%d}-{end:%Y%m%d}.pdf'

    def _pdf(self, start: date, end: date, rows: list) -> bytes:
        output = BytesIO(); doc = SimpleDocTemplate(output, pagesize=A4, leftMargin=7*mm, rightMargin=7*mm, topMargin=8*mm, bottomMargin=8*mm)
        styles = getSampleStyleSheet(); cell = ParagraphStyle('occurrence', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9)
        title = ParagraphStyle('occurrence-title', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=14)
        data = [['Data / Hora', 'Contrato', 'Cliente', 'Cobrador', 'Observação', 'Localização']]
        for occurrence, contract, client, collector in rows:
            moment = occurrence.created_at.astimezone(UTC).strftime('%d/%m/%Y\n%H:%M') if occurrence.created_at else '-'
            observation = 'Fechado' if occurrence.kind == 'closed' else 'Não pagou'
            link = '-'
            if occurrence.latitude and occurrence.longitude:
                url = quote(f'https://www.google.com/maps?q={occurrence.latitude},{occurrence.longitude}', safe=':/?=,')
                link = f'<link href="{url}" color="blue">Abrir mapa</link>'
            data.append([moment, str(contract.contratos_id if contract else occurrence.contract_id or '-'), client.nome if client else 'Cliente removido', collector, observation, link])
        if len(data) == 1: data.append(['-', '-', 'Nenhuma ocorrência no período.', '', '', ''])
        table = Table([[Paragraph(str(value).replace('\n', '<br/>'), cell) for value in row] for row in data], colWidths=[25*mm,22*mm,60*mm,32*mm,28*mm,25*mm], repeatRows=1)
        table.setStyle(TableStyle([('LINEBELOW',(0,0),(-1,0),.5,colors.black),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('LINEBELOW',(0,1),(-1,-1),.15,colors.grey),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
        now = datetime.now()
        def page_header(canvas, document):
            canvas.saveState(); canvas.setFont('Helvetica', 7); right=A4[0]-7*mm
            canvas.drawRightString(right, A4[1]-6*mm, now.strftime('%d/%m/%Y')); canvas.drawRightString(right, A4[1]-10*mm, now.strftime('%H:%M')); canvas.drawRightString(right, A4[1]-14*mm, f'N. Pág. {canvas.getPageNumber()}'); canvas.restoreState()
        doc.build([Paragraph('RELATÓRIO DE OCORRÊNCIAS', title), Paragraph(f'Período: {start:%d/%m/%Y} até {end:%d/%m/%Y}', cell), Spacer(1,4*mm), table], onFirstPage=page_header, onLaterPages=page_header)
        return output.getvalue()
