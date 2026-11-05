"""A4 review PDFs from immutable B1 layouts. No engineering recalculation.

There is deliberately no manufacturing release in B2. Every physical page is
marked for review; missing assets are text findings, never substitute drawings.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
from io import BytesIO
from pathlib import Path
import re
from threading import Lock
from typing import Literal

import reportlab
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from pydantic import Field

from .production_images import ProductionImageStore, model_identity
from .production_layout import ProductionLayoutDocument, ProductionLayoutRequest
from .production_schemas import OPModel
from .production_service import canonical_json

PDF_RENDERER_VERSION = "OP_PDF_B2_0.1.0"
REVIEW_LABEL = "CONFERÊNCIA — NÃO FABRICAR"
_LOCK = Lock()
_FONT = "OPVera"
_BOLD = "OPVeraBold"
_PATH = re.compile(r"(?i)(?:\b[a-z]:[\\/]|file://|\\\\[^\s\\]+\\)[^\r\n]*")
_UNITS = {"piece": "un", "run": "conj.", "unresolved": "unid. pendente", "consumption_factor": "fator de consumo"}
_GEOMETRY = json.loads((Path(__file__).parent / "data/op_pdf_geometry_v1.json").read_text(encoding="utf-8"))
_GEOMETRY_SHA = hashlib.sha256(canonical_json(_GEOMETRY).encode("utf-8")).hexdigest()


class ProductionPdfRequest(OPModel):
    layout_request: ProductionLayoutRequest
    purpose: Literal["REVIEW", "PRODUCTION"] = "REVIEW"


class PdfBlocker(OPModel):
    code: str
    item_id: str | None = None
    engine_position: int | None = None
    message: str


class ProductionPdfReadiness(OPModel):
    review_allowed: bool = True
    fabrication_allowed: Literal[False] = False
    layout_sha256: str
    blockers: tuple[PdfBlocker, ...]


class PdfReviewNote(OPModel):
    item_id: str
    classification: str
    message: str


class PdfModelHeading(OPModel):
    item_id: str
    model_key: str
    description: str = Field(min_length=1)


class PdfCellTrace(OPModel):
    text: str
    bbox: tuple[float, float, float, float]


class PdfRowFragment(OPModel):
    item_id: str
    engine_position: int
    print_position: int
    page_number: int
    fragment: int
    cells: tuple[PdfCellTrace, ...]


class PdfPageTrace(OPModel):
    page_number: int
    item_id: str
    kind: Literal["TABLE", "FINDINGS"]


class PdfImageTrace(OPModel):
    page_number: int
    item_id: str
    sha256: str
    bbox: tuple[float, float, float, float]


class ProductionPdfAudit(OPModel):
    renderer_version: str = PDF_RENDERER_VERSION
    reference_geometry_sha256: str = _GEOMETRY_SHA
    layout_sha256: str
    pdf_sha256: str
    review_notes_sha256: str
    model_headings_sha256: str
    page_count: int
    row_count: int
    rows: tuple[PdfRowFragment, ...]
    pages: tuple[PdfPageTrace, ...]
    images: tuple[PdfImageTrace, ...]
    readiness: ProductionPdfReadiness


@dataclass(frozen=True)
class ProductionPdfResult:
    """Private PDF bytes and independent-inspector trace; no filesystem side effect."""
    content: bytes
    audit: ProductionPdfAudit


def pdf_number(value: float | int | None) -> str:
    """Decimal text without rounding, locale ambiguity or scientific notation."""
    if value is None:
        return "—"
    number = Decimal(str(value))
    if not number.is_finite():
        raise ValueError("Número técnico não finito no PDF.")
    result = format(number, "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return result.replace(".", ",")


def printable_text(value: object) -> str:
    """Omit local paths and isolated legacy sentinels; do not evaluate markup."""
    text = "" if value is None else str(value)
    text = _PATH.sub("[caminho local omitido]", text)
    text = "".join(char for char in text if ord(char) >= 32 or char == "\n")
    return "[resíduo legado omitido]" if text.strip() == "A" else text


def _ensure_fonts():
    with _LOCK:
        if _FONT not in pdfmetrics.getRegisteredFontNames():
            folder = Path(reportlab.__file__).parent / "fonts"
            pdfmetrics.registerFont(TTFont(_FONT, str(folder / "Vera.ttf")))
            pdfmetrics.registerFont(TTFont(_BOLD, str(folder / "VeraBd.ttf")))


def _validate_layout(layout):
    expected = hashlib.sha256(canonical_json(layout.model_dump(mode="json", exclude={"layout_sha256"})).encode("utf-8")).hexdigest()
    if expected != layout.layout_sha256:
        raise ValueError("Snapshot de apresentação alterado; hash inválido.")
    ids = [page.item_id for page in layout.pages]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("Plano exige itens únicos e não vazios.")
    for page in layout.pages:
        positions = [row.engine_position for block in page.blocks for row in block.rows]
        prints = [row.print_position for block in page.blocks for row in block.rows]
        if len(set(positions)) != len(positions) or prints != list(range(1, len(prints) + 1)):
            raise ValueError("Linhas do plano possuem identidade/ordem inválida.")


def _image_bytes(reference, store, company_id):
    if reference is None or reference.status != "VERIFIED" or reference.selector is None or store is None:
        return None
    actual = store.resolve(reference.selector, company_id)
    if actual != reference:
        return None
    entry = next((entry for entry in store.manifest.entries if entry.sha256 == actual.sha256 and entry.relative_path == actual.relative_path), None)
    if entry is None:
        return None
    try:
        return store.read_verified(entry)
    except (OSError, ValueError):
        return None


def _prepare(layout, store):
    _validate_layout(layout)
    if store is not None:
        if store.manifest.company_id != layout.company_id:
            raise ValueError("Imagens de outra empresa.")
        digest = hashlib.sha256(canonical_json(store.manifest.model_dump(mode="json")).encode("utf-8")).hexdigest()
        if digest != layout.asset_manifest_sha256:
            raise ValueError("Manifest difere do snapshot; reconstruir apresentação explicitamente.")
    blockers = [PdfBlocker(code="INDEPENDENT_DOCUMENT_AUDIT_PENDING", message="Documento de conferência; emissão para fabricação não foi autorizada.")]
    images = {}
    for page in layout.pages:
        for finding in page.findings:
            blockers.append(PdfBlocker(code=finding.code, item_id=page.item_id,
                                      engine_position=finding.engine_position, message=printable_text(finding.message)))
        references = [page.model_image, page.frame_section, page.leaf_section]
        references += [row.profile_image for block in page.blocks for row in block.rows]
        for reference in references:
            if reference is None:
                continue
            key = canonical_json(reference.model_dump(mode="json"))
            data = _image_bytes(reference, store, layout.company_id)
            images[key] = data
            if data is None:
                blockers.append(PdfBlocker(code="MISSING_OR_INVALID_PDF_ASSET", item_id=page.item_id,
                                          message="Imagem não disponível/verificada para este modelo, código e acabamento."))
        text_fields = [page.model_description, *page.header.model_dump().values()]
        for block in page.blocks:
            for row in block.rows:
                text_fields += [row.utilization_label, row.technical.description, row.technical.code]
        if any(value is not None and printable_text(value) != str(value) for value in text_fields):
            blockers.append(PdfBlocker(code="LEGACY_TEXT_REDACTED", item_id=page.item_id,
                                      message="Caminho local/caractere residual omitido na impressão; revisar dado original."))
    unique = {canonical_json(b.model_dump(mode="json")): b for b in blockers}
    readiness = ProductionPdfReadiness(layout_sha256=layout.layout_sha256, blockers=tuple(unique.values()))
    return readiness, images


def production_pdf_readiness(layout: ProductionLayoutDocument, *, image_store: ProductionImageStore | None = None) -> ProductionPdfReadiness:
    """Return non-bypassable document/audit blockers; never grants manufacturing."""
    return _prepare(layout, image_store)[0]


def pdf_model_headings(request: ProductionLayoutRequest) -> tuple[PdfModelHeading, ...]:
    """Use B1's image/model naming, independently of engineering descriptions."""
    headings = []
    for item in request.production_order.items:
        key, basename = model_identity(item.technical_input.model_dump(mode="json"), item.finish_key)
        if basename is not None:
            headings.append(PdfModelHeading(item_id=item.item_id, model_key=key, description=basename[:-4]))
    return tuple(headings)


