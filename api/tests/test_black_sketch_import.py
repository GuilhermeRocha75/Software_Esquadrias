import hashlib
from pathlib import Path
import unittest

from api.tests.test_maxim_ar_sketch import MaximArSketchTests, BASE, COMPANY
from api.app.production_images import ProductionImageManifest, ProductionImageStore
from tools.import_op_sketches import import_sketches


class BlackSketchImportTests(MaximArSketchTests):
    def test_import_preserves_library_and_renders_all_three_families(self):
        root = Path(self.temp.name)
        source = root / "incoming"
        source.mkdir()
        raw = (root / "sketch.jpg").read_bytes()
        names = ("JANELA 1 FOLHA MAXIM-AR (PRETO).jpg",
                 "PORTA 1 FOLHA DE GIRO COM PAINEL HORIZONTAL (PRETO).jpg",
                 "PAINEL  FIXO - 00 (PRETO).jpg")
        for name in names:
            (source / name).write_bytes(raw)
        manifest = root / "manifest.json"
        manifest.write_text(self.store.manifest.model_dump_json())
        self.assertEqual(import_sketches(source, manifest), 3)
        first = manifest.read_bytes()
        self.assertEqual(import_sketches(source, manifest), 3)
        self.assertEqual(manifest.read_bytes(), first)
        parsed = ProductionImageManifest.model_validate_json(first)
        self.assertIn(self.entry, parsed.entries)
        self.assertEqual(len(parsed.entries), 4)
        self.store = ProductionImageStore(root, parsed)
        technicals = (dict(BASE, leaf_system="PRIME_WINDOW_42x63"),
                      dict(family="GR", width_mm=900, height_mm=2100),
                      dict(family="FX", width_mm=800, height_mm=600))
        for technical in technicals:
            with self.subTest(family=technical["family"]):
                request = dict(production_order=dict(company_id=str(COMPANY), order_id="TEST",
                    items=[dict(item_id="1", finish_key="PRETO", technical_input=technical)]),
                    context=dict(company_id=str(COMPANY)))
                preview = self.client.post("/api/v1/production-orders/layout-preview", json=request)
                self.assertEqual(preview.status_code, 200, preview.text)
                image = preview.json()["pages"][0]["model_image"]
                self.assertEqual(image["status"], "VERIFIED")
                self.assertEqual(image["selector"]["finish_key"], "PRETO")
                op = self.client.post("/api/v1/production-orders/pdf", json=dict(layout_request=request))
                self.assertEqual(op.status_code, 200, op.text[:200])
                quote = self.client.post("/api/v1/quotes/full-pdf", json=dict(
                    company_id=str(COMPANY), client="Teste", number="1", installation=0,
                    lines=[dict(technical=technical, label="1", finish="PRETO", unit=100, total=100)]))
                self.assertEqual(quote.status_code, 200, quote.text[:200])
                self.assertEqual(quote.headers["X-Quote-Missing-Sketches"], "")
