from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "arquitetura-multicliente-por-tenant.pdf"

NAVY = colors.HexColor("#19324A")
BLUE = colors.HexColor("#D9E8FF")
BLUE_BORDER = colors.HexColor("#78A9FF")
YELLOW = colors.HexColor("#FFF0BF")
YELLOW_BORDER = colors.HexColor("#E4BC50")
GREEN = colors.HexColor("#DCEFE2")
GREEN_BORDER = colors.HexColor("#84BE94")
ROSE = colors.HexColor("#FAD9D6")
ROSE_BORDER = colors.HexColor("#DF9993")
TEXT = colors.HexColor("#263746")
MUTED = colors.HexColor("#5F6E79")


class ArchitectureDiagram(Flowable):
    def __init__(self, mode: str) -> None:
        super().__init__()
        self.mode = mode
        self.width = 17.2 * cm
        self.height = 12.5 * cm

    @staticmethod
    def _box(canvas, x, y, width, height, title, lines, fill, border):
        canvas.setFillColor(fill)
        canvas.setStrokeColor(border)
        canvas.setLineWidth(1.2)
        canvas.roundRect(x, y, width, height, 8, fill=1, stroke=1)
        canvas.setFillColor(NAVY)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawCentredString(x + width / 2, y + height - 16, title)
        canvas.setFillColor(TEXT)
        canvas.setFont("Helvetica", 8.2)
        baseline = y + height - 32
        for line in lines:
            canvas.drawCentredString(x + width / 2, baseline, line)
            baseline -= 12

    @staticmethod
    def _arrow(canvas, x1, y1, x2, y2, label=None):
        canvas.setStrokeColor(NAVY)
        canvas.setFillColor(NAVY)
        canvas.setLineWidth(1.25)
        canvas.line(x1, y1, x2, y2)
        angle_x = -6 if x2 >= x1 else 6
        canvas.line(x2, y2, x2 + angle_x, y2 + 3)
        canvas.line(x2, y2, x2 + angle_x, y2 - 3)
        if label:
            canvas.setFont("Helvetica", 7.4)
            canvas.drawCentredString((x1 + x2) / 2, (y1 + y2) / 2 + 6, label)

    def draw(self):
        canvas = self.canv
        x = 0
        if self.mode == "front":
            self._box(canvas, x, 280, 150, 65, "FRONTEND", ["cvfinanceiro.vstec.net", "ou", "bcfinanceiro.vstec.net"], BLUE, BLUE_BORDER)
            self._box(canvas, x + 230, 280, 150, 65, "API / BACKEND", ["Resolvedor lê o Host", "e identifica o tenant"], YELLOW, YELLOW_BORDER)
            self._box(canvas, x + 460, 280, 150, 65, "REGISTRO CENTRAL", ["Domínio -> cliente", "cliente -> banco"], GREEN, GREEN_BORDER)
            self._arrow(canvas, 150, 312, 230, 312, "HTTPS")
            self._arrow(canvas, 380, 312, 460, 312, "consulta")
            self._box(canvas, x + 230, 130, 150, 65, "SESSÃO SQL", ["Conexão exclusiva", "por requisição"], YELLOW, YELLOW_BORDER)
            self._box(canvas, x + 460, 205, 150, 65, "BANCO CV", ["cv_financeiro", "dados só da CV"], BLUE, BLUE_BORDER)
            self._box(canvas, x + 460, 100, 150, 65, "BANCO BC", ["bc_financeiro", "dados só da BC"], ROSE, ROSE_BORDER)
            self._arrow(canvas, 305, 280, 305, 195, "sessão")
            self._arrow(canvas, 380, 162, 460, 237, "CV")
            self._arrow(canvas, 380, 162, 460, 132, "BC")
        else:
            self._box(canvas, x, 280, 150, 65, "APP MOBILE", ["Usuário abre o app", "e informa a empresa"], BLUE, BLUE_BORDER)
            self._box(canvas, x + 230, 280, 150, 65, "LOGIN DA API", ["company_code + login", "+ senha"], YELLOW, YELLOW_BORDER)
            self._box(canvas, x + 460, 280, 150, 65, "REGISTRO CENTRAL", ["Código -> cliente", "cliente -> banco"], GREEN, GREEN_BORDER)
            self._arrow(canvas, 150, 312, 230, 312, "HTTPS")
            self._arrow(canvas, 380, 312, 460, 312, "consulta")
            self._box(canvas, x + 230, 130, 150, 65, "JWT", ["Inclui tenant_id", "e expiração"], YELLOW, YELLOW_BORDER)
            self._box(canvas, x + 460, 205, 150, 65, "BANCO CV", ["company_code: cv", "cv_financeiro"], BLUE, BLUE_BORDER)
            self._box(canvas, x + 460, 100, 150, 65, "BANCO BC", ["company_code: bc", "bc_financeiro"], ROSE, ROSE_BORDER)
            self._arrow(canvas, 305, 280, 305, 195, "retorna token")
            self._arrow(canvas, 380, 162, 460, 237, "código CV")
            self._arrow(canvas, 380, 162, 460, 132, "código BC")
        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica-Oblique", 8)
        canvas.drawString(0, 28, "A API decide a conexão. O frontend e o app nunca recebem credenciais nem nome do banco.")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D9E0E5"))
    canvas.line(2 * cm, 1.45 * cm, A4[0] - 2 * cm, 1.45 * cm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2 * cm, 0.95 * cm, "VSTEC • Arquitetura multicliente com banco por tenant")
    canvas.drawRightString(A4[0] - 2 * cm, 0.95 * cm, f"Página {doc.page}")
    canvas.restoreState()


