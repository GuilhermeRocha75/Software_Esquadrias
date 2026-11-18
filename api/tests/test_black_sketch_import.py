from pathlib import Path

from api.tests.test_maxim_ar_sketch import MaximArSketchTests, BASE, COMPANY
from api.app.production_images import ProductionImageManifest, ProductionImageStore, model_identity
from tools.import_op_sketches import import_sketches


class BlackSketchImportTests(MaximArSketchTests):
    def test_reimported_maxim_ar_sketch_replaces_unavailable_binding_for_each_finish(self):
        root = Path(self.temp.name)
        source = root / "incoming"
        source.mkdir()
        original = root / "sketch.jpg"
        entries = []
        for finish in ("BRANCO", "PRETO"):
            key, basename = model_identity(BASE, finish)
            (source / basename).write_bytes(original.read_bytes())
            selector = self.entry.selector.model_copy(update={"model_key": key, "finish_key": finish})
            entries.append(self.entry.model_copy(update={"selector": selector}))
        path = root / "manifest.json"
        path.write_text(self.store.manifest.model_copy(update={"entries": tuple(entries)}).model_dump_json())
        import_sketches(source, path)
        original.unlink()
        self.store = ProductionImageStore(root, ProductionImageManifest.model_validate_json(path.read_bytes()))
        request = dict(production_order=dict(company_id=str(COMPANY), order_id="TEST", items=[
            dict(item_id=finish, finish_key=finish, technical_input=BASE) for finish in ("BRANCO", "PRETO")
        ]), context=dict(company_id=str(COMPANY)))
        preview = self.client.post("/api/v1/production-orders/layout-preview", json=request)
        self.assertEqual(preview.status_code, 200, preview.text)
        for page, finish in zip(preview.json()["pages"], ("BRANCO", "PRETO"), strict=True):
            image = page["model_image"]
            self.assertEqual(image["status"], "VERIFIED")
            self.assertEqual(image["selector"]["finish_key"], finish)
        quote = self.client.post("/api/v1/quotes/full-pdf", json=dict(
            company_id=str(COMPANY), client="Teste", number="1", installation=0,
            lines=[dict(technical=BASE, label=finish, finish=finish, unit=100, total=100)
                   for finish in ("BRANCO", "PRETO")]))
        self.assertEqual(quote.status_code, 200)
        self.assertEqual(quote.headers["X-Quote-Missing-Sketches"], "")

    def test_import_preserves_library_and_renders_all_three_families(self):
        root = Path(self.temp.name)
        source = root / "incoming"
        source.mkdir()
        raw = (root / "sketch.jpg").read_bytes()
        names = ("JANELA 1 FOLHA MAXIM-AR (PRETO).jpg",
                 "JANELA 2 FOLHAS MAXIM-AR (V) (BRANCO).JPG",
                 "PORTA 1 FOLHA DE GIRO COM PAINEL HORIZONTAL (PRETO).jpg",
                 "PAINEL  FIXO - 00 (PRETO).jpg")
        for name in names:
            (source / name).write_bytes(raw)
        manifest = root / "manifest.json"
        manifest.write_text(self.store.manifest.model_dump_json())
        self.assertEqual(import_sketches(source, manifest), 4)
        first = manifest.read_bytes()
        self.assertEqual(import_sketches(source, manifest), 4)
        self.assertEqual(manifest.read_bytes(), first)
        parsed = ProductionImageManifest.model_validate_json(first)
        self.assertIn(self.entry, parsed.entries)
        self.assertEqual(len(parsed.entries), 5)
        self.store = ProductionImageStore(root, parsed)
        vertical = dict(BASE, leaf_count=2, orientation="VERTICAL")
        self.assertEqual(self.store.resolve_model(vertical, "BRANCO", COMPANY).status, "VERIFIED")
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
