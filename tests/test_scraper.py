"""
Tests unitarios y de integración con Mocks para scraper.py.
Verifica normalización de modelos, matching difuso, parsers, reintentos y degradación elegante.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

import requests

from scraper import (
    clean_model_name,
    create_resilient_session,
    extract_model_family_and_version,
    find_aa_match,
    generate_readme_markdown,
    generate_resultados_markdown,
    get_arena_data,
    get_artificial_analysis_data,
    get_top_model_name,
)


class TestScraperNormalization(unittest.TestCase):
    """Pruebas para normalización de nombres y matching de modelos."""

    def test_clean_model_name_basic(self):
        full, base = clean_model_name("Claude Opus 5 (max)")
        self.assertEqual(full, "claudeopus5max")
        self.assertEqual(base, "claudeopus5")

    def test_clean_model_name_with_provider_and_hyphens(self):
        full, base = clean_model_name("claude-opus-5-high")
        self.assertEqual(full, "claudeopus5high")
        self.assertEqual(base, "claudeopus5")

    def test_clean_model_name_with_dates_and_harness(self):
        full, base = clean_model_name("gpt-5.6-sol-xhigh (codex-harness)")
        self.assertEqual(full, "gpt5.6solxhighcodexharness")
        self.assertEqual(base, "gpt5.6sol")

    def test_clean_model_name_date_stripping(self):
        full, base = clean_model_name("deepseek-v4-pro-high-20260813")
        self.assertIn("v4", base)
        self.assertNotIn("20260813", base)
        self.assertNotIn("high", base)

    def test_clean_model_name_empty(self):
        self.assertEqual(clean_model_name(""), ("", ""))
        self.assertEqual(clean_model_name(None), ("", ""))

    def test_extract_model_family_and_version(self):
        fam, ver = extract_model_family_and_version("claudeopus5")
        self.assertEqual(fam, "claudeopus")
        self.assertEqual(ver, "5")

        fam2, ver2 = extract_model_family_and_version("geminiflash3.7")
        self.assertEqual(fam2, "geminiflash")
        self.assertEqual(ver2, "3.7")

    def test_find_aa_match_exact_and_base(self):
        aa_dict = {
            "claudeopus5max": {
                "name": "Claude Opus 5 (max)",
                "full_key": "claudeopus5max",
                "base_key": "claudeopus5",
                "intelligence": 63.05,
                "speed": 61.9,
                "cost": 2.3369
            },
            "gemini3.7flashhigh": {
                "name": "Gemini 3.7 Flash (high)",
                "full_key": "gemini3.7flashhigh",
                "base_key": "gemini3.7flash",
                "intelligence": 56.03,
                "speed": 340.1,
                "cost": 0.4022
            }
        }

        # Exact match
        match1 = find_aa_match("Claude Opus 5 (max)", aa_dict)
        self.assertIsNotNone(match1)
        self.assertEqual(match1["name"], "Claude Opus 5 (max)")

        # Base match with different suffix
        match2 = find_aa_match("claude-opus-5-high", aa_dict)
        self.assertIsNotNone(match2)
        self.assertEqual(match2["name"], "Claude Opus 5 (max)")

        # Version dots vs hyphens
        match3 = find_aa_match("gemini-3.7-flash-high", aa_dict)
        self.assertIsNotNone(match3)
        self.assertEqual(match3["name"], "Gemini 3.7 Flash (high)")

    def test_find_aa_match_avoids_false_positives(self):
        aa_dict = {
            "claude4.5haiku": {
                "name": "Claude 4.5 Haiku",
                "full_key": "claude4.5haiku",
                "base_key": "claude4.5haiku",
                "intelligence": 45.0,
            }
        }
        # A completely different model family/version should NOT match Claude 4.5 Haiku
        match = find_aa_match("Claude Opus 5", aa_dict)
        self.assertIsNone(match)

    def test_get_top_model_name_safe(self):
        categories = {
            "text": [{"name": "Claude Fable 5", "score": "1506"}],
            "empty_cat": []
        }
        self.assertEqual(get_top_model_name(categories, "text", "Default"), "Claude Fable 5")
        self.assertEqual(get_top_model_name(categories, "empty_cat", "Default"), "Default")
        self.assertEqual(get_top_model_name(categories, "missing_cat", "Default"), "Default")


class TestScraperNetworkAndResilience(unittest.TestCase):
    """Pruebas de tolerancia a fallos, reintentos y degradación elegante."""

    def test_create_resilient_session(self):
        session = create_resilient_session(retries=2, backoff_factor=0.5)
        self.assertIn("https://", session.adapters)
        self.assertIn("http://", session.adapters)
        adapter = session.adapters["https://"]
        self.assertEqual(adapter.max_retries.total, 2)

    def test_get_artificial_analysis_data_mock_success(self):
        mock_html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "Dataset",
                "data": [
                    {
                        "label": "Claude Opus 5 (max)",
                        "intelligenceIndex": 63.05,
                        "medianOutputSpeed": 61.9,
                        "costPerIntelligenceIndexTask": 2.3369,
                        "contextWindowTokens": 1000000
                    }
                ]
            }
            </script>
        </head>
        </html>
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.raise_for_status = MagicMock()

        mock_session = MagicMock()
        mock_session.get.return_value = mock_response

        data = get_artificial_analysis_data(session=mock_session)
        self.assertEqual(len(data), 1)
        m = list(data.values())[0]
        self.assertEqual(m["name"], "Claude Opus 5 (max)")
        self.assertEqual(m["intelligence"], 63.05)
        self.assertEqual(m["speed"], 61.9)
        self.assertEqual(m["cost"], 2.3369)
        self.assertEqual(m["context_str"], "1000k")

    def test_get_artificial_analysis_data_handles_error(self):
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.RequestException("Connection timeout")

        data = get_artificial_analysis_data(session=mock_session)
        self.assertEqual(data, {})

    def test_get_arena_data_mock_success(self):
        mock_html = """
        <html>
        <body>
            <div aria-label="Text arena: top 10 models by score">
                <div class="flex flex-col sm:contents">
                    <span title="claude-fable-5">claude-fable-5</span>
                    <span class="text-text-primary tabular-nums">1506</span>
                    <span class="text-text-secondary tabular-nums">1</span>
                </div>
            </div>
            <div aria-label="Agent arena: top 10 models by net improvement">
                <div class="flex flex-col sm:contents">
                    <span title="Claude Opus 5 (High)">Claude Opus 5 (High)</span>
                    <span class="text-interactive-positive tabular-nums">+12.19%</span>
                    <span class="text-text-secondary tabular-nums">1</span>
                </div>
            </div>
        </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.raise_for_status = MagicMock()

        mock_session = MagicMock()
        mock_session.get.return_value = mock_response

        data = get_arena_data(session=mock_session)
        self.assertIn("text", data)
        self.assertEqual(len(data["text"]), 1)
        self.assertEqual(data["text"][0]["name"], "claude-fable-5")
        self.assertEqual(data["text"][0]["score"], "1506")

        self.assertIn("agent", data)
        self.assertEqual(len(data["agent"]), 1)
        self.assertEqual(data["agent"][0]["score"], "+12.19%")

    def test_get_arena_data_handles_error(self):
        mock_session = MagicMock()
        mock_session.get.side_effect = requests.RequestException("Server 500 Error")

        data = get_arena_data(session=mock_session)
        self.assertIsInstance(data, dict)
        self.assertTrue(all(isinstance(v, list) and len(v) == 0 for v in data.values()))

    def test_markdown_generation_with_empty_sources(self):
        """Verifica que si una o ambas fuentes fallan, el markdown se genera sin excepciones."""
        # Ambas vacías
        res_md = generate_resultados_markdown({}, {}, "2026-08-15 00:00 UTC")
        self.assertIn("# 🏆 Leaderboard Consolidado de Modelos de IA", res_md)
        self.assertIn("⚠️ **Aviso:**", res_md)

        readme_md = generate_readme_markdown({}, {}, "2026-08-15 00:00 UTC")
        self.assertIn("# 🤖 Monitor Inteligente de Modelos de IA", readme_md)
        self.assertIn("Claude Fable 5", readme_md)  # Fallback seguro


if __name__ == "__main__":
    unittest.main()
