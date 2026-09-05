# 🤖 Monitor Inteligente de Modelos de IA

[![Actualizar Leaderboard](https://github.com/eluisjonathann/monitor-modelos-ia/actions/workflows/update-leaderboard.yml/badge.svg)](https://github.com/eluisjonathann/monitor-modelos-ia/actions/workflows/update-leaderboard.yml)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Data Sources](https://img.shields.io/badge/Fuentes-Artificial%20Analysis%20%7C%20Arena%20LMSYS-orange)
![Update Frequency](https://img.shields.io/badge/Actualizaci%C3%B3n-3x%20al%20d%C3%ADa-green)

> 🔄 **Última sincronización automática:** `2026-09-05 13:47 UTC`

Sistema automatizado mediante **GitHub Actions** que monitorea, fusiona y clasifica en tiempo real las métricas de los modelos de inteligencia artificial líderes del mercado.

👉 **[📊 Explorar el Leaderboard Completo y Detallado en RESULTADOS.md](RESULTADOS.md)**

---

## 🎯 Guía Rápida de Recomendación (¿Qué modelo usar hoy?)

| Caso de Uso | Modelo Recomendado Líder | Por qué elegirlo |
| :--- | :--- | :--- |
| 🎓 **Tesis & Redacción Académica** | **claude-fable-5** | Máximo razonamiento, síntesis conceptual y profundidad lógica. |
| 💻 **Programación & Desarrollo Web** | **claude-fable-5.1-max** | Mayor precisión en generación de código, refactorización y terminal. |
| ⚡ **Consultas Diarias & Búsqueda Web** | **gpt-5.6-sol-xhigh** | Respuestas precisas conectadas a internet en tiempo real. |
| 🤖 **Agentes Autónomos & Workflows** | **Claude Opus 5 (High)** | Mejor resolución autónoma en tareas multi-paso complejas. |
| 🎨 **Generación de Imágenes** | **gpt-image-2 (medium)** | Máxima fidelidad de instrucciones y calidad visual. |
| 🎬 **Generación de Video** | **gemini-omni-1.1-flash** | Consistencia temporal y calidad de movimiento. |

---

## 🧠 Top 10 - Inteligencia General & Eficiencia (Artificial Analysis)

| Puesto | Modelo | Índice Inteligencia | Velocidad (t/s) | Costo / Tarea ($ USD) | Ventana Contexto |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | **Claude Fable 5.1 (max with fallback)** | 56.76 | 67.1 t/s | $6.1169 | 1000k |
| 2 | **GPT-6 Astra (max)** | 54.66 | 63.4 t/s | $2.5673 | 1000k |
| 3 | **Claude Opus 5 (max)** | 54.05 | 56.8 t/s | $4.2053 | 1000k |
| 4 | **Claude Fable 5 (with fallback)** | 53.19 | 68.1 t/s | - | 1000k |
| 5 | **Muse Spark 1.3 (max)** | 52.95 | 190.1 t/s | $0.9588 | 1000k |
| 6 | **GPT-5.6 Sol (max)** | 51.26 | 80.9 t/s | - | 1000k |
| 7 | **Grok 4.6 (high)** | 50.58 | 62.8 t/s | $1.2536 | 500k |
| 8 | **Kimi K3 (max)** | 50.23 | 40.3 t/s | $1.5764 | 1048k |
| 9 | **GLM-5.3 (max)** | 48.58 | 84.2 t/s | $1.2594 | 1000k |
| 10 | **Gemini 3.8 Flash (high)** | 47.07 | - | $0.7380 | 1000k |

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