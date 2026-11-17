import unittest

from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from api.app.main import full_quote_pdf
from api.app.quote_pdf import QuotePdf


class FullQuotePdfTest(unittest.TestCase):
    def test_missing_sketch_still_returns_pdf_with_item_warning(self):
        payload = {
            "company_id": "00000000-0000-0000-0000-000000000001",
            "client": "Cliente de teste", "number": "001", "installation": 460,
            "lines": [{"label": "01", "finish": "BRANCO", "unit": 400, "total": 800,
                       "technical": {"family": "CR", "leaf_system": "PRIME_WINDOW_42x66",
                                     "leaf_count": 2, "width_mm": 1200, "height_mm": 1500, "quantity": 2}}],
        }
        with patch.dict("os.environ", {"ORC_CROQUIS_DIR": ""}):
            response = full_quote_pdf(QuotePdf.model_validate(payload), image_store=None)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.body.startswith(b"%PDF-"))
        self.assertEqual(response.headers["X-Quote-Missing-Sketches"], "1")
