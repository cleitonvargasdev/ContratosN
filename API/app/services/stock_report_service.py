from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from io import BytesIO

from fastapi import HTTPException
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Produto
from app.models.stock import MovimentoEstoque
from app.models.user import User


class StockReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def generate(self, start: date, end: date, product_id: int | None, user_id: int | None) -> tuple[bytes, str]:
        if end < start:
            raise HTTPException(400, "A data final deve ser igual ou posterior à inicial.")

        product = await self.session.get(Produto, product_id) if product_id else None
        if product_id and product is None:
            raise HTTPException(404, "Produto não encontrado.")
        user = await self.session.get(User, user_id) if user_id else None
        if user_id and user is None:
            raise HTTPException(404, "Usuário não encontrado.")

        start_at = datetime.combine(start, time.min, UTC)
        end_at = datetime.combine(end + timedelta(days=1), time.min, UTC)
        products = await self._products(product_id)
        balances = await self._opening_balances(start_at, product_id)
        closing_balances = await self._opening_balances(end_at, product_id)
        movements = await self._movements(start_at, end_at, product_id, user_id)
        pdf = self._pdf(start, end, products, balances, closing_balances, movements, product.descricao if product else None, user.nome if user else None)
        suffix = str(product_id) if product_id else "todos"
        return pdf, f"estoque-{suffix}-{start:%Y%m%d}-{end:%Y%m%d}.pdf"

    async def _products(self, product_id: int | None) -> list[Produto]:
        statement = select(Produto).order_by(Produto.descricao, Produto.produto_id)
        if product_id:
            statement = statement.where(Produto.produto_id == product_id)
        return list((await self.session.scalars(statement)).all())

    async def _opening_balances(self, start_at: datetime, product_id: int | None) -> dict[int, tuple[int, int]]:
        statement = select(
            MovimentoEstoque.produto_id,
            func.coalesce(func.sum(case((MovimentoEstoque.condicao == "novo", MovimentoEstoque.quantidade), else_=0)), 0),
            func.coalesce(func.sum(case((MovimentoEstoque.condicao == "usado", MovimentoEstoque.quantidade), else_=0)), 0),
        ).where(MovimentoEstoque.criado_em < start_at).group_by(MovimentoEstoque.produto_id)
        if product_id:
            statement = statement.where(MovimentoEstoque.produto_id == product_id)
        return {row[0]: (int(row[1]), int(row[2])) for row in (await self.session.execute(statement)).all()}

    async def _movements(self, start_at: datetime, end_at: datetime, product_id: int | None, user_id: int | None):
        statement = select(MovimentoEstoque).where(
            MovimentoEstoque.criado_em >= start_at,
            MovimentoEstoque.criado_em < end_at,
        )
        if product_id:
            statement = statement.where(MovimentoEstoque.produto_id == product_id)
        if user_id:
            statement = statement.where(MovimentoEstoque.usuario_id == user_id)
        statement = statement.order_by(MovimentoEstoque.produto_id, MovimentoEstoque.criado_em, MovimentoEstoque.movimento_id)
        return list((await self.session.scalars(statement)).all())

    def _pdf(self, start: date, end: date, products: list[Produto], balances: dict[int, tuple[int, int]], closing_balances: dict[int, tuple[int, int]], movements: list[MovimentoEstoque], product_name: str | None, user_name: str | None) -> bytes:
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=landscape(A4), leftMargin=7 * mm, rightMargin=7 * mm, topMargin=12 * mm, bottomMargin=8 * mm)
        styles = getSampleStyleSheet()
        normal = ParagraphStyle("stock-normal", parent=styles["Normal"], fontName="Helvetica", fontSize=7, leading=8.5)
        heading = ParagraphStyle("stock-heading", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=14, leading=16)
        summary = ParagraphStyle("stock-summary", parent=normal, fontName="Helvetica-Bold", alignment=2)
        elements = [
            Paragraph("RELATÓRIO DE MOVIMENTAÇÃO DE ESTOQUE", heading),
            Paragraph(f"Período: {start:%d/%m/%Y} até {end:%d/%m/%Y}", normal),
            Paragraph(f"Produto: <b>{product_name or 'TODOS OS PRODUTOS'}</b> &nbsp;&nbsp; Usuário: <b>{user_name or 'TODOS OS USUÁRIOS'}</b>", normal),
            Spacer(1, 4 * mm),
        ]
        movements_by_product: dict[int, list[MovimentoEstoque]] = {}
        for movement in movements:
            movements_by_product.setdefault(movement.produto_id, []).append(movement)

        for product in products:
            opening_new, opening_used = balances.get(product.produto_id, (0, 0))
            closing_new, closing_used = closing_balances.get(product.produto_id, (0, 0))
            rows = [["Data", "Operação", "Condição", "Entrada / saída", "Antes", "Depois", "Motivo / observação", "Responsável"]]
            for movement in movements_by_product.get(product.produto_id, []):
                note = movement.motivo + (f" — {movement.observacao}" if movement.observacao else "")
                when = movement.criado_em.astimezone(UTC).strftime("%d/%m/%Y %H:%M") if movement.criado_em.tzinfo else movement.criado_em.strftime("%d/%m/%Y %H:%M")
                rows.append([when, self._kind(movement.tipo), movement.condicao.title(), self._signed(movement.quantidade), str(movement.saldo_antes), str(movement.saldo_depois), note, movement.usuario_nome])

            if len(rows) == 1:
                rows.append(["", "", "", "", "", "", "Nenhuma movimentação no período.", ""])
            before_total = opening_new + opening_used
            after_total = closing_new + closing_used
            rows.append(["", "", "", "", "", "", "Saldo antes", f"Novos: {opening_new}  Usados: {opening_used}  Total: {before_total}"])
            rows.append(["", "", "", "", "", "", "Saldo depois", f"Novos: {closing_new}  Usados: {closing_used}  Total: {after_total}"])
            table_data = [[Paragraph(self._escape(str(cell)), normal) for cell in row] for row in rows]
            table = Table(table_data, colWidths=[29 * mm, 24 * mm, 20 * mm, 25 * mm, 16 * mm, 16 * mm, 94 * mm, 35 * mm], repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f5f7f9")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#8b98a5")),
                ("LINEBELOW", (0, 1), (-1, -3), 0.2, colors.HexColor("#d7dde3")),
                ("BACKGROUND", (0, -2), (-1, -1), colors.HexColor("#fff5ed")),
                ("FONTNAME", (6, -2), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (3, 1), (5, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.extend([Paragraph(f"Produto: <b>{self._escape(product.descricao)}</b>", summary), table, Spacer(1, 5 * mm)])

        generated_at = datetime.now()
        def page_header(canvas, _document):
            canvas.saveState()
            canvas.setFont("Helvetica", 7)
            canvas.drawRightString(landscape(A4)[0] - 7 * mm, landscape(A4)[1] - 7 * mm, f"Gerado em {generated_at:%d/%m/%Y %H:%M} · Página {canvas.getPageNumber()}")
            canvas.restoreState()
        doc.build(elements, onFirstPage=page_header, onLaterPages=page_header)
        return output.getvalue()

    @staticmethod
    def _kind(kind: str) -> str:
        return {"entrada": "Entrada", "baixa": "Baixa", "ajuste": "Ajuste", "devolucao": "Devolução", "venda": "Venda"}.get(kind, kind)

    @staticmethod
    def _signed(value: int) -> str:
        return f"+{value}" if value > 0 else str(value)

    @staticmethod
    def _escape(value: str) -> str:
        return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
