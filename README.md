# 🤖 Monitor Inteligente de Modelos de IA

[![Actualizar Leaderboard](https://github.com/eluisjonathann/monitor-modelos-ia/actions/workflows/update-leaderboard.yml/badge.svg)](https://github.com/eluisjonathann/monitor-modelos-ia/actions/workflows/update-leaderboard.yml)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Data Sources](https://img.shields.io/badge/Fuentes-Artificial%20Analysis%20%7C%20Arena%20LMSYS-orange)
![Update Frequency](https://img.shields.io/badge/Actualizaci%C3%B3n-3x%20al%20d%C3%ADa-green)

> 🔄 **Última sincronización automática:** `2026-08-19 11:30 UTC`

Sistema automatizado mediante **GitHub Actions** que monitorea, fusiona y clasifica en tiempo real las métricas de los modelos de inteligencia artificial líderes del mercado.

👉 **[📊 Explorar el Leaderboard Completo y Detallado en RESULTADOS.md](RESULTADOS.md)**

---

## 🎯 Guía Rápida de Recomendación (¿Qué modelo usar hoy?)

| Caso de Uso | Modelo Recomendado Líder | Por qué elegirlo |
| :--- | :--- | :--- |
| 🎓 **Tesis & Redacción Académica** | **claude-fable-5** | Máximo razonamiento, síntesis conceptual y profundidad lógica. |
| 💻 **Programación & Desarrollo Web** | **claude-opus-5-max** | Mayor precisión en generación de código, refactorización y terminal. |
| ⚡ **Consultas Diarias & Búsqueda Web** | **claude-opus-4-6-search** | Respuestas precisas conectadas a internet en tiempo real. |
| 🤖 **Agentes Autónomos & Workflows** | **Claude Opus 5 (High)** | Mejor resolución autónoma en tareas multi-paso complejas. |
| 🎨 **Generación de Imágenes** | **gpt-image-2 (medium)** | Máxima fidelidad de instrucciones y calidad visual. |
| 🎬 **Generación de Video** | **gemini-omni-flash** | Consistencia temporal y calidad de movimiento. |

---

## 🧠 Top 10 - Inteligencia General & Eficiencia (Artificial Analysis)

| Puesto | Modelo | Índice Inteligencia | Velocidad (t/s) | Costo / Tarea ($ USD) | Ventana Contexto |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | **Claude Opus 5 (max)** | 63.05 | 54.6 t/s | $2.3369 | 1000k |
| 2 | **Claude Fable 5 (with fallback)** | 62.07 | 67.6 t/s | $3.1396 | 1000k |
| 3 | **GPT-5.6 Sol (max)** | 60.93 | 65.4 t/s | $1.2312 | 1000k |
| 4 | **Grok 4.6 (high)** | 60.92 | 56.5 t/s | $0.8367 | 500k |
| 5 | **Kimi K3 (max)** | 59.7 | 38.2 t/s | $0.8375 | 1048k |
| 6 | **GLM-5.3 (max)** | 59.51 | 84.7 t/s | $0.6829 | 1000k |
| 7 | **Qwen3.8 Max** | 58.08 | - | - | 1000k |
| 8 | **Muse Spark 1.2 (xhigh)** | 56.76 | - | $0.3992 | 1048k |
| 9 | **GPT-5.6 Terra (max)** | 56.58 | 117.4 t/s | - | 1000k |
| 10 | **Gemini 3.7 Flash (high)** | 56.03 | 343.7 t/s | $0.4022 | 1000k |

---

## 📂 Categorías Especializadas en `LEADERBOARD_MODELOS_IA.md`
- 🌟 **Fusión Cruzada:** Tabla global con inteligencia, velocidad, costo y Elo cruzados.
- 🎓 **Tesis e Investigación:** Para papers, redacción académica y deducción lógica.
- 💻 **Programación y Terminal:** Para apps, debugging y código frontend/backend.
- ⚡ **Consultas Cotidianas:** Búsqueda en vivo y respuestas rápidas para el día a día.
- 🤖 **Agentes Autónomos:** Para automatización de flujos y herramientas.
- 📄 **Documentos y PDFs:** Extracción en balances y textos de más de 1M de tokens.
- 👁️ **Visión Multimodal:** Interpretación de capturas, planos y fotos.
- 🎨 **De Diseño UI a Código:** Conversión directa de imágenes a HTML/Tailwind/React.
- 🖼️ **Imágenes & Video:** Generación y edición multimedia con IA.
- 💰 **Campeones de Eficiencia:** Modelos más veloces y económicos para producción.

---

## ⚙️ Arquitectura y Automatización
- **Workflow:** [`.github/workflows/update-leaderboard.yml`](.github/workflows/update-leaderboard.yml) se ejecuta automáticamente cada 8 horas (10:00 PM, 6:00 AM y 2:00 PM hora Perú).
- **Web Scraping Dinámico:** Extrae datos en vivo sin dependencias pesadas mediante `requests` y `beautifulsoup4`.
- **Auto-Commit Seguro:** Si los datos cambian, el bot de GitHub actualiza `LEADERBOARD_MODELOS_IA.md` y `README.md` automáticamente sin colisiones.