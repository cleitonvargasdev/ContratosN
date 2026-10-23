from collections import defaultdict
from datetime import UTC, date, datetime, time, timedelta
from io import BytesIO

from fastapi import HTTPException
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounts_receivable import ContaReceber
from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.contract_commodato import ContratoComodato, ContratoComodatoItem
from app.models.receipt import Recebimento
from app.models.user import User


class AccountsReceivableReportService:
    """Produces the open-installments report, grouped by customer and contract."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def generate(
        self,
        start: date,
        end: date,
        employee_id: int | None = None,
        client_id: int | None = None,
        comodato: bool | None = None,
    ) -> tuple[bytes, str]:
        if end < start:
            raise HTTPException(400, "A data final deve ser igual ou posterior à inicial.")
        if (end - start).days > 366:
            raise HTTPException(400, "Informe um período de até 1 ano.")
        if employee_id is not None and await self.session.get(User, employee_id) is None:
            raise HTTPException(404, "Funcionário não encontrado.")
        if client_id is not None and await self.session.get(Cliente, client_id) is None:
            raise HTTPException(404, "Cliente não encontrado.")

        rows = await self._rows(start, end, employee_id, client_id, comodato)
        items_by_contract = await self._commodato_items({row["contract"].contratos_id for row in rows})
        employee = await self.session.get(User, employee_id) if employee_id is not None else None
        client = await self.session.get(Cliente, client_id) if client_id is not None else None
        pdf = self._pdf(start, end, rows, items_by_contract, employee.nome if employee else None, client.nome if client else None, comodato)
        return pdf, f"contas-a-receber-{start:%Y%m%d}-{end:%Y%m%d}.pdf"

    async def _rows(self, start: date, end: date, employee_id: int | None, client_id: int | None, comodato: bool | None) -> list[dict]:
        due_date = func.coalesce(ContaReceber.vencimentol, ContaReceber.vencimento_original)
        balance = func.coalesce(ContaReceber.valor_total, 0) - func.coalesce(ContaReceber.valor_recebido, 0)
        filters = [
            due_date >= datetime.combine(start, time.min, UTC),
            due_date < datetime.combine(end + timedelta(days=1), time.min, UTC),
            or_(ContaReceber.quitado.is_(False), ContaReceber.quitado.is_(None)),
            balance > 0,
        ]
        if employee_id is not None:
            filters.append(Cliente.usuario_id == employee_id)
        if client_id is not None:
            filters.append(Cliente.clientes_id == client_id)

        comodato_exists = select(ContratoComodato.comodato_id).where(ContratoComodato.contrato_id == Contrato.contratos_id).exists()
        if comodato is True:
            filters.append(comodato_exists)
        elif comodato is False:
            filters.append(~comodato_exists)

        last_payment = (
            select(Recebimento.contrato_id.label("contract_id"), func.max(Recebimento.data_recebimento).label("last_payment"))
            .group_by(Recebimento.contrato_id)
            .subquery()
        )
        stmt = (
            select(ContaReceber, Contrato, Cliente, last_payment.c.last_payment)
            .join(Contrato, Contrato.contratos_id == ContaReceber.contratos_id)
            .outerjoin(Cliente, Cliente.clientes_id == Contrato.cliente_id)
            .outerjoin(last_payment, last_payment.c.contract_id == Contrato.contratos_id)
            .where(and_(*filters))
            .order_by(func.upper(Cliente.nome), Contrato.contratos_id, due_date, ContaReceber.parcela_nro, ContaReceber.id)
        )
        return [
            {"installment": installment, "contract": contract, "client": client, "last_payment": last_payment_date}
            for installment, contract, client, last_payment_date in (await self.session.execute(stmt)).all()
        ]

    async def _commodato_items(self, contract_ids: set[int]) -> dict[int, list[ContratoComodatoItem]]:
        if not contract_ids:
            return {}
        stmt = (
            select(ContratoComodato.contrato_id, ContratoComodatoItem)
            .join(ContratoComodatoItem, ContratoComodatoItem.comodato_id == ContratoComodato.comodato_id)
            .where(ContratoComodato.contrato_id.in_(contract_ids))
            .order_by(ContratoComodato.contrato_id, ContratoComodatoItem.item_id)
        )
        grouped: dict[int, list[ContratoComodatoItem]] = defaultdict(list)
        for contract_id, item in (await self.session.execute(stmt)).all():
            grouped[contract_id].append(item)
        return grouped

    def _pdf(self, start: date, end: date, rows: list[dict], items_by_contract: dict[int, list[ContratoComodatoItem]], employee: str | None, client: str | None, comodato: bool | None) -> bytes:
        output = BytesIO()
        page_size = landscape(A4)
        doc = SimpleDocTemplate(output, pagesize=page_size, leftMargin=6 * mm, rightMargin=6 * mm, topMargin=13 * mm, bottomMargin=9 * mm)
        styles = getSampleStyleSheet()
        title = ParagraphStyle("accounts-title", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=15, leading=17)
        client_style = ParagraphStyle("accounts-client", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10)
        cell = ParagraphStyle("accounts-cell", parent=styles["Normal"], fontName="Helvetica", fontSize=6.8, leading=8.2)
        bold_cell = ParagraphStyle("accounts-bold-cell", parent=cell, fontName="Helvetica-Bold")
        item_cell = ParagraphStyle("accounts-item", parent=cell, fontSize=6.5, leading=7.5)

        filters = [f"Período de vencimento: {start:%d/%m/%Y} até {end:%d/%m/%Y}", f"Funcionário: {employee or 'TODOS OS FUNCIONÁRIOS'}"]
        if client:
            filters.append(f"Cliente: {client}")
        filters.append(f"Comodato: {self._comodato_label(comodato)}")
        story = [Paragraph("RELATÓRIO DE CONTAS A RECEBER", title), Paragraph(" &nbsp;&nbsp; ".join(filters), cell), Spacer(1, 3 * mm)]
        headers = ["Contrato", "Data contrato", "Val. contrato", "Juros", "Dias", "Valor parcela", "Valor final", "Último pgto", "Parc. aberto", "Total vencido"]
        widths = [17 * mm, 22 * mm, 22 * mm, 13 * mm, 10 * mm, 22 * mm, 22 * mm, 22 * mm, 20 * mm, 25 * mm]
        grouped: dict[tuple[int | None, str], list[dict]] = defaultdict(list)
        for row in rows:
            entity = row["client"]
            grouped[(getattr(entity, "clientes_id", None), getattr(entity, "nome", None) or "CLIENTE NÃO INFORMADO")].append(row)

        total = 0.0
        for (_, client_name), client_rows in grouped.items():
            story.append(Paragraph(self._escape(client_name).upper(), client_style))
            by_contract: dict[int, list[dict]] = defaultdict(list)
            for row in client_rows:
                by_contract[row["contract"].contratos_id].append(row)
            table_rows: list[list[Paragraph]] = [[Paragraph(header, bold_cell) for header in headers]]
            for contract_id, contract_rows in by_contract.items():
                contract = contract_rows[0]["contract"]
                contract_total = sum(self._balance(row["installment"]) for row in contract_rows)
                total += contract_total
                table_rows.append([
                    Paragraph(str(contract_id), cell),
                    Paragraph(self._date(contract.data_contrato), cell),
                    Paragraph(self._money(contract.valor_empretismo), cell),
                    Paragraph(self._number(contract.percent_juros), cell),
                    Paragraph(str(contract.qtde_dias or "-"), cell),
                    Paragraph(self._money(contract.valor_parcela), cell),
                    Paragraph(self._money(contract.valor_final), cell),
                    Paragraph(self._date(contract_rows[0]["last_payment"]), cell),
                    Paragraph(str(len(contract_rows)), bold_cell),
                    Paragraph(self._money(contract_total), bold_cell),
                ])
                commodate_items = items_by_contract.get(contract_id, [])
                if commodate_items:
                    products = "<br/>".join(
                        f"<b>{int(item.quantidade or 0)}x</b> {self._escape(item.descricao_produto or 'Produto')}"
                        + (f" ({self._escape(item.condicao)})" if item.condicao else "")
                        for item in commodate_items
                    )
                    item_box = Table([[Paragraph(f"<b>COMODATO — Produtos:</b><br/>{products}", item_cell)]], colWidths=[189 * mm])
                    item_box.setStyle(TableStyle([
                        ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor("#64748b")),
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]))
                    table_rows.append([item_box] + [""] * (len(headers) - 1))
            table = Table(table_rows, colWidths=widths, repeatRows=1)
            table_style = [
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                ("LINEBELOW", (0, 1), (-1, -1), 0.2, colors.HexColor("#64748b")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
            for index, row in enumerate(table_rows):
                if isinstance(row[0], Table):
                    table_style.append(("SPAN", (0, index), (-1, index)))
                    table_style.append(("ALIGN", (0, index), (-1, index), "LEFT"))
            table.setStyle(TableStyle(table_style))
            story.extend([KeepTogether([table]), Spacer(1, 2 * mm)])
        if not rows:
            story.append(Paragraph("Nenhuma parcela em aberto encontrada para os filtros informados.", cell))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(f"*** TOTAL A RECEBER NO PERÍODO: &nbsp;&nbsp; {self._money(total)}", ParagraphStyle("accounts-total", parent=bold_cell, alignment=2, fontSize=8)))

        generated_at = datetime.now()
        def page_header(canvas, document):
            canvas.saveState()
            canvas.setFont("Helvetica", 7)
            right = page_size[0] - 6 * mm
            canvas.drawRightString(right, page_size[1] - 6 * mm, generated_at.strftime("%d/%m/%Y"))
            canvas.drawRightString(right, page_size[1] - 10 * mm, generated_at.strftime("%H:%M"))
            canvas.drawRightString(right, page_size[1] - 14 * mm, f"N. Pág. {canvas.getPageNumber()}")
            canvas.restoreState()
        doc.build(story, onFirstPage=page_header, onLaterPages=page_header)
        return output.getvalue()

    @staticmethod
    def _balance(item: ContaReceber) -> float:
        return max(float(item.valor_total or 0) - float(item.valor_recebido or 0), 0)

    @staticmethod
    def _money(value: float | None) -> str:
        return f"R$ {float(value or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def _number(value: float | None) -> str:
        return f"{float(value or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def _date(value: datetime | None) -> str:
        return value.strftime("%d/%m/%Y") if value else "-"

    @staticmethod
    def _comodato_label(value: bool | None) -> str:
        return "COM E SEM COMODATO" if value is None else ("SOMENTE COM COMODATO" if value else "SOMENTE SEM COMODATO")

    @staticmethod
    def _escape(value: str) -> str:
        return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
