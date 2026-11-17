"""Regression for existing DESIGN-only manifests used by PRIME Maxim-Ar items."""
import hashlib
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import UUID

from fastapi.testclient import TestClient
from PIL import Image

from api.app.main import app, _production_image_store
from api.app.production_images import (
    ImageSelector, ProductionImageManifest, ProductionImageStore,
    StoredProductionImage, image_metadata, model_identity,
)

COMPANY = UUID(int=1)
BASE = dict(family="MAXIM_AR", width_mm=800, height_mm=600,
            leaf_system="DESIGN_WINDOW_60x78")


class MaximArSketchTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        root = Path(self.temp.name)
        data = BytesIO()
        Image.new("RGB", (30, 40), "white").save(data, "JPEG")
        raw = data.getvalue()
        (root / "sketch.jpg").write_bytes(raw)
        media, width, height = image_metadata(raw)
        key, _ = model_identity(BASE, "BRANCO")
        self.entry = StoredProductionImage(
            selector=ImageSelector(kind="MODEL_SKETCH", model_key=key, finish_key="BRANCO"),
            relative_path="sketch.jpg", sha256=hashlib.sha256(raw).hexdigest(),
            media_type=media, width_px=width, height_px=height, finish_policy="EXACT")
        self.store = ProductionImageStore(root, ProductionImageManifest(
            company_id=COMPANY, source_workbook_sha256="a" * 64, entries=(self.entry,)))
        app.dependency_overrides[_production_image_store] = lambda: self.store
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.temp.cleanup()

    def test_existing_design_binding_renders_prime_in_both_endpoints(self):
        for orientation in ("HORIZONTAL", "VERTICAL"):
            technical = dict(BASE, leaf_system="PRIME_WINDOW_42x63", orientation=orientation)
            with self.subTest(orientation=orientation):
                request = dict(production_order=dict(company_id=str(COMPANY), order_id="TEST",
                    items=[dict(item_id="1", finish_key="BRANCO", technical_input=technical)]),
                    context=dict(company_id=str(COMPANY)))
                preview = self.client.post("/api/v1/production-orders/layout-preview", json=request)
                self.assertEqual(preview.status_code, 200, preview.text)
                self.assertEqual(preview.json()["pages"][0]["model_image"]["status"], "VERIFIED")
                op = self.client.post("/api/v1/production-orders/pdf", json=dict(layout_request=request))
                self.assertEqual(op.status_code, 200, op.text[:200])
                self.assertTrue(op.content.startswith(b"%PDF"))
                quote = self.client.post("/api/v1/quotes/full-pdf", json=dict(
                    company_id=str(COMPANY), client="Teste", number="1", installation=0,
                    lines=[dict(technical=technical, label="1", finish="BRANCO", unit=100, total=100)]))
                self.assertEqual(quote.status_code, 200, quote.text[:200])
                self.assertEqual(quote.headers["X-Quote-Missing-Sketches"], "")

    def test_other_shapes_colors_and_companies_do_not_match(self):
        prime = dict(BASE, leaf_system="PRIME_WINDOW_42x63")
        for change in (dict(leaf_count=2), dict(screen_enabled=True),
                       dict(leaf_grid=dict(vertical_transoms=1)),
                       dict(bottom_fixed_panel=dict(height_mm=200))):
            with self.subTest(change=change):
                self.assertEqual(self.store.resolve_model(dict(prime, **change), "BRANCO", COMPANY).status, "MISSING_ASSET")
        self.assertEqual(self.store.resolve_model(prime, "PRETO", COMPANY).status, "MISSING_ASSET")
        with self.assertRaises(ValueError):
            self.store.resolve_model(prime, "BRANCO", UUID(int=2))

    def test_corrupted_legacy_image_is_not_used(self):
        (Path(self.temp.name) / "sketch.jpg").write_bytes(b"broken")
        prime = dict(BASE, leaf_system="PRIME_WINDOW_42x63")
        self.assertNotEqual(self.store.resolve_model(prime, "BRANCO", COMPANY).status, "VERIFIED")