def _wrap(text, width, font, size):
    text = printable_text(text)
    glyphs = pdfmetrics.getFont(font).face.charToGlyph
    if any(ord(char) not in glyphs for char in text if char != "\n"):
        raise ValueError("Texto contém glifo sem suporte na fonte incorporada; fornecer fonte adequada antes de emitir.")
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split():
            if current and pdfmetrics.stringWidth(current + " " + word, font, size) <= width:
                current += " " + word
                continue
            if current:
                lines.append(current)
                current = ""
            while word and pdfmetrics.stringWidth(word, font, size) > width:
                count = 1
                while count < len(word) and pdfmetrics.stringWidth(word[:count + 1], font, size) <= width:
                    count += 1
                lines.append(word[:count])
                word = word[count:]
            current = word
        lines.append(current)
    return lines or [""]


def _row_cells(row):
    t = row.technical
    label = row.utilization_label if row.utilization_label is not None else ("" if row.legacy_row is not None else t.utilization)
    description = t.description or "[sem descrição]"
    code = t.code if t.code is not None else "[sem código]"
    quantity = pdf_number(t.quantity_total) + " " + _UNITS[t.quantity_unit]
    if (t.quantity_per_unit, t.quantity_total) != (t.bom_quantity_per_unit, t.bom_quantity_total):
        description += f"\nFator BOM: {pdf_number(t.bom_quantity_per_unit)}/esq.; {pdf_number(t.bom_quantity_total)} total."
    if t.quantity_unit == "unresolved":
        description += f"\nUnidade física pendente; unidade de catálogo: {t.material_unit or 'ausente'}."
    has_surface = t.width_mm is not None or t.height_mm is not None
    has_length = t.final_length_mm is not None or t.cut_length_mm is not None
    kind = "SURFACES" if has_surface and not has_length else "CUTS" if has_length else "UNITS"
    if kind == "SURFACES":
        a, b = pdf_number(t.width_mm), pdf_number(t.height_mm)
    elif kind == "CUTS":
        a, b = pdf_number(t.final_length_mm), pdf_number(t.cut_length_mm)
        if has_surface:
            description += f"\nLargura/altura: {pdf_number(t.width_mm)} × {pdf_number(t.height_mm)} mm."
    else:
        a, b = "", ""
    return kind, tuple(printable_text(v) for v in (label, "", description, code, a, b, quantity))


