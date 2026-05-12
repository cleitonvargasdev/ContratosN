from datetime import datetime
from io import BytesIO

from fastapi import HTTPException, status
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.graphics.shapes import Drawing, PolyLine
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.accounts_receivable import ContaReceber
from app.models.client import Cliente
from app.models.contract import Contrato
from app.models.contract_commodato import ContratoComodato
from app.models.location import Bairro, Cidade
from app.models.parameter import Parametro
from app.models.receipt import Recebimento
from app.core.timezone import get_local_timezone
from app.services.whatsapp_service import WhatsAppService


class ContractReportService:
    PAGE_MARGIN = 5 * mm
    COLUMN_GAP = 4 * mm
    MAX_ROWS_PER_COLUMN = 17

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.whatsapp_service = WhatsAppService(session)
        self.local_timezone = get_local_timezone()

    async def generate_contract_pdf(self, contract_id: int) -> tuple[bytes, str]:
        contract, client, parameter = await self._load_contract_context(contract_id)
        installments = await self._load_installments(contract_id)
        latest_receipts = await self._load_latest_receipts(contract_id)
        bairro_name, cidade_name = await self._load_location_labels(client)

        pdf_bytes = self._build_pdf(
            contract=contract,
            client=client,
            company_name=(parameter.nome_fantasia or "EMPRESA").strip().upper() if parameter else "EMPRESA",
            installments=installments,
            latest_receipts=latest_receipts,
            bairro_name=bairro_name,
            cidade_name=cidade_name,
        )
        return pdf_bytes, f"contrato-{contract.contratos_id}.pdf"

    async def generate_commodato_pdf(self, contract_id: int) -> tuple[bytes, str]:
        contract, client, parameter = await self._load_contract_context(contract_id)
        comodato = await self._load_commodato(contract_id)
        installments = await self._load_installments(contract_id)
        if comodato is None or not list(getattr(comodato, "items", []) or []):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comodato nao encontrado")

        parameter_bairro_name, parameter_city_name = await self._load_parameter_location_labels(parameter)
        pdf_bytes = self._build_commodato_pdf(
            contract=contract,
            client=client,
            parameter=parameter,
            comodato=comodato,
            installments=installments,
            parameter_bairro_name=parameter_bairro_name,
            parameter_city_name=parameter_city_name,
        )
        return pdf_bytes, f"comodato-{contract.contratos_id}.pdf"

    async def send_contract_pdf_whatsapp(self, contract_id: int, public_pdf_url: str) -> dict[str, object]:
        contract, client, _ = await self._load_contract_context(contract_id)
        if client is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente nao encontrado")
        if client.nao_enviar_whatsapp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cliente marcado para nao enviar WhatsApp")

        phone_number = (client.celular01 or client.telefone or "").strip()
        if not phone_number:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cliente sem telefone cadastrado para WhatsApp")

        message_text = f"Olá! {(client.nome or 'cliente').strip() or 'cliente'}, segue o espelho do seu contrato nº {contract.contratos_id}."
        provider_result = await self.whatsapp_service.send_document_message(phone_number, public_pdf_url, message_text)
        return {
            "success": True,
            "message": str(provider_result.get("message") or "Documento enviado com sucesso."),
            "chatid": str(provider_result.get("chatid") or ""),
            "contract_id": contract.contratos_id,
            "document_url": public_pdf_url,
        }

    async def _load_contract_context(self, contract_id: int) -> tuple[Contrato, Cliente | None, Parametro | None]:
        parameter_subquery = select(Parametro.parametros_id).order_by(Parametro.parametros_id.asc()).limit(1).scalar_subquery()
        result = await self.session.execute(
            select(Contrato, Cliente, Parametro)
            .outerjoin(Cliente, Cliente.clientes_id == Contrato.cliente_id)
            .outerjoin(Parametro, Parametro.parametros_id == parameter_subquery)
            .where(Contrato.contratos_id == contract_id)
        )
        row = result.one_or_none()
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato nao encontrado")
        return row

    async def _load_installments(self, contract_id: int) -> list[ContaReceber]:
        result = await self.session.execute(
            select(ContaReceber)
            .where(ContaReceber.contratos_id == contract_id)
            .order_by(ContaReceber.parcela_nro.asc(), ContaReceber.vencimentol.asc(), ContaReceber.id.asc())
        )
        return list(result.scalars().all())

    async def _load_latest_receipts(self, contract_id: int) -> dict[int, datetime | None]:
        result = await self.session.execute(
            select(Recebimento.parcela_nro, func.max(Recebimento.data_recebimento))
            .where(Recebimento.contrato_id == contract_id)
            .group_by(Recebimento.parcela_nro)
        )
        return {int(parcela_nro): latest for parcela_nro, latest in result.all() if parcela_nro is not None}

    async def _load_commodato(self, contract_id: int) -> ContratoComodato | None:
        result = await self.session.execute(
            select(ContratoComodato)
            .options(selectinload(ContratoComodato.items), selectinload(ContratoComodato.avalista))
            .where(ContratoComodato.contrato_id == contract_id)
        )
        return result.scalar_one_or_none()

    async def _load_location_labels(self, client: Cliente | None) -> tuple[str | None, str | None]:
        if client is None:
            return None, None

        bairro_name: str | None = None
        cidade_name: str | None = None

        if client.bairro_id is not None:
            bairro_name = await self.session.scalar(select(Bairro.bairro_nome).where(Bairro.bairro_id == client.bairro_id))

        if client.cidade_id is not None:
            cidade_name = await self.session.scalar(select(Cidade.cidade).where(Cidade.cidade_id == client.cidade_id))

        return bairro_name, cidade_name

    async def _load_parameter_location_labels(self, parameter: Parametro | None) -> tuple[str | None, str | None]:
        if parameter is None:
            return None, None

        bairro_name: str | None = None
        cidade_name: str | None = None

        if parameter.bairrosid is not None:
            bairro_name = await self.session.scalar(select(Bairro.bairro_nome).where(Bairro.bairro_id == parameter.bairrosid))

        if parameter.cidade_id is not None:
            cidade_name = await self.session.scalar(select(Cidade.cidade).where(Cidade.cidade_id == parameter.cidade_id))

        return bairro_name, cidade_name

    def _build_pdf(
        self,
        *,
        contract: Contrato,
        client: Cliente | None,
        company_name: str,
        installments: list[ContaReceber],
        latest_receipts: dict[int, datetime | None],
        bairro_name: str | None,
        cidade_name: str | None,
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
        styles.add(ParagraphStyle(name="MetaCell", parent=styles["Normal"], fontSize=9, leading=11, textColor=colors.HexColor("#111827")))
        styles.add(ParagraphStyle(name="CellCenter", parent=styles["Normal"], fontSize=8.5, leading=10, alignment=TA_CENTER))

        installment_amount = self._resolve_installment_amount(contract, installments)
        summary_rows = [
            [
                Paragraph(f"<b>Contrato:</b> {contract.contratos_id}", styles["MetaCell"]),
                Paragraph(f"<b>Nº de Parcelas:</b> {len(installments)}", styles["MetaCell"]),
            ],
            [
                Paragraph(f"<b>Cliente:</b> {(client.nome if client and client.nome else '-')}", styles["MetaCell"]),
                Paragraph(f"<b>Valor R$:</b> {self._format_currency(installment_amount)}", styles["MetaCell"]),
            ],
            [
                Paragraph(f"<b>Documento:</b> {(client.cpf_cnpj if client and client.cpf_cnpj else '-')}", styles["MetaCell"]),
                Paragraph(f"<b>Telefone:</b> {(client.celular01 if client and client.celular01 else client.telefone if client and client.telefone else '-')}", styles["MetaCell"]),
            ],
            [
                Paragraph(f"<b>Endereco:</b> {self._build_address(client, bairro_name, cidade_name)}", styles["MetaCell"]),
                Paragraph("", styles["MetaCell"]),
            ],
        ]
        observation_text = (contract.obs or "").strip()
        if observation_text:
            summary_rows.append([
                Paragraph(f"<b>Observação:</b> {observation_text}", styles["MetaCell"]),
                Paragraph("", styles["MetaCell"]),
            ])

        summary_table = Table(summary_rows, colWidths=[98 * mm, 98 * mm])
        summary_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("SPAN", (0, len(summary_rows) - 1), (1, len(summary_rows) - 1)) if observation_text else ("TOPPADDING", (0, 0), (0, 0), 2),
        ]))

        story = [
            Paragraph(company_name or "EMPRESA", styles["CompanyTitle"]),
            Spacer(1, 2.5 * mm),
            summary_table,
            Spacer(1, 3 * mm),
        ]

        table_header = [[
            Paragraph("<b>Parc.</b>", styles["CellCenter"]),
            Paragraph("<b>Vencimento</b>", styles["CellCenter"]),
            Paragraph("<b>Valor</b>", styles["CellCenter"]),
            Paragraph("<b>PG</b>", styles["CellCenter"]),
            Paragraph("<b>Data</b>", styles["CellCenter"]),
        ]]

        rows: list[list[object]] = []
        for installment in installments:
            parcela_nro = int(installment.parcela_nro or 0)
            latest_payment = latest_receipts.get(parcela_nro)
            value_text = self._format_currency(float(installment.valor_total or installment.valor_base or contract.valor_parcela or 0))
            rows.append([
                Paragraph(str(parcela_nro or "-"), styles["CellCenter"]),
                Paragraph(self._format_date(installment.vencimentol or installment.vencimento_original), styles["CellCenter"]),
                Paragraph(value_text, styles["CellCenter"]),
                self._build_payment_ok_mark() if installment.quitado else Paragraph("-", styles["CellCenter"]),
                Paragraph(self._format_date(latest_payment), styles["CellCenter"]),
            ])

        if rows:
            for section_start in range(0, len(rows), self.MAX_ROWS_PER_COLUMN * 2):
                left_rows = rows[section_start : section_start + self.MAX_ROWS_PER_COLUMN]
                right_rows = rows[section_start + self.MAX_ROWS_PER_COLUMN : section_start + (self.MAX_ROWS_PER_COLUMN * 2)]
                dual_table = self._build_installments_dual_table(table_header, left_rows, right_rows)
                story.append(dual_table)
                story.append(Spacer(1, 2 * mm))

        document.build(story, onFirstPage=self._draw_page_frame, onLaterPages=self._draw_page_frame)
        return buffer.getvalue()

    def _build_commodato_pdf(
        self,
        *,
        contract: Contrato,
        client: Cliente | None,
        parameter: Parametro | None,
        comodato: ContratoComodato,
        installments: list[ContaReceber],
        parameter_bairro_name: str | None,
        parameter_city_name: str | None,
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
        styles.add(ParagraphStyle(name="ComodatoCompanyTitle", parent=styles["Title"], fontSize=16, leading=19, alignment=TA_CENTER, textColor=colors.HexColor("#111827")))
        styles.add(ParagraphStyle(name="ComodatoTitle", parent=styles["Heading2"], fontSize=13, leading=15, alignment=TA_CENTER, textColor=colors.HexColor("#111827")))
        styles.add(ParagraphStyle(name="ComodatoMeta", parent=styles["Normal"], fontSize=10.8, leading=12.8, textColor=colors.HexColor("#111827")))
        styles.add(ParagraphStyle(name="ComodatoCell", parent=styles["Normal"], fontSize=10.5, leading=12, textColor=colors.HexColor("#111827")))
        styles.add(ParagraphStyle(name="ComodatoBody", parent=styles["Normal"], fontSize=10.7, leading=13, alignment=TA_JUSTIFY, textColor=colors.HexColor("#111827")))
        styles.add(ParagraphStyle(name="ComodatoSignature", parent=styles["Normal"], fontSize=8.8, leading=10.8, alignment=TA_CENTER, textColor=colors.HexColor("#111827")))

        avalista = getattr(comodato, "avalista", None)
        items = list(getattr(comodato, "items", []) or [])
        total_quantidade = sum(int(item.quantidade or 0) for item in items)
        total_valor = sum(float(item.quantidade or 0) * float(item.valor_unitario or 0) for item in items)
        company_name = self._to_title_case(parameter.nome_fantasia or parameter.razao_social if parameter else "Empresa")
        company_address = self._build_parameter_address(parameter, parameter_bairro_name, parameter_city_name)
        emission_city = self._to_title_case(parameter_city_name) if parameter_city_name else ""
        emission_date = datetime.now(self.local_timezone).strftime("%d/%m/%Y")
        installment_count = len(installments)
        installment_value = self._resolve_installment_amount(contract, installments)
        first_due_date = installments[0].vencimentol or installments[0].vencimento_original if installments else None
        last_due_date = installments[-1].vencimentol or installments[-1].vencimento_original if installments else None
        payment_schedule_label = self._describe_contract_payment_schedule(contract)

        header_rows = [
            [
                Paragraph(f"<b>Comodato:</b> {contract.contratos_id}", styles["ComodatoMeta"]),
                Paragraph(f"<b>Data:</b> {emission_date}", styles["ComodatoMeta"]),
            ],
            [
                Paragraph(f"<b>Cliente:</b> {self._to_title_case(client.nome if client and client.nome else '-')}", styles["ComodatoMeta"]),
                Paragraph(f"<b>Documento:</b> {(client.cpf_cnpj if client and client.cpf_cnpj else '-')}", styles["ComodatoMeta"]),
            ],
            [
                Paragraph(f"<b>Avalista:</b> {self._to_title_case(getattr(avalista, 'nome', None) or '-')}", styles["ComodatoMeta"]),
                Paragraph(f"<b>Telefone:</b> {(client.celular01 if client and client.celular01 else client.telefone if client and client.telefone else '-')}", styles["ComodatoMeta"]),
            ],
            [
                Paragraph(f"<b>Emitente:</b> {company_name}", styles["ComodatoMeta"]),
                Paragraph(f"<b>Cidade:</b> {self._to_title_case(parameter_city_name or '-')}", styles["ComodatoMeta"]),
            ],
            [
                Paragraph(f"<b>Endereço:</b> {self._to_title_case(company_address)}", styles["ComodatoMeta"]),
                Paragraph(f"<b>Quantidade Total:</b> {total_quantidade}", styles["ComodatoMeta"]),
            ],
        ]

        header_table = Table(header_rows, colWidths=[98 * mm, 98 * mm])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))

        item_rows: list[list[object]] = [[
            Paragraph("<b>Quantidade</b>", styles["ComodatoCell"]),
            Paragraph("<b>Unidade</b>", styles["ComodatoCell"]),
            Paragraph("<b>Produto</b>", styles["ComodatoCell"]),
            Paragraph("<b>Valor Unitário</b>", styles["ComodatoCell"]),
            Paragraph("<b>Subtotal</b>", styles["ComodatoCell"]),
        ]]

        for item in items:
            subtotal = float(item.quantidade or 0) * float(item.valor_unitario or 0)
            item_rows.append([
                Paragraph(str(int(item.quantidade or 0)), styles["ComodatoCell"]),
                Paragraph("Unidade", styles["ComodatoCell"]),
                Paragraph(self._to_title_case(item.descricao_produto or f"Produto {item.produto_id}"), styles["ComodatoCell"]),
                Paragraph(self._format_currency(float(item.valor_unitario or 0)), styles["ComodatoCell"]),
                Paragraph(self._format_currency(subtotal), styles["ComodatoCell"]),
            ])

        items_table = Table(item_rows, colWidths=[22 * mm, 24 * mm, 84 * mm, 30 * mm, 36 * mm], repeatRows=1)
        items_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))

        total_table = Table(
            [[Paragraph(f"<b>Total Do Comodato:</b> {self._format_currency(total_valor)}", styles["ComodatoMeta"]) ]],
            colWidths=[196 * mm],
        )
        total_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))

        city_line = f"{emission_city}, {emission_date}" if emission_city else emission_date
        intro_text = (
            f"Contrato de comodato que entre si fazem {company_name}, estabelecida em {self._to_title_case(company_address)}, "
            f"doravante denominada comodante, e {self._to_title_case(client.nome if client and client.nome else 'cliente')}, "
            f"doravante denominado(a) comodatário(a), tendo como avalista {self._to_title_case(getattr(avalista, 'nome', None) or '-')}, "
            f" mediante as cláusulas e condições seguintes."
        )
        clauses = self._build_commodato_clause_texts(
            contract_id=contract.contratos_id,
            total_valor=total_valor,
            total_quantidade=total_quantidade,
            installment_count=installment_count,
            installment_value=installment_value,
            payment_schedule_label=payment_schedule_label,
            first_due_date=self._format_date(first_due_date),
            last_due_date=self._format_date(last_due_date),
            company_name=company_name,
            client_name=self._to_title_case(client.nome if client and client.nome else '-'),
            avalista_name=self._to_title_case(getattr(avalista, 'nome', None) or '-'),
            emission_city=emission_city or '-',
            emission_date=emission_date,
        )
        signature_table = self._build_commodato_signature_table(
            styles=styles,
            company_name=company_name,
            client_name=self._to_title_case(client.nome if client and client.nome else '-'),
            avalista_name=self._to_title_case(getattr(avalista, 'nome', None) or '-'),
        )

        story = [
            Paragraph(company_name or "Empresa", styles["ComodatoCompanyTitle"]),
            Spacer(1, 2 * mm),
            Paragraph(f"Comodato Nº {contract.contratos_id}", styles["ComodatoTitle"]),
            Spacer(1, 2.5 * mm),
            header_table,
            Spacer(1, 3 * mm),
            Paragraph(intro_text, styles["ComodatoBody"]),
            Spacer(1, 2 * mm),
            items_table,
            Spacer(1, 2 * mm),
            total_table,
            Spacer(1, 2.5 * mm),
        ]

        for clause in clauses:
            story.append(Paragraph(clause, styles["ComodatoBody"]))
            story.append(Spacer(1, 1.6 * mm))

        story.extend([
            Spacer(1, 5 * mm),
            Paragraph(self._to_title_case(city_line), styles["ComodatoMeta"]),
            Spacer(1, 7 * mm),
            signature_table,
        ])

        document.build(story, onFirstPage=self._draw_page_frame, onLaterPages=self._draw_page_frame)
        return buffer.getvalue()

    def _build_commodato_signature_table(self, *, styles, company_name: str, client_name: str, avalista_name: str) -> Table:
        signature_rows = [
            [Paragraph("__________________________________", styles["ComodatoSignature"]), Paragraph("__________________________________", styles["ComodatoSignature"]), Paragraph("__________________________________", styles["ComodatoSignature"])],
            [Paragraph(company_name, styles["ComodatoSignature"]), Paragraph(client_name, styles["ComodatoSignature"]), Paragraph(avalista_name, styles["ComodatoSignature"])],
            [Paragraph("Comodante", styles["ComodatoSignature"]), Paragraph("Comodatário(a)", styles["ComodatoSignature"]), Paragraph("Avalista", styles["ComodatoSignature"])],
        ]
        table = Table(signature_rows, colWidths=[64 * mm, 64 * mm, 64 * mm])
        table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        return table

    @staticmethod
    def _build_commodato_clause_texts(
        *,
        contract_id: int,
        total_valor: float,
        total_quantidade: int,
        installment_count: int,
        installment_value: float,
        payment_schedule_label: str,
        first_due_date: str,
        last_due_date: str,
        company_name: str,
        client_name: str,
        avalista_name: str,
        emission_city: str,
        emission_date: str,
    ) -> list[str]:
        return [
            f"I - O objeto deste comodato corresponde às mercadorias descritas na tabela acima, vinculadas ao contrato nº {contract_id}, em quantidade total de {total_quantidade} item(ns) e valor de referência de {ContractReportService._format_currency(total_valor)}.",
            f"II - O contrato vinculado a este comodato será pago em {installment_count} parcela(s) de {ContractReportService._format_currency(installment_value)}, {payment_schedule_label}, iniciando em {first_due_date} e finalizando em {last_due_date}, conforme informações do contrato.",
            f"III - As mercadorias permanecem de propriedade exclusiva da comodante {company_name}, ficando a posse direta com {client_name}, que declara recebê-las em perfeito estado de conservação e funcionamento.",
            f"IV - O(a) comodatário(a) obriga-se a manter os bens em perfeito estado, utilizando-os de forma adequada, não podendo ceder, alienar, transferir, penhorar ou dar destinação diversa da ajustada, sem autorização expressa da comodante.",
            f"V - Em caso de inadimplemento contratual, uso indevido, retenção indevida ou descumprimento de qualquer cláusula, assistirá à comodante o direito de promover a imediata restituição dos bens, bem como a cobrança das perdas e danos eventualmente apuradas.",
            f"VI - O(a) avalista {avalista_name} assina o presente instrumento e assume responsabilidade solidária pelo fiel cumprimento das obrigações aqui estabelecidas, inclusive quanto à guarda, restituição e integridade dos bens entregues em comodato.",
            f"VII - Caso haja necessidade de ingresso em juízo, correrão por conta do(a) comodatário(a) as despesas judiciais, custas processuais e honorários advocatícios, ficando eleito o foro da comarca informada no contrato para dirimir eventuais dúvidas oriundas deste instrumento.",
            f"VIII - E, por estarem de pleno acordo, comodante, comodatário(a) e avalista assinam o presente comodato em duas vias de igual teor, para todos os efeitos de direito, em {emission_city}, na data de {emission_date}.",
        ]

    @staticmethod
    def _describe_contract_payment_schedule(contract: Contrato) -> str:
        if bool(contract.cobranca_mensal):
            return "em pagamentos mensais"

        if bool(contract.cobranca_quinzenal):
            return "em pagamentos quinzenais"

        allowed_weekdays = ContractReportService._get_allowed_weekdays(contract)
        if allowed_weekdays == {0, 1, 2, 3, 4}:
            return "em pagamentos diários de segunda a sexta"
        if allowed_weekdays == {0, 1, 2, 3, 4, 5}:
            return "em pagamentos diários de segunda a sábado"
        if allowed_weekdays == {0, 1, 2, 3, 4, 5, 6}:
            return "em pagamentos diários de segunda a domingo"
        if len(allowed_weekdays) == 1:
            return "em pagamentos semanais"

        return "conforme a periodicidade definida no contrato"

    @staticmethod
    def _get_allowed_weekdays(contract: Contrato) -> set[int]:
        allowed_weekdays: set[int] = set()
        if bool(contract.cobranca_domingo):
            allowed_weekdays.add(6)
        if bool(contract.cobranca_segunda):
            allowed_weekdays.add(0)
        if bool(contract.cobranca_terca):
            allowed_weekdays.add(1)
        if bool(contract.cobranca_quarta):
            allowed_weekdays.add(2)
        if bool(contract.cobranca_quinta):
            allowed_weekdays.add(3)
        if bool(contract.cobranca_sexta):
            allowed_weekdays.add(4)
        if bool(contract.cobranca_sabado):
            allowed_weekdays.add(5)
        return allowed_weekdays or {0, 1, 2, 3, 4}

    def _build_installments_dual_table(self, table_header: list[list[object]], left_rows: list[list[object]], right_rows: list[list[object]]) -> Table:
        left_table = self._build_installment_table(table_header + left_rows)
        right_table = self._build_installment_table(table_header + right_rows) if right_rows else Spacer(1, 1)
        wrapper = Table(
            [[left_table, right_table]],
            colWidths=[(A4[0] - (self.PAGE_MARGIN * 2) - self.COLUMN_GAP) / 2, (A4[0] - (self.PAGE_MARGIN * 2) - self.COLUMN_GAP) / 2],
        )
        wrapper.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        return wrapper

    @staticmethod
    def _build_installment_table(table_data: list[list[object]]) -> Table:
        table = Table(table_data, colWidths=[11 * mm, 20 * mm, 29 * mm, 9 * mm, 17 * mm], repeatRows=1)
        table.setStyle(TableStyle([
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
        return table

    @staticmethod
    def _build_payment_ok_mark() -> Drawing:
        drawing = Drawing(8, 8)
        check = PolyLine([1, 4, 3.25, 1.5, 7, 6.5], strokeColor=colors.black, strokeWidth=1.25)
        drawing.add(check)
        return drawing

    @classmethod
    def _draw_page_frame(cls, canvas, document) -> None:
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
    def _resolve_installment_amount(contract: Contrato, installments: list[ContaReceber]) -> float:
        if contract.valor_parcela is not None:
            return float(contract.valor_parcela)
        if installments:
            return float(installments[0].valor_total or installments[0].valor_base or 0)
        return 0.0

    @staticmethod
    def _build_address(client: Cliente | None, bairro_name: str | None, cidade_name: str | None) -> str:
        if client is None:
            return "-"

        street_parts = [
            (client.endereco or "").strip(),
            (client.nro or "").strip(),
            (client.complemento or "").strip(),
        ]
        location_parts = [
            (bairro_name or "").strip(),
            (cidade_name or "").strip(),
            (client.uf or "").strip(),
        ]

        values = [part for part in street_parts if part]
        location_values = [part for part in location_parts if part]
        if location_values:
            values.append(" - ".join(location_values))

        return ", ".join(values) if values else "-"

    @staticmethod
    def _build_parameter_address(parameter: Parametro | None, bairro_name: str | None, cidade_name: str | None) -> str:
        if parameter is None:
            return "-"

        street_parts = [
            (parameter.endereco or "").strip(),
            str(parameter.nro).strip() if parameter.nro is not None else "",
            (parameter.complemento or "").strip(),
        ]
        location_parts = [
            (bairro_name or "").strip(),
            (cidade_name or "").strip(),
            (parameter.uf or "").strip(),
            (parameter.cep or "").strip(),
        ]

        values = [part for part in street_parts if part]
        location_values = [part for part in location_parts if part]
        if location_values:
            values.append(" - ".join(location_values))

        return ", ".join(values) if values else "-"

    @staticmethod
    def _format_currency(value: float) -> str:
        return f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

    def _format_date(self, value: datetime | None) -> str:
        if value is None:
            return "-"
        if value.tzinfo is not None and value.utcoffset() is not None:
            value = value.astimezone(self.local_timezone)
        return value.strftime("%d/%m/%Y")

    @staticmethod
    def _to_title_case(value: str | None) -> str:
        text = (value or "-").strip()
        if not text:
            return "-"
        return " ".join(part[:1].upper() + part[1:].lower() if part else "" for part in text.split())
