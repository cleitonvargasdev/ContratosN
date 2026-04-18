from datetime import datetime
from io import BytesIO

from fastapi import HTTPException, status
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timezone import get_local_timezone
from app.models.accounts_receivable import ContaReceber
from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.negotiation import Negociacao, NegociacaoContrato
from app.models.parameter import Parametro
from app.models.user import User


class NegotiationReportService:
    PAGE_MARGIN = 8 * mm

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.local_timezone = get_local_timezone()

    async def generate_negotiation_pdf(self, negotiation_id: int) -> tuple[bytes, str]:
        neg, client, user, parameter = await self._load_context(negotiation_id)
        original_contracts = await self._load_original_contracts(negotiation_id)
        new_installments = await self._load_new_installments(neg.contrato_gerado_id)

        pdf_bytes = self._build_pdf(
            neg=neg,
            client=client,
            user=user,
            company_name=(parameter.nome_fantasia or "EMPRESA").strip().upper() if parameter else "EMPRESA",
            original_contracts=original_contracts,
            new_installments=new_installments,
        )
        return pdf_bytes, f"negociacao-{negotiation_id}.pdf"

    async def _load_context(self, negotiation_id: int) -> tuple[Negociacao, Cliente | None, User | None, Parametro | None]:
        parameter_subquery = select(Parametro.parametros_id).order_by(Parametro.parametros_id.asc()).limit(1).scalar_subquery()
        result = await self.session.execute(
            select(Negociacao, Cliente, User, Parametro)
            .outerjoin(Cliente, Cliente.clientes_id == Negociacao.cliente_id)
            .outerjoin(User, User.id == Negociacao.usuario_id)
            .outerjoin(Parametro, Parametro.parametros_id == parameter_subquery)
            .where(Negociacao.negociacao_id == negotiation_id)
        )
        row = result.one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Negociacao nao encontrada")
        return row

    async def _load_original_contracts(self, negotiation_id: int) -> list[tuple[NegociacaoContrato, Contrato | None]]:
        result = await self.session.execute(
            select(NegociacaoContrato, Contrato)
            .outerjoin(Contrato, Contrato.contratos_id == NegociacaoContrato.contrato_id)
            .where(NegociacaoContrato.negociacao_id == negotiation_id)
            .order_by(NegociacaoContrato.contrato_id.asc())
        )
        return list(result.all())

    async def _load_new_installments(self, contract_id: int | None) -> list[ContaReceber]:
        if contract_id is None:
            return []
        result = await self.session.execute(
            select(ContaReceber)
            .where(ContaReceber.contratos_id == contract_id)
            .order_by(ContaReceber.parcela_nro.asc(), ContaReceber.vencimentol.asc(), ContaReceber.id.asc())
        )
        return list(result.scalars().all())

    def _build_pdf(
        self,
        *,
        neg: Negociacao,
        client: Cliente | None,
        user: User | None,
        company_name: str,
        original_contracts: list[tuple[NegociacaoContrato, Contrato | None]],
        new_installments: list[ContaReceber],
    ) -> bytes:
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=self.PAGE_MARGIN,
            rightMargin=self.PAGE_MARGIN,
            topMargin=self.PAGE_MARGIN,
            bottomMargin=self.PAGE_MARGIN,
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="CompanyTitle", parent=styles["Title"], fontSize=15, leading=18, alignment=TA_CENTER, textColor=colors.HexColor("#111827")))
        styles.add(ParagraphStyle(name="SectionTitle", parent=styles["Heading3"], fontSize=11, leading=14, textColor=colors.HexColor("#111827"), spaceAfter=4))
        styles.add(ParagraphStyle(name="MetaCell", parent=styles["Normal"], fontSize=9, leading=11, textColor=colors.HexColor("#111827")))
        styles.add(ParagraphStyle(name="CellCenter", parent=styles["Normal"], fontSize=8.5, leading=10, alignment=TA_CENTER))
        styles.add(ParagraphStyle(name="CellLeft", parent=styles["Normal"], fontSize=8.5, leading=10, alignment=TA_LEFT))

        story: list = [
            Paragraph(company_name, styles["CompanyTitle"]),
            Spacer(1, 2 * mm),
            Paragraph(f"<b>NEGOCIAÇÃO Nº {neg.negociacao_id}</b>", styles["SectionTitle"]),
            Spacer(1, 1 * mm),
        ]

        # Summary info
        col_width = (A4[0] - self.PAGE_MARGIN * 2) / 2
        summary_data = [
            [
                Paragraph(f"<b>Cliente:</b> {(client.nome if client else '-')}", styles["MetaCell"]),
                Paragraph(f"<b>Data:</b> {self._format_date(neg.data_negociacao)}", styles["MetaCell"]),
            ],
            [
                Paragraph(f"<b>Documento:</b> {(client.cpf_cnpj if client and client.cpf_cnpj else '-')}", styles["MetaCell"]),
                Paragraph(f"<b>Usuário:</b> {(user.nome if user else '-')}", styles["MetaCell"]),
            ],
            [
                Paragraph(f"<b>Valor Total em Aberto:</b> {self._format_currency(neg.valor_total_aberto)}", styles["MetaCell"]),
                Paragraph(f"<b>Contrato Gerado:</b> {neg.contrato_gerado_id or '-'}", styles["MetaCell"]),
            ],
            [
                Paragraph(f"<b>Qtde Parcelas:</b> {neg.qtde_parcelas}", styles["MetaCell"]),
                Paragraph(f"<b>Valor Parcela:</b> {self._format_currency(neg.valor_parcela)}", styles["MetaCell"]),
            ],
        ]
        summary_table = Table(summary_data, colWidths=[col_width, col_width])
        summary_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 4 * mm))

        # Original contracts section
        story.append(Paragraph("<b>Contratos Originais</b>", styles["SectionTitle"]))
        orig_header = [[
            Paragraph("<b>Contrato</b>", styles["CellCenter"]),
            Paragraph("<b>Data Contrato</b>", styles["CellCenter"]),
            Paragraph("<b>Valor Empréstimo</b>", styles["CellCenter"]),
            Paragraph("<b>Valor em Aberto</b>", styles["CellCenter"]),
        ]]
        orig_rows = []
        for link, contract in original_contracts:
            orig_rows.append([
                Paragraph(str(link.contrato_id), styles["CellCenter"]),
                Paragraph(self._format_date(contract.data_contrato) if contract else "-", styles["CellCenter"]),
                Paragraph(self._format_currency(float(contract.valor_empretismo or 0)) if contract else "-", styles["CellCenter"]),
                Paragraph(self._format_currency(link.valor_aberto), styles["CellCenter"]),
            ])

        orig_table_data = orig_header + orig_rows
        orig_col_widths = [30 * mm, 35 * mm, 45 * mm, 45 * mm]
        orig_table = Table(orig_table_data, colWidths=orig_col_widths, repeatRows=1)
        orig_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(orig_table)
        story.append(Spacer(1, 5 * mm))

        # New installments section
        if new_installments:
            story.append(Paragraph(f"<b>Parcelas do Novo Contrato ({neg.contrato_gerado_id})</b>", styles["SectionTitle"]))
            inst_header = [[
                Paragraph("<b>Parc.</b>", styles["CellCenter"]),
                Paragraph("<b>Vencimento</b>", styles["CellCenter"]),
                Paragraph("<b>Valor</b>", styles["CellCenter"]),
                Paragraph("<b>Situação</b>", styles["CellCenter"]),
            ]]
            inst_rows = []
            for inst in new_installments:
                sit = "QUITADO" if inst.quitado else "PENDENTE"
                inst_rows.append([
                    Paragraph(str(inst.parcela_nro or "-"), styles["CellCenter"]),
                    Paragraph(self._format_date(inst.vencimentol or inst.vencimento_original), styles["CellCenter"]),
                    Paragraph(self._format_currency(float(inst.valor_total or inst.valor_base or 0)), styles["CellCenter"]),
                    Paragraph(sit, styles["CellCenter"]),
                ])

            inst_table_data = inst_header + inst_rows
            inst_col_widths = [20 * mm, 35 * mm, 45 * mm, 30 * mm]
            inst_table = Table(inst_table_data, colWidths=inst_col_widths, repeatRows=1)
            inst_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]))
            story.append(inst_table)
        else:
            story.append(Paragraph(f"<b>Novo Contrato ({neg.contrato_gerado_id})</b> - Parcelas ainda nao geradas", styles["SectionTitle"]))

        story.append(Spacer(1, 6 * mm))

        # Observation
        if neg.obs:
            story.append(Paragraph("<b>Observações:</b>", styles["MetaCell"]))
            story.append(Spacer(1, 1 * mm))
            story.append(Paragraph(neg.obs.replace("\n", "<br/>"), styles["MetaCell"]))

        document.build(story, onFirstPage=self._draw_page_frame, onLaterPages=self._draw_page_frame)
        return buffer.getvalue()

    @classmethod
    def _draw_page_frame(cls, canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#94a3b8"))
        canvas.setLineWidth(0.5)
        inset = 1.5 * mm
        canvas.rect(
            document.leftMargin - inset,
            document.bottomMargin - inset,
            document.pagesize[0] - (document.leftMargin + document.rightMargin) + (inset * 2),
            document.pagesize[1] - (document.topMargin + document.bottomMargin) + (inset * 2),
        )
        canvas.restoreState()

    @staticmethod
    def _format_currency(value: float | None) -> str:
        if value is None:
            return "-"
        return f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

    def _format_date(self, value: datetime | None) -> str:
        if value is None:
            return "-"
        if value.tzinfo is not None and value.utcoffset() is not None:
            value = value.astimezone(self.local_timezone)
        return value.strftime("%d/%m/%Y")
