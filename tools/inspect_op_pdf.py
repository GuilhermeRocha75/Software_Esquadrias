"""Independent PDF inspection: actual text boxes, page geometry and image pixels.

Requires developer dependencies. Reports identifiers/counts, never customer
header text or source paths. Does not invoke the renderer or the Engine.
"""
from __future__ import annotations

import hashlib
from io import BytesIO
import re

import pymupdf
from pypdf import PdfReader
from PIL import Image


def _compact(value):
    return re.sub(r"\s+", "", value)


def _pixels(image):
    image = image.convert("RGB")
    return image.size, hashlib.sha256(image.tobytes()).hexdigest()


def inspect_pdf(content: bytes, audit, *, expected_images: dict[str, bytes] | None = None) -> dict:
    """Check independently decoded PDF against renderer's cell/row trace.

    Every traced cell must be inside the page and recoverable in its own box.
    Original image pixels can additionally be verified using Pillow on both
    sides; bitmaps from historical PDFs are a separate visual comparison.
    """
    errors = []
    try:
        reader = PdfReader(BytesIO(content), strict=True)
        document = pymupdf.open(stream=content, filetype="pdf")
    except Exception:
        return {"integrity_valid": False, "errors": [{"code": "UNREADABLE_PDF"}]}
    with document:
        page_objects = [document[index] for index in range(len(document))]
        text_pages = {index: page.get_textpage() for index, page in enumerate(page_objects)}
        characters = {}
        for index, page in enumerate(page_objects):
            raw = page.get_text("rawdict", textpage=text_pages[index])
            characters[index] = [(char["bbox"], char["c"]) for block in raw["blocks"] if block["type"] == 0
                                  for line in block["lines"] for span in line["spans"] for char in span["chars"]]
        if hashlib.sha256(content).hexdigest() != audit.pdf_sha256:
            errors.append({"code": "PDF_HASH_MISMATCH"})
        if len(reader.pages) != len(document) or len(document) != audit.page_count:
            errors.append({"code": "PAGE_COUNT_MISMATCH"})
        all_text = []
        for index, page in enumerate(page_objects):
            text = page.get_text()
            all_text.append(text)
            if abs(page.rect.width - 595.27559) > 0.02 or abs(page.rect.height - 841.88976) > 0.02:
                errors.append({"code": "NOT_A4_PORTRAIT", "page": index + 1})
            if "CONFERÊNCIA" not in text or "NÃO FABRICAR" not in text:
                errors.append({"code": "MISSING_REVIEW_MARK", "page": index + 1})
            if re.search(r"(?i)[a-z]:[\\/]|file://|\\\\[^\s\\]+\\", text) or any(line.strip() == "A" for line in text.splitlines()):
                errors.append({"code": "LOCAL_PATH_OR_SENTINEL_PRINTED", "page": index + 1})
            for block in page.get_text("blocks"):
                if block[0] < -0.1 or block[1] < -0.1 or block[2] > page.rect.width + 0.1 or block[3] > page.rect.height + 0.1:
                    errors.append({"code": "TEXT_OUTSIDE_PAGE", "page": index + 1})
        verified_cells = 0
        for row in audit.rows:
            page = page_objects[row.page_number - 1]
            for cell_index, cell in enumerate(row.cells):
                x0, y0, x1, y1 = cell.bbox
                box = pymupdf.Rect(x0, page.rect.height - y1, x1, page.rect.height - y0)
                if not page.rect.contains(box):
                    errors.append({"code": "CELL_OUTSIDE_PAGE", "item_id": row.item_id, "engine_position": row.engine_position})
                # Decode each page once. Selecting fully contained glyph boxes
                # avoids repeated whole-page extraction and also catches glyph
                # overflow that an intersection-only textbox could overlook.
                text = "".join(char for rect, char in characters[row.page_number - 1]
                               if rect[0] >= box.x0 - 0.2 and rect[1] >= box.y0 - 0.2
                               and rect[2] <= box.x1 + 0.2 and rect[3] <= box.y1 + 0.2)
                if _compact(text) != _compact(cell.text):
                    errors.append({"code": "CELL_TEXT_MISMATCH", "item_id": row.item_id,
                                   "engine_position": row.engine_position, "fragment": row.fragment, "cell": cell_index})
                else:
                    verified_cells += 1
        identities = {(row.item_id, row.engine_position) for row in audit.rows}
        if len(identities) != audit.row_count:
            errors.append({"code": "ROW_COUNT_MISMATCH"})
        image_count = 0
        page_images = {}
        for number, page in enumerate(reader.pages, 1):
            records = []
            objects = page.get("/Resources", {}).get("/XObject", {})
            for obj in objects.values():
                image = obj.get_object()
                if image.get("/Subtype") != "/Image":
                    continue
                data = image.get_data()
                digest = hashlib.sha256(data).hexdigest()
                pixels = None
                try:
                    if "/DCTDecode" in image.get("/Filter", []):
                        with Image.open(BytesIO(data)) as decoded:
                            pixels = _pixels(decoded)
                    elif image.get("/BitsPerComponent") == 8:
                        mode = {"/DeviceRGB": "RGB", "/DeviceGray": "L", "/DeviceCMYK": "CMYK"}.get(image.get("/ColorSpace"))
                        if mode:
                            pixels = _pixels(Image.frombytes(mode, (image["/Width"], image["/Height"]), data))
                except (ValueError, OSError):
                    pass
                records.append((digest, pixels, obj.idnum))
            image_count += len(records)
            page_images[number] = records
        image_checks = 0
        for placement in audit.images:
            if expected_images is not None:
                data = expected_images.get(placement.sha256)
                if data is None:
                    errors.append({"code": "IMAGE_SOURCE_UNAVAILABLE", "page": placement.page_number})
                    continue
                if hashlib.sha256(data).hexdigest() != placement.sha256:
                    errors.append({"code": "IMAGE_SOURCE_HASH_MISMATCH", "page": placement.page_number})
                    continue
                with Image.open(BytesIO(data)) as image:
                    expected = _pixels(image)
                candidates = [record for record in page_images[placement.page_number] if record[0] == placement.sha256 or record[1] == expected]
                if not candidates:
                    errors.append({"code": "IMAGE_PIXELS_MISMATCH", "page": placement.page_number})
                else:
                    page = page_objects[placement.page_number - 1]
                    x0, y0, x1, y1 = placement.bbox
                    box = pymupdf.Rect(x0, page.rect.height - y1, x1, page.rect.height - y0)
                    rects = [rect for record in candidates for rect in page.get_image_rects(record[2])]
                    if not any(max(abs(a - b) for a, b in zip(box, rect)) < 0.1 for rect in rects):
                        errors.append({"code": "IMAGE_PLACEMENT_MISMATCH", "page": placement.page_number})
                    else:
                        image_checks += 1
        return {"integrity_valid": not errors, "errors": errors, "pages": len(document),
                "table_pages": sum(p.kind == "TABLE" for p in audit.pages),
                "finding_pages": sum(p.kind == "FINDINGS" for p in audit.pages),
                "rows": len(identities), "row_fragments": len(audit.rows), "verified_cells": verified_cells,
                "embedded_images": image_count, "verified_image_placements": image_checks,
                "manufacturing_allowed": audit.readiness.fabrication_allowed}