class _Renderer:
    widths = (92, 40, 187, 58, 54, 54, 74)
    left = 18
    bottom = 42
    size = 6.0
    leading = 7.3

    def __init__(self, layout, readiness, images, review_notes, model_headings):
        self.layout, self.readiness, self.image_data = layout, readiness, images
        self.review_notes = review_notes
        self.titles = {heading.item_id: heading.description for heading in model_headings}
        self.buffer = BytesIO()
        self.canvas = Canvas(self.buffer, pagesize=A4, pageCompression=1, invariant=1)
        self.canvas.setTitle("Ordem de Produção — Conferência B2")
        self.canvas.setAuthor("Software Esquadrias")
        self.canvas.setCreator(PDF_RENDERER_VERSION)
        self.pages, self.rows, self.images = [], [], []
        self.page_number = 0
        self.y = 0

    def text(self, x, y, text, size=6.1, bold=False):
        self.canvas.setFont(_BOLD if bold else _FONT, size)
        self.canvas.drawString(x, y, printable_text(text))

    def paragraph(self, text, x, top, width, size=6.1, bold=False):
        font = _BOLD if bold else _FONT
        lines = _wrap(text, width, font, size)
        for n, line in enumerate(lines):
            self.text(x, top - size - n * (size + 1.5), line, size, bold)
        return len(lines) * (size + 1.5)

    def new_page(self, page, kind="TABLE", continuation=False):
        if self.page_number:
            self.canvas.showPage()
        self.page_number += 1
        self.pages.append(PdfPageTrace(page_number=self.page_number, item_id=page.item_id, kind=kind))
        self.text(18, 823, REVIEW_LABEL, 10, True)
        self.text(18, 22, "Conferência B2 — pendências não resolvidas. Não utilizar para fabricação.", 6.4, True)
        self.text(440, 22, f"Página {self.page_number}", 6.4)
        self.text(18, 11, f"Snapshot: {self.layout.layout_sha256[:24]} | {PDF_RENDERER_VERSION}", 5.2)
        if continuation or kind == "FINDINGS":
            self.y = 795
            self.y -= self.paragraph(f"Item {page.header.item_label} — {'Pendências e divergências' if kind == 'FINDINGS' else 'Continuação'}", 18, self.y, 559, 9, True) + 4
            self.y -= self.paragraph(self.titles.get(page.item_id, page.model_description), 18, self.y, 559, 7) + 5
            self.text(18, self.y - 7, f"Largura {pdf_number(page.header.width_mm)} mm | Altura {pdf_number(page.header.height_mm)} mm | Quant. {page.header.quantity}", 7)
            self.y -= 23
            return
        x0, y0, x1, y1 = _GEOMETRY["model_box_top_left_pt"]
        self.image(page, page.model_image, (x0, A4[1] - y1, x1 - x0, y1 - y0), "Croqui não disponível", fit=False)
        self.text(160, 800, "Seção do marco", 6.2, True)
        self.image(page, page.frame_section, (160, 744, 85, 48), "Seção não disponível")
        if page.leaf_section is not None:
            self.text(265, 800, "Seção da folha", 6.2, True)
            self.image(page, page.leaf_section, (265, 744, 85, 48), "Seção não disponível")
        self.text(391, 801, "ORDEM DE PRODUÇÃO", 8.5, True)
        title_height = self.paragraph(f"Pedido {self.layout.order_id}\nItem {page.header.item_label}\nDocumento para auditoria", 391, 789, 180, 7)
        bar_top = min(710, 789 - title_height - 7)
        widths = (60, 275, 52, 62, 62, 48)
        labels = page.header_columns
        values = (page.header.client_code or "[não informado]", page.header.client_name or "[não informado]",
                  page.header.item_label, pdf_number(page.header.width_mm), pdf_number(page.header.height_mm), str(page.header.quantity))
        self.canvas.setFillColorRGB(0, 0, 0)
        self.canvas.rect(18, bar_top - 11, 559, 11, fill=1, stroke=0)
        x = 18
        for width, label in zip(widths, labels):
            self.canvas.setFillColorRGB(1, 1, 1)
            self.text(x + 3, bar_top - 8, label, 6.2)
            x += width
        self.canvas.setFillColorRGB(0, 0, 0)
        x, heights = 18, []
        for width, value in zip(widths, values):
            heights.append(self.paragraph(value, x + 3, bar_top - 14, width - 6, 6.5))
            x += width
        top = bar_top - 15 - max(heights) - 5
        work = "Obra: " + (page.header.work_name or "[não informada]")
        if page.header.work_code:
            work += " | Código: " + page.header.work_code
        top -= self.paragraph(work, 21, top, 553, 6.2) + 5
        title = self.titles.get(page.item_id, page.model_description + (f" ({page.finish_key})" if page.finish_key else ""))
        top -= self.paragraph(title, 21, top, 553, 6.7, True) + 6
        if top < 450:
            raise ValueError("Cabeçalho excede o espaço reservado; revisar os textos antes de gerar PDF.")
        self.y = top

    def image(self, page, reference, box, absent, fit=True):
        if reference is None:
            return
        key = canonical_json(reference.model_dump(mode="json"))
        data = self.image_data.get(key)
        x, y, width, height = box
        if data is None:
            self.paragraph(absent, x + 2, y + height - 2, width - 4, 5.5)
            return
        reader = ImageReader(BytesIO(data))
        original_width, original_height = reader.getSize()
        scale = min(width / original_width, height / original_height)
        w, h = (original_width * scale, original_height * scale) if fit else (width, height)
        dx, dy = x + (width - w) / 2, y + (height - h) / 2
        self.canvas.drawImage(reader, dx, dy, width=w, height=h, mask="auto")
        self.images.append(PdfImageTrace(page_number=self.page_number, item_id=page.item_id,
                                        sha256=reference.sha256, bbox=(dx, dy, dx + w, dy + h)))

    def heading(self, kind, title=None):
        if title:
            self.y -= self.paragraph(title, 20, self.y - 3, 555, 6.1, True) + 5
        labels = ("Utilização", "Perfil", "Descrição", "Código", "Largura (mm)" if kind == "SURFACES" else "Med. Final (mm)" if kind == "CUTS" else "",
                  "Altura (mm)" if kind == "SURFACES" else "Med. Corte (mm)" if kind == "CUTS" else "", "Quant. total")
        self.canvas.setFillColorRGB(0, 0, 0)
        self.canvas.rect(18, self.y - 13, 559, 13, fill=1, stroke=0)
        self.canvas.setFillColorRGB(1, 1, 1)
        x = 18
        for width, label in zip(self.widths, labels):
            self.text(x + 2, self.y - 8.5, label, 5.8)
            x += width
        self.canvas.setFillColorRGB(0, 0, 0)
        self.y -= 16

    def row(self, page, row, kind, cells):
        # Numeric/code cells can use a smaller font, but no value is rounded.
        sizes, wrapped = [], []
        for n, (text, width) in enumerate(zip(cells, self.widths)):
            size = self.size
            if n >= 3:
                longest = max(text.split(), key=lambda word: pdfmetrics.stringWidth(word, _FONT, size), default="")
                while size > 4.7 and pdfmetrics.stringWidth(longest, _FONT, size) > width - 4:
                    size = round(size - 0.1, 1)
            sizes.append(size)
            wrapped.append(_wrap(text, width - 4, _FONT, size))
        offset, fragment = 0, 0
        while offset < max(len(lines) for lines in wrapped):
            minimum = _GEOMETRY["profile_min_row_height_pt"] if row.profile_image is not None and fragment == 0 else 9.3
            if self.y - self.bottom < max(minimum, 12):
                self.new_page(page, continuation=True)
                self.heading(kind)
            capacity = max(1, int((self.y - self.bottom - 4) // self.leading))
            count = min(max(len(lines) for lines in wrapped) - offset, capacity)
            segments = [lines[offset:offset + count] for lines in wrapped]
            if fragment and not any(segments[0]):
                segments[0] = ["Continuação da linha"]
            if fragment and not any(segments[3]) and len(wrapped[3]) <= capacity:
                segments[3] = wrapped[3]
            height = max(minimum, max(len(segment) for segment in segments) * self.leading + 2)
            if height > self.y - self.bottom:
                self.new_page(page, continuation=True)
                self.heading(kind)
                continue
            fragment += 1
            top, x, trace = self.y, self.left, []
            for n, (segment, width, size) in enumerate(zip(segments, self.widths, sizes)):
                for line_number, text in enumerate(segment):
                    self.text(x + 2, top - 1 - size - line_number * self.leading, text, size)
                if any(segment):
                    trace.append(PdfCellTrace(text="\n".join(segment), bbox=(x, top - height, x + width, top)))
                x += width
            if row.profile_image is not None and fragment == 1:
                self.image(page, row.profile_image, (self.left + self.widths[0] + 1, top - height + 2, self.widths[1] - 2, height - 4), "Imagem ausente", fit=False)
            self.rows.append(PdfRowFragment(item_id=page.item_id, engine_position=row.engine_position,
                                           print_position=row.print_position, page_number=self.page_number, fragment=fragment, cells=tuple(trace)))
            self.y -= height
            offset += count

    def findings(self, page):
        self.new_page(page, kind="FINDINGS")
        groups = defaultdict(list)
        for blocker in self.readiness.blockers:
            if blocker.item_id in {None, page.item_id}:
                groups[(blocker.code, blocker.message)].append(blocker.engine_position)
        paragraphs = ["Documento não equivalente para fabricação enquanto persistirem diferenças técnicas ou ausência de auditoria individual."]
        paragraphs.append("Descrição técnica da Engine: " + page.model_description)
        for (code, message), positions in groups.items():
            refs = [str(p) for p in positions if p is not None]
            paragraphs.append(code + ": " + message + (" Linhas Engine: " + ", ".join(refs) + "." if refs else ""))
        paragraphs += [note.classification + ": " + note.message for note in self.review_notes if note.item_id == page.item_id]
        for block in page.blocks:
            for row in block.rows:
                t = row.technical
                if t.quantity_per_unit != t.quantity_total:
                    paragraphs.append(f"Quantidade linha Engine {row.engine_position}, código {t.code or '[ausente]'}: {pdf_number(t.quantity_per_unit)}/esquadria; {pdf_number(t.quantity_total)} total ({_UNITS[t.quantity_unit]}).")
        long_codes = defaultdict(list)
        for block in page.blocks:
            for row in block.rows:
                code = row.technical.code
                if code and pdfmetrics.stringWidth(printable_text(code), _FONT, 4.7) > self.widths[3] - 4:
                    long_codes[code].append(row.engine_position)
        for code, positions in long_codes.items():
            paragraphs.append(f"Código completo (linhas Engine {', '.join(map(str, positions))}): {code}")
        paragraphs.append("Quantidades são totais do pedido; /esq. identifica valores por esquadria. un = peças; conj. = conjuntos de consumo. Unidade pendente não equivale a contagem física validada. Nenhum arredondamento foi aplicado pelo PDF.")
        for paragraph in paragraphs:
            lines = _wrap(paragraph, 547, _FONT, 7)
            for line in lines:
                if self.y < 54:
                    self.new_page(page, kind="FINDINGS", continuation=True)
                self.text(24, self.y - 8, line, 7)
                self.y -= 10
            self.y -= 7

    def run(self):
        for page in self.layout.pages:
            self.new_page(page)
            previous_kind = None
            for block in page.blocks:
                for index, row in enumerate(block.rows):
                    kind, cells = _row_cells(row)
                    if kind != previous_kind or index == 0:
                        if self.y - self.bottom < 55:
                            self.new_page(page, continuation=True)
                        title = {"CONSUMABLES": "Consumíveis — Med. Corte: comprimento agregado/esquadria; Quant.: conjuntos do pedido", "ACCESSORIES": "Acessórios", "HARDWARE": "Ferragens", "SCREWS": "Parafusos", "ENGINE_EXTENSION": "Linhas adicionais — sequência a confirmar"}.get(block.kind) if index == 0 else None
                        self.heading(kind, title)
                    self.row(page, row, kind, cells)
                    previous_kind = kind
            self.findings(page)
        self.canvas.save()
        return self.buffer.getvalue()


def render_production_pdf(
    layout: ProductionLayoutDocument, *, image_store: ProductionImageStore | None = None,
    review_notes: tuple[PdfReviewNote, ...] = (),
    model_headings: tuple[PdfModelHeading, ...] = (),
) -> ProductionPdfResult:
    """Render a saved B1 snapshot as a review PDF, returning bytes plus trace.

    Every item starts a new page; continuation pages and findings annexes have
    repeated identification. Oversized rows split by lines without truncation.
    No calculator, HTML resource loader, external URL or filesystem writer runs.
    """
    _ensure_fonts()
    readiness, images = _prepare(layout, image_store)
    pages = {page.item_id: page for page in layout.pages}
    if len({h.item_id for h in model_headings}) != len(model_headings) or any(h.item_id not in pages or h.model_key != pages[h.item_id].model_key for h in model_headings):
        raise ValueError("Identificação textual não corresponde ao modelo do snapshot.")
    if any(note.item_id not in pages for note in review_notes):
        raise ValueError("Nota de conferência referencia item inexistente.")
    renderer = _Renderer(layout, readiness, images, review_notes, model_headings)
    content = renderer.run()
    identities = {(row.item_id, row.engine_position) for row in renderer.rows}
    expected = {(page.item_id, row.engine_position) for page in layout.pages for block in page.blocks for row in block.rows}
    if identities != expected:
        raise ValueError("Integridade do PDF: linhas técnicas ausentes.")
    audit = ProductionPdfAudit(layout_sha256=layout.layout_sha256, pdf_sha256=hashlib.sha256(content).hexdigest(),
              review_notes_sha256=hashlib.sha256(canonical_json([note.model_dump(mode="json") for note in review_notes]).encode("utf-8")).hexdigest(),
              model_headings_sha256=hashlib.sha256(canonical_json([h.model_dump(mode="json") for h in model_headings]).encode("utf-8")).hexdigest(),
              page_count=len(renderer.pages), row_count=len(identities), rows=tuple(renderer.rows), pages=tuple(renderer.pages),
              images=tuple(renderer.images), readiness=readiness)
    return ProductionPdfResult(content, audit)