def build_pdf():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm, topMargin=1.7 * cm, bottomMargin=2 * cm
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("TitleCustom", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=23, leading=28, textColor=NAVY, spaceAfter=8)
    subtitle = ParagraphStyle("SubtitleCustom", parent=styles["BodyText"], fontSize=11, leading=16, textColor=MUTED, spaceAfter=18)
    h2 = ParagraphStyle("H2Custom", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=NAVY, spaceBefore=8, spaceAfter=8)
    body = ParagraphStyle("BodyCustom", parent=styles["BodyText"], fontSize=10.2, leading=15, textColor=TEXT, spaceAfter=8)
    note = ParagraphStyle("NoteCustom", parent=body, backColor=colors.HexColor("#F3F7FA"), borderColor=colors.HexColor("#D6E1E8"), borderWidth=0.7, borderPadding=10, spaceBefore=8, spaceAfter=12)

    story = [
        Paragraph("Arquitetura multicliente", title),
        Paragraph("Banco de dados separado por empresa • resolução segura de conexão por domínio no Frontend e por código da empresa no App", subtitle),
        Paragraph("Objetivo", h2),
        Paragraph("Cada cliente terá seu próprio banco de dados. A aplicação continua sendo uma só, mas a API identifica a empresa antes de consultar qualquer dado e abre uma sessão SQLAlchemy ligada somente ao banco daquele cliente.", body),
        Paragraph("Regra principal: o navegador e o aplicativo não escolhem o nome do banco. Eles apresentam uma identificação de empresa; o backend, usando um cadastro central controlado pela VSTEC, decide qual banco pode ser acessado.", note),
        Paragraph("1. Acesso pelo Frontend: domínio identifica a empresa", h2),
        ArchitectureDiagram("front"),
        Paragraph("Exemplos de domínio", h2),
    ]
    domain_rows = [
        ["Endereço no navegador", "Tenant / empresa", "Banco que a API seleciona"],
        ["https://cvfinanceiro.vstec.net", "CV Financeiro", "cv_financeiro"],
        ["https://bcfinanceiro.vstec.net", "BC Financeiro", "bc_financeiro"],
    ]
    domain_table = Table(domain_rows, colWidths=[6.2 * cm, 4.1 * cm, 4.9 * cm])
    domain_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9), ("LEADING", (0, 0), (-1, -1), 12),
        ("BACKGROUND", (0, 1), (-1, 1), BLUE), ("BACKGROUND", (0, 2), (-1, 2), ROSE),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7D3DB")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [domain_table, PageBreak(), Paragraph("2. Acesso pelo App: código da empresa identifica o tenant", h2), ArchitectureDiagram("app")]
    app_rows = [
        ["Código informado no app", "Empresa", "Banco selecionado"],
        ["cv", "CV Financeiro", "cv_financeiro"],
        ["bc", "BC Financeiro", "bc_financeiro"],
    ]
    app_table = Table(app_rows, colWidths=[5.2 * cm, 5 * cm, 5 * cm])
    app_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 1), (-1, 1), BLUE), ("BACKGROUND", (0, 2), (-1, 2), ROSE),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7D3DB")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [Spacer(1, 6), app_table, Paragraph("Fluxo de login no app", h2)]
    steps = [
        ["1", "O usuário informa o código da empresa, por exemplo <b>cv</b> ou <b>bc</b>."],
        ["2", "O app envia <b>company_code</b>, login e senha para um endpoint de login da API."],
        ["3", "O resolvedor consulta o cadastro central, abre a conexão do banco correto e valida o usuário nesse banco."],
        ["4", "A API devolve um JWT contendo o identificador interno do tenant (<b>tenant_id</b>)."],
        ["5", "Nas demais requisições, a API confere o tenant do JWT e usa somente a conexão daquele tenant."],
    ]
    steps_table = Table(steps, colWidths=[1 * cm, 14.2 * cm], hAlign="LEFT")
    steps_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), YELLOW), ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#D6DEE4")), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story += [steps_table, Paragraph("3. Cadastro central e regras de segurança", h2)]
    story += [Paragraph("O cadastro central é um banco administrativo pequeno. Ele não armazena contratos ou clientes; apenas controla qual empresa está ativa, seus domínios, seus códigos e a referência segura para sua conexão. As senhas de banco não podem ficar no app, no frontend nem em texto aberto no cadastro.", body)]
    security_rows = [
        ["Situação", "Comportamento esperado da API"],
        ["Domínio desconhecido", "Bloqueia a requisição com “empresa não encontrada”."],
        ["Código de empresa inexistente", "Não inicia login e não revela detalhes internos."],
        ["Token da CV usado para tentar acessar BC", "Bloqueia: o tenant do JWT não corresponde ao tenant resolvido."],
        ["Cliente inativo", "Bloqueia novos acessos, mesmo que o domínio exista."],
    ]
    security_table = Table(security_rows, colWidths=[5.1 * cm, 10.1 * cm])
    security_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7FAFC")), ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#D6DEE4")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [security_table, Paragraph("Resumo da decisão", h2), Paragraph("No Frontend, o domínio é a identificação principal: <b>cvfinanceiro.vstec.net</b> e <b>bcfinanceiro.vstec.net</b>. No App, o código da empresa é informado no login: <b>cv</b> ou <b>bc</b>. Nos dois casos, somente o backend resolve e abre a conexão do banco correspondente.", note)]
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    build_pdf()
