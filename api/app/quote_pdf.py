"""Customer-facing full quote. Prices arrive from the same commercial calculation as the screen."""
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path
from uuid import UUID
from xml.sax.saxutils import escape

from pydantic import BaseModel, Field, FiniteFloat
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .production_images import ImageSelector, image_metadata, model_identity
from .production_schemas import TechnicalInput


class QuoteLine(BaseModel):
    technical: TechnicalInput
    label: str = Field(max_length=100)
    finish: str = Field(pattern=r"^(BRANCO|PRETO)$")
    unit: FiniteFloat
    total: FiniteFloat


class QuotePdf(BaseModel):
    company_id: UUID
    number: str = Field(max_length=300)
    client: str = Field(max_length=200)
    client_code: str = Field(default="", max_length=100)
    work_code: str = Field(default="", max_length=100)
    phone: str = Field(default="", max_length=300)
    city: str = Field(default="", max_length=300)
    project: str = Field(default="", max_length=300)
    date: str = Field(default="", max_length=40)
    notes: str = Field(default="", max_length=5000)
    payment: str = Field(default="", max_length=500)
    delivery: str = Field(default="", max_length=500)
    validity: str = Field(default="", max_length=500)
    installation: FiniteFloat
    lines: list[QuoteLine] = Field(min_length=1, max_length=51)


def money(value):
    amount = Decimal(str(value)).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
    return "R$ " + format(amount, ",.2f").translate(str.maketrans(",.", ".,"))


def sketch(store, directory, company, key, finish, basename):
    selector = ImageSelector(kind="MODEL_SKETCH", model_key=key, finish_key=finish)
    if store:
        match = store.resolve(selector, company)
        if match.status == "VERIFIED":
            entry = next(e for e in store.manifest.entries if e.selector == selector)
            return store.read_verified(entry)
    if directory and basename:
        root = Path(directory).resolve()
        path = (root / basename).resolve()
        if path.parent == root and path.is_file() and path.stat().st_size <= 20_000_000:
            raw = path.read_bytes()
            image_metadata(raw)
            return raw
    return None


def render_quote(payload, store=None, directory=None):
    stream = BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=A4, leftMargin=17*mm, rightMargin=17*mm,
                            topMargin=17*mm, bottomMargin=19*mm, title="Orçamento completo")
    ink = colors.HexColor("#20384a")
    def paragraph(value, size=10, bold=False):
        style = ParagraphStyle("quote", fontName="Helvetica-Bold" if bold else "Helvetica",
                               fontSize=size, leading=size+4, textColor=ink)
        return Paragraph(escape(str(value)).replace("\n", "<br/>"), style)

    def table(rows, widths):
        block = Table(rows, colWidths=[v*mm for v in widths], hAlign="LEFT")
        block.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                   ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9eff2")),
                                   ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#c7d3db")),
                                   ("TOPPADDING", (0, 0), (-1, -1), 5),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        return block

    story = [PageBreak(), paragraph("Orçamento completo", 21, True), paragraph("   |   ".join(filter(None, [f"Nº {payload.number}", payload.date]))),
             Spacer(1, 10), paragraph(payload.client, 14, True)]
    for label, value in [("Código do cliente", payload.client_code), ("Telefone", payload.phone), ("Cidade", payload.city), ("Obra", payload.project), ("Código da obra", payload.work_code)]:
        if value:
            story.append(paragraph(f"{label}: {value}"))
    story.append(Spacer(1, 12))
    missing = []
    for index, row in enumerate(payload.lines, 1):
        item = row.technical.model_dump(mode="json")
        key, basename = model_identity(item, row.finish)
        raw = sketch(store, directory, payload.company_id, key, row.finish, basename)
        if raw:
            picture = Image(BytesIO(raw))
            picture._restrictSize(51*mm, 40*mm)
        else:
            missing.append(index)
            picture = paragraph("Croqui indisponível", 9)
        details = [paragraph(basename[:-4], 11, True)]
        fields = [("Vidro(s)", item.get("glass_description")), ("Acab. interno", item.get("internal_finish")),
                  ("Acab. externo", item.get("external_finish")), ("Fechamento", item.get("closure_mode")),
                  ("Persiana", (item.get("shutter") or {}).get("mode"))]
        for label, value in fields:
            if value:
                details.append(paragraph(f"{label}: {value}", 9))
        specs = [f"{item['width_mm']:g} mm", f"{item['height_mm']:g} mm", item['quantity'], money(row.unit), money(row.total)]
        story.append(KeepTogether([paragraph(f"Item {row.label}", 12, True), Spacer(1, 4),
            table([[details, picture]], [119, 55]),
            table([[paragraph(t, 9, True) for t in ("Largura", "Altura", "Quantidade", "Valor unitário", "Valor total")],
                   [paragraph(t, 10) for t in specs]], [32, 32, 30, 40, 40]), Spacer(1, 12)]))
    subtotal = sum(line.total for line in payload.lines)
    totals = [("Esquadrias", subtotal), ("Instalação", payload.installation), ("Total do orçamento", subtotal + payload.installation)]
    story.append(KeepTogether([table([[paragraph(k, 11, True), paragraph(money(v), 11, True)] for k, v in totals], [119, 55])]))
    for label, value in [("Condições de pagamento", payload.payment), ("Prazo de entrega", payload.delivery),
                         ("Validade", payload.validity), ("Observações", payload.notes)]:
        if value:
            story.extend([Spacer(1, 6), paragraph(label, 10, True), paragraph(value)])
    def footer(canvas, document):
        canvas.setFont("Helvetica", 8)
        canvas.drawString(17*mm, 10*mm, "Croquis ilustrativos, sem escala.")
        canvas.drawRightString(193*mm, 10*mm, f"Página {document.page}")
    def cover(canvas, document):
        image = Path(__file__).parent / "assets" / "fenster-apresentacao.jpg"
        canvas.drawImage(str(image), 18, A4[1] - 28 - 739, width=552, height=739)

    doc.build(story, onFirstPage=cover, onLaterPages=footer)
    return stream.getvalue(), missing
