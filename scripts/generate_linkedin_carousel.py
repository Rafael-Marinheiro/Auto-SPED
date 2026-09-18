"""Gera o carrossel público do Auto-SPED para publicação no LinkedIn."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from reportlab.lib.colors import Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "Auto-SPED_LinkedIn_Carrossel.pdf"
WIDTH = 576
HEIGHT = 720

NAVY = HexColor("#071A2B")
NAVY_2 = HexColor("#0B263D")
TEAL = HexColor("#19D3A2")
TEAL_DARK = HexColor("#0B9F7B")
GOLD = HexColor("#F4C95D")
WHITE = HexColor("#F7FBFA")
MUTED = HexColor("#A9BBC8")
INK = HexColor("#102A3A")
PALE = HexColor("#EAF5F2")
RED = HexColor("#EF6F6C")


def register_fonts() -> tuple[str, str]:
    regular_candidates = (
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    )
    bold_candidates = (
        Path("C:/Windows/Fonts/seguisb.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
    )
    regular = next((path for path in regular_candidates if path.exists()), None)
    bold = next((path for path in bold_candidates if path.exists()), None)
    if regular is None or bold is None:
        return "Helvetica", "Helvetica-Bold"
    pdfmetrics.registerFont(TTFont("AutoSped-Regular", str(regular)))
    pdfmetrics.registerFont(TTFont("AutoSped-Bold", str(bold)))
    return "AutoSped-Regular", "AutoSped-Bold"


FONT, FONT_BOLD = register_fonts()


def rounded_rect(
    canvas: Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    fill: Color,
    radius: float = 14,
    stroke: Color | None = None,
) -> None:
    canvas.setFillColor(fill)
    canvas.setStrokeColor(fill if stroke is None else stroke)
    canvas.roundRect(x, y, width, height, radius, fill=1, stroke=1 if stroke else 0)


def wrap_text(text: str, font: str, size: float, max_width: float) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if pdfmetrics.stringWidth(candidate, font, size) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        if not words:
            lines.append("")
    return lines


def draw_text(
    canvas: Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    size: float = 18,
    color: Color = WHITE,
    bold: bool = False,
    leading: float | None = None,
) -> float:
    font = FONT_BOLD if bold else FONT
    line_height = leading or size * 1.28
    canvas.setFont(font, size)
    canvas.setFillColor(color)
    for line in wrap_text(text, font, size, max_width):
        canvas.drawString(x, y, line)
        y -= line_height
    return y


def bullet_list(
    canvas: Canvas,
    items: Iterable[str],
    x: float,
    y: float,
    width: float,
    size: float = 17,
    gap: float = 13,
    bullet_color: Color = TEAL,
) -> float:
    for item in items:
        lines = wrap_text(item, FONT, size, width - 26)
        canvas.setFillColor(bullet_color)
        canvas.circle(x + 5, y + 5, 4, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont(FONT, size)
        for line in lines:
            canvas.drawString(x + 22, y, line)
            y -= size * 1.25
        y -= gap
    return y


def base_page(canvas: Canvas, page: int, label: str) -> None:
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, WIDTH, HEIGHT, fill=1, stroke=0)
    canvas.setFillColor(TEAL)
    canvas.rect(0, HEIGHT - 8, WIDTH, 8, fill=1, stroke=0)
    canvas.setFont(FONT_BOLD, 11)
    canvas.setFillColor(MUTED)
    canvas.drawString(36, 29, f"AUTO-SPED  /  {label.upper()}")
    canvas.drawRightString(WIDTH - 36, 29, f"{page:02d} / 08")


def title(canvas: Canvas, kicker: str, heading: str, body: str = "") -> float:
    canvas.setFont(FONT_BOLD, 13)
    canvas.setFillColor(TEAL)
    canvas.drawString(36, 657, kicker.upper())
    y = draw_text(canvas, heading, 36, 622, 504, size=34, bold=True, leading=39)
    if body:
        y -= 11
        y = draw_text(canvas, body, 36, y, 500, size=16, color=MUTED, leading=22)
    return y


def page_cover(canvas: Canvas) -> None:
    base_page(canvas, 1, "Portfólio")
    canvas.setFillColor(TEAL)
    canvas.circle(485, 592, 88, fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.setFont(FONT_BOLD, 28)
    canvas.drawCentredString(485, 582, "SPED")
    canvas.setFillColor(GOLD)
    canvas.circle(439, 537, 18, fill=1, stroke=0)
    canvas.setFont(FONT_BOLD, 16)
    canvas.setFillColor(TEAL)
    canvas.drawString(36, 625, "PROJETO OPEN SOURCE")
    draw_text(canvas, "Auto-SPED", 36, 545, 430, size=58, bold=True, leading=60)
    draw_text(
        canvas,
        "Do ERP ao arquivo fiscal com rastreabilidade, validação e arquitetura reutilizável.",
        36,
        458,
        470,
        size=23,
        leading=31,
    )
    rounded_rect(canvas, 36, 210, 504, 132, NAVY_2, stroke=TEAL_DARK)
    draw_text(canvas, "EFD ICMS/IPI", 58, 304, 210, size=18, bold=True, color=GOLD)
    draw_text(
        canvas,
        "Python  |  Firebird  |  Desktop  |  CLI  |  Conectores",
        58,
        265,
        445,
        size=17,
    )
    draw_text(canvas, "Rafael Marinheiro", 58, 225, 300, size=15, color=MUTED)


def page_problem(canvas: Canvas) -> None:
    base_page(canvas, 2, "Problema")
    y = title(
        canvas,
        "O ponto de partida",
        "Uma necessidade mensal virou engenharia de produto.",
        "A emissão precisava continuar funcionando enquanto a solução evoluía.",
    )
    y -= 30
    bullet_list(
        canvas,
        (
            "Muitos documentos e itens vindos de um ERP com Firebird.",
            "Erros de CST, quantidade, preço, totais e documentos só apareciam tarde no PVA.",
            "Versão e arquitetura do cliente Firebird podiam bloquear a conexão.",
            "Alterar o gerador sem preservar o resultado homologado criaria risco operacional.",
        ),
        42,
        y,
        490,
    )
    rounded_rect(canvas, 36, 76, 504, 90, TEAL)
    draw_text(
        canvas,
        "Objetivo: automatizar sem perder controle, explicação ou confiança.",
        58,
        132,
        460,
        size=20,
        color=NAVY,
        bold=True,
        leading=25,
    )


def flow_box(canvas: Canvas, x: float, y: float, width: float, label: str, note: str) -> None:
    rounded_rect(canvas, x, y, width, 82, NAVY_2, stroke=TEAL_DARK)
    draw_text(canvas, label, x + 14, y + 54, width - 28, size=15, bold=True)
    draw_text(canvas, note, x + 14, y + 29, width - 28, size=11, color=MUTED, leading=14)


def page_architecture(canvas: Canvas) -> None:
    base_page(canvas, 3, "Arquitetura")
    title(
        canvas,
        "Separação de responsabilidades",
        "Uma lógica fiscal. Várias fontes de dados.",
        "Cada ERP implementa um capturador; o núcleo permanece independente.",
    )
    flow_box(canvas, 36, 420, 132, "1. Fonte", "Firebird, PostgreSQL, XML ou CSV")
    flow_box(canvas, 194, 420, 132, "2. Capturador", "Traduz a origem para o contrato fiscal")
    flow_box(canvas, 352, 420, 188, "3. Núcleo fiscal", "Normaliza, valida e gera os registros")
    canvas.setStrokeColor(TEAL)
    canvas.setLineWidth(3)
    for start, end in ((168, 194), (326, 352)):
        canvas.line(start + 5, 461, end - 5, 461)
        canvas.line(end - 13, 467, end - 5, 461)
        canvas.line(end - 13, 455, end - 5, 461)
    rounded_rect(canvas, 36, 216, 504, 124, PALE)
    draw_text(canvas, "FiscalDataProvider", 58, 305, 210, size=20, bold=True, color=INK)
    draw_text(
        canvas,
        "Contrato estável que desacopla tabelas do ERP, regras fiscais e escritor do SPED.",
        58,
        270,
        455,
        size=16,
        color=INK,
        leading=22,
    )
    draw_text(
        canvas,
        "Resultado: novos conectores sem reescrever o motor de emissão.",
        36,
        150,
        500,
        size=21,
        bold=True,
        color=GOLD,
        leading=27,
    )


def mapping_row(canvas: Canvas, y: float, source: str, entity: str, target: str) -> None:
    rounded_rect(canvas, 36, y, 504, 62, NAVY_2, stroke=TEAL_DARK)
    draw_text(canvas, source, 50, y + 39, 145, size=13, color=MUTED)
    draw_text(canvas, entity, 210, y + 39, 150, size=13, bold=True)
    draw_text(canvas, target, 404, y + 39, 120, size=13, bold=True, color=TEAL)
    canvas.setStrokeColor(MUTED)
    canvas.setLineWidth(1.5)
    canvas.line(176, y + 31, 198, y + 31)
    canvas.line(370, y + 31, 392, y + 31)


def page_mapping(canvas: Canvas) -> None:
    base_page(canvas, 4, "Mapa de captura")
    title(
        canvas,
        "Rastreabilidade",
        "Cada campo mostra de onde veio e onde será usado.",
        "O mapa de captura reduz tentativa e erro ao adaptar outro ERP.",
    )
    canvas.setFont(FONT_BOLD, 11)
    canvas.setFillColor(MUTED)
    canvas.drawString(50, 477, "ORIGEM")
    canvas.drawString(210, 477, "ENTIDADE FISCAL")
    canvas.drawString(404, 477, "REGISTRO")
    mapping_row(canvas, 397, "EMPRESA", "Dados cadastrais", "0000")
    mapping_row(canvas, 321, "CLIENTES / FORN.", "Participantes", "0150")
    mapping_row(canvas, 245, "PRODUTOS", "Itens e unidades", "0190 / 0200")
    mapping_row(canvas, 169, "NF-E / NFC-E", "Documento fiscal", "C100")
    mapping_row(canvas, 93, "ITENS / TRIBUTOS", "Detalhes e totalização", "C170 / C190")


def page_validation(canvas: Canvas) -> None:
    base_page(canvas, 5, "Validação")
    y = title(
        canvas,
        "Antes do PVA",
        "Erros são tratados o mais perto possível da origem.",
        "A ferramenta mostra o registro afetado, a causa e a ação sugerida.",
    )
    y -= 23
    cards = (
        ("01", "Prévia", "Resumo da empresa, documentos, itens e totais."),
        ("02", "Validação", "CST, CFOP, NCM, unidade, duplicidade e contadores."),
        ("03", "Geração", "Escrita decimal precisa e leiaute pela competência."),
        ("04", "Conferência", "Validação estrutural do TXT antes do PVA."),
    )
    for index, (number, heading, note) in enumerate(cards):
        row, col = divmod(index, 2)
        x = 36 + col * 258
        card_y = y - 137 - row * 150
        rounded_rect(canvas, x, card_y, 246, 124, NAVY_2, stroke=TEAL_DARK)
        canvas.setFillColor(TEAL)
        canvas.circle(x + 31, card_y + 90, 18, fill=1, stroke=0)
        canvas.setFillColor(NAVY)
        canvas.setFont(FONT_BOLD, 11)
        canvas.drawCentredString(x + 31, card_y + 86, number)
        draw_text(canvas, heading, x + 59, card_y + 98, 168, size=17, bold=True)
        draw_text(canvas, note, x + 18, card_y + 61, 210, size=13, color=MUTED, leading=17)


def page_safety(canvas: Canvas) -> None:
    base_page(canvas, 6, "Segurança")
    title(
        canvas,
        "Correções controladas",
        "ACID aplicado às alterações no banco.",
        "O padrão é somente leitura. Qualquer escrita exige revisão e confirmação.",
    )
    steps = (
        ("A", "Atomicidade", "Falhou? rollback de todo o plano."),
        ("C", "Consistência", "Pré-condição e validação após a mudança."),
        ("I", "Isolamento", "Uma operação por fonte e período."),
        ("D", "Durabilidade", "Commit acompanhado de recibo e auditoria."),
    )
    y = 448
    for letter, heading, note in steps:
        canvas.setFillColor(TEAL)
        canvas.circle(68, y + 20, 24, fill=1, stroke=0)
        canvas.setFillColor(NAVY)
        canvas.setFont(FONT_BOLD, 19)
        canvas.drawCentredString(68, y + 13, letter)
        draw_text(canvas, heading, 110, y + 34, 170, size=17, bold=True)
        draw_text(canvas, note, 110, y + 8, 410, size=14, color=MUTED)
        y -= 86
    rounded_rect(canvas, 36, 71, 504, 72, NAVY_2, stroke=RED)
    draw_text(
        canvas,
        "Nenhuma correção é aplicada automaticamente.",
        58,
        111,
        460,
        size=18,
        bold=True,
    )


def page_quality(canvas: Canvas) -> None:
    base_page(canvas, 7, "Qualidade")
    y = title(
        canvas,
        "Produto, não script isolado",
        "Engenharia para evoluir sem interromper a emissão mensal.",
    )
    y -= 32
    bullet_list(
        canvas,
        (
            "Testes de paridade preservam o fluxo homologado do DADOS.FDB.",
            "Suíte automatizada em Python 3.10, 3.11 e 3.12.",
            "Lint, tipagem estática e integração contínua no GitHub Actions.",
            "Interface desktop, CLI, instalador Windows e histórico local.",
            "Seletor de cliente Firebird por versão e arquitetura.",
            "Exemplos anonimizados e política para proteger dados fiscais.",
        ),
        42,
        y,
        490,
        size=16,
        gap=10,
        bullet_color=GOLD,
    )
    rounded_rect(canvas, 36, 73, 504, 72, PALE)
    draw_text(canvas, "Licença MIT", 57, 117, 140, size=18, bold=True, color=INK)
    draw_text(canvas, "Estude, adapte e crie seu conector.", 196, 117, 320, size=16, color=INK)


def page_cta(canvas: Canvas) -> None:
    base_page(canvas, 8, "Colaboração")
    canvas.setFillColor(TEAL)
    canvas.circle(288, 575, 62, fill=1, stroke=0)
    canvas.setFillColor(NAVY)
    canvas.setFont(FONT_BOLD, 25)
    canvas.drawCentredString(288, 566, "</>")
    draw_text(
        canvas,
        "Seu ERP também precisa gerar SPED?",
        48,
        466,
        480,
        size=35,
        bold=True,
        leading=42,
    )
    draw_text(
        canvas,
        "Aproveite o núcleo fiscal e implemente apenas o capturador da sua fonte de dados.",
        48,
        354,
        480,
        size=20,
        color=MUTED,
        leading=28,
    )
    rounded_rect(canvas, 48, 191, 480, 92, TEAL)
    draw_text(canvas, "github.com/Rafael-Marinheiro/Auto-SPED", 70, 245, 440, size=18, bold=True, color=NAVY)
    draw_text(canvas, "Open source  |  MIT  |  Contribuições bem-vindas", 70, 214, 440, size=14, color=INK)
    draw_text(canvas, "Rafael Marinheiro", 48, 122, 300, size=18, bold=True)
    draw_text(canvas, "Python  -  Integração fiscal  -  Engenharia de software", 48, 91, 465, size=14, color=MUTED)


def build() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas = Canvas(str(OUTPUT), pagesize=(WIDTH, HEIGHT), pageCompression=1)
    canvas.setTitle("Auto-SPED - do ERP ao arquivo fiscal")
    canvas.setAuthor("Rafael Marinheiro")
    canvas.setSubject("Portfólio de engenharia de software e integração fiscal")
    for page in (
        page_cover,
        page_problem,
        page_architecture,
        page_mapping,
        page_validation,
        page_safety,
        page_quality,
        page_cta,
    ):
        page(canvas)
        canvas.showPage()
    canvas.save()
    return OUTPUT


if __name__ == "__main__":
    print(build())
