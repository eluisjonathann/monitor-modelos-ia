# 🤖 Monitor Inteligente de Modelos de IA

[![Actualizar Leaderboard](https://github.com/eluisjonathann/monitor-modelos-ia/actions/workflows/update-leaderboard.yml/badge.svg)](https://github.com/eluisjonathann/monitor-modelos-ia/actions/workflows/update-leaderboard.yml)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Data Sources](https://img.shields.io/badge/Fuentes-Artificial%20Analysis%20%7C%20Arena%20LMSYS-orange)
![Update Frequency](https://img.shields.io/badge/Actualizaci%C3%B3n-3x%20al%20d%C3%ADa-green)

> 🔄 **Última sincronización automática:** `2026-09-26 08:27 UTC`

Sistema automatizado mediante **GitHub Actions** que monitorea, fusiona y clasifica en tiempo real las métricas de los modelos de inteligencia artificial líderes del mercado.

👉 **[📊 Explorar el Leaderboard Completo y Detallado en RESULTADOS.md](RESULTADOS.md)**

---

## 🎯 Guía Rápida de Recomendación (¿Qué modelo usar hoy?)

| Caso de Uso | Modelo Recomendado Líder | Por qué elegirlo |
| :--- | :--- | :--- |
| 🎓 **Tesis & Redacción Académica** | **Claude Fable 5** | Máximo razonamiento, síntesis conceptual y profundidad lógica. |
| 💻 **Programación & Desarrollo Web** | **Claude Opus 5** | Mayor precisión en generación de código, refactorización y terminal. |
| ⚡ **Consultas Diarias & Búsqueda Web** | **Claude Opus 4.6 Search** | Respuestas precisas conectadas a internet en tiempo real. |
| 🤖 **Agentes Autónomos & Workflows** | **Claude Opus 5 (High)** | Mejor resolución autónoma en tareas multi-paso complejas. |
| 🎨 **Generación de Imágenes** | **GPT Image 2** | Máxima fidelidad de instrucciones y calidad visual. |
| 🎬 **Generación de Video** | **Gemini Omni Flash** | Consistencia temporal y calidad de movimiento. |

---

## 🧠 Top 10 - Inteligencia General & Eficiencia (Artificial Analysis)

| Puesto | Modelo | Índice Inteligencia | Velocidad (t/s) | Costo / Tarea ($ USD) | Ventana Contexto |
| :---: | :--- | :---: | :---: | :---: | :---: |
| - | *Sin datos de Artificial Analysis disponibles* | - | - | - | - |

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