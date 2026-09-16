import os
import unittest
from unittest.mock import patch

from api.app.main import _cors_origins


class DeploymentConfigTests(unittest.TestCase):
    def test_local_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                _cors_origins(),
                ["http://127.0.0.1:5173", "http://localhost:5173"],
            )

    def test_same_origin_production_needs_no_cross_origin_allowlist(self):
        with patch.dict(os.environ, {"CORS_ALLOWED_ORIGINS": ""}):
            self.assertEqual(_cors_origins(), [])

    def test_explicit_production_origins(self):
        with patch.dict(
            os.environ,
            {"CORS_ALLOWED_ORIGINS": "https://app.example.com/, https://admin.example.com"},
        ):
            self.assertEqual(
                _cors_origins(),
                ["https://app.example.com", "https://admin.example.com"],
            )

    def test_wildcard_is_rejected(self):
        with patch.dict(os.environ, {"CORS_ALLOWED_ORIGINS": "*"}):
            with self.assertRaises(ValueError):
                _cors_origins()


if __name__ == "__main__":
    unittest.main()
