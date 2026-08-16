"""
Tests de integridad estructural y sintáctica de los archivos Markdown generados.
Valida tablas alineadas, conteo de columnas homogéneo, encabezados y enlaces.
"""

import re
import unittest

from scraper import generate_readme_markdown, generate_resultados_markdown


class TestMarkdownIntegrity(unittest.TestCase):
    """Pruebas de integridad para RESULTADOS.md y README.md."""

    def setUp(self):
        self.sample_aa = {
            "opus5": {
                "name": "Claude Opus 5 (max)",
                "full_key": "opus5max",
                "base_key": "opus5",
                "intelligence": 63.05,
                "speed": 61.9,
                "cost": 2.3369,
                "context_str": "1000k"
            },
            "flash3.7": {
                "name": "Gemini 3.7 Flash (high)",
                "full_key": "flash3.7high",
                "base_key": "flash3.7",
                "intelligence": 56.03,
                "speed": 340.1,
                "cost": 0.4022,
                "context_str": "1000k"
            }
        }

        self.sample_arena = {
            "text": [{"name": "claude-fable-5", "score": "1506", "margin": "1"}],
            "code": [{"name": "claude-opus-5-max", "score": "1692", "margin": "1"}],
            "search": [{"name": "claude-opus-4-6-search", "score": "1253", "margin": "1"}],
            "agent": [{"name": "Claude Opus 5 (High)", "score": "12.19%", "margin": "1"}],
            "document": [{"name": "claude-opus-5-high", "score": "1520", "margin": "1"}],
            "vision": [{"name": "claude-fable-5", "score": "1315", "margin": "1"}],
            "image_to_code": [{"name": "claude-opus-5-max", "score": "1670", "margin": "1"}],
            "image_gen": [{"name": "gpt-image-2 (medium)", "score": "1381", "margin": "1"}],
            "image_edit": [{"name": "gpt-image-2 (medium)", "score": "1463", "margin": "1"}],
            "video_gen": [{"name": "gemini-omni-flash", "score": "1512", "margin": "1"}],
            "video_edit": [{"name": "minimax-h3", "score": "1390", "margin": "1"}],
        }

        self.now_utc = "2026-08-15 12:00 UTC"

    def test_resultados_markdown_all_11_categories_present(self):
        content = generate_resultados_markdown(self.sample_aa, self.sample_arena, self.now_utc)

        expected_sections = [
            "## 1. 🌟 Fusión Cruzada: Top Modelos Globales",
            "## 2. 🎓 Tesis, Investigación Académica",
            "## 3. 💻 Programación, Terminal",
            "## 4. ⚡ Consultas Rápidas, Dudas Cotidianas",
            "## 5. 🤖 Agentes Autónomos",
            "## 6. 📄 Extracción & Análisis de Documentos",
            "## 7. 👁️ Visión Multimodal",
            "## 8. 🎨 De Diseño UI / Mockup a Código",
            "## 9. 🖼️ Generación & Edición Creativa de Imágenes",
            "## 10. 🎬 Generación & Edición de Video",
            "## 11. 💰 Campeones de Eficiencia"
        ]

        for sec in expected_sections:
            self.assertTrue(
                any(sec.lower() in line.lower() for line in content.splitlines()),
                f"Sección faltante en RESULTADOS.md: {sec}"
            )

    def test_markdown_tables_column_consistency(self):
        """Valida que todas las filas de cada tabla Markdown tengan el mismo número de columnas (pipes)."""
        content = generate_resultados_markdown(self.sample_aa, self.sample_arena, self.now_utc)
        lines = content.splitlines()

        current_table: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                current_table.append(stripped)
            else:
                if current_table:
                    # Validar consistencia de la tabla acumulada
                    col_counts = [row.count("|") for row in current_table]
                    first_count = col_counts[0]
                    for idx, c in enumerate(col_counts):
                        self.assertEqual(
                            c, first_count,
                            f"Tabla desalineada en fila {idx}: '{current_table[idx]}' esperadas {first_count} pipes, encontradas {c}"
                        )
                    current_table = []

    def test_readme_markdown_structure(self):
        readme = generate_readme_markdown(self.sample_aa, self.sample_arena, self.now_utc)
        self.assertIn("# 🤖 Monitor Inteligente de Modelos de IA", readme)
        self.assertIn("## 🎯 Guía Rápida de Recomendación", readme)
        self.assertIn("## 🧠 Top 10 - Inteligencia General & Eficiencia", readme)
        self.assertIn("## 📂 Categorías Especializadas", readme)
        self.assertIn("## ⚙️ Arquitectura y Automatización", readme)

    def test_no_nan_or_undefined_in_markdown(self):
        res_content = generate_resultados_markdown(self.sample_aa, self.sample_arena, self.now_utc)
        readme_content = generate_readme_markdown(self.sample_aa, self.sample_arena, self.now_utc)

        for content, name in [(res_content, "RESULTADOS.md"), (readme_content, "README.md")]:
            self.assertNotIn("NaN", content, f"Encontrado NaN en {name}")
            self.assertNotIn("undefined", content.lower(), f"Encontrado undefined en {name}")
            self.assertNotIn("None", content, f"Encontrado literal 'None' en {name}")


if __name__ == "__main__":
    unittest.main()
