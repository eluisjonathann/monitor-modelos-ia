"""
Monitor Avanzado de Modelos de Inteligencia Artificial
Extrae, fusiona y clasifica métricas en tiempo real desde:
- Artificial Analysis (Inteligencia, Velocidad, Costos, Contexto)
- LMSYS / Arena Leaderboard (Rankings por casos de uso y benchmarks especializados)

Diseñado con tolerancia a fallos, reintentos con backoff exponencial, degradación elegante
y normalización cruzada de modelos.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# Configuración de logging robusto compatible con UTF-8
logger = logging.getLogger("model_monitor")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

# Marcas y proveedores conocidos para normalización
KNOWN_PROVIDERS = [
    "anthropic", "google", "openai", "meta", "bytedance",
    "xai", "mistral", "deepseek", "alibaba", "qwen", "zhipu",
    "moonshot", "kimi", "cohere", "nvidia", "microsoft", "01-ai"
]

# Modificadores de esfuerzo, arneses y sufijos de razonamiento/fechas
MODIFIER_PATTERN = re.compile(
    r'\b(high|max|xhigh|low|medium|with fallback|codex harness|codex|harness|search|preview|grounding|thinking|instruct|chat|\d{8}|\d{4})\b',
    re.IGNORECASE
)


def create_resilient_session(
    retries: int = 3,
    backoff_factor: float = 1.5,
    status_forcelist: tuple[int, ...] = (429, 500, 502, 503, 504)
) -> requests.Session:
    """Crea una sesión HTTP configurada con reintentos y backoff exponencial."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def clean_model_name(name: str) -> tuple[str, str]:
    """
    Normaliza el nombre de un modelo retornando dos claves:
    1. full_key: clave normalizada completa (sin puntuación superflua ni marcas)
    2. base_key: clave base sin modificadores de razonamiento/esfuerzo ni sufijos temporales
    """
    if not name:
        return "", ""

    s = name.lower().strip()
    # Reemplazar caracteres separadores por espacios
    s = re.sub(r'[\(\)\[\]_/\-]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()

    # Eliminar nombres de marcas/proveedores conocidos
    for prov in KNOWN_PROVIDERS:
        s = re.sub(rf'\b{re.escape(prov)}\b', '', s, flags=re.IGNORECASE)

    s = re.sub(r'\s+', ' ', s).strip()
    full_key = re.sub(r'[^a-z0-9.]', '', s)

    # Base key: remover modificadores de esfuerzo, modos y fechas
    base = MODIFIER_PATTERN.sub('', s)
    base = re.sub(r'\s+', ' ', base).strip()
    base_key = re.sub(r'[^a-z0-9.]', '', base)

    # Si base_key quedó vacía tras remover modificadores, volver a full_key
    if not base_key:
        base_key = full_key

    return full_key, base_key


def extract_model_family_and_version(key: str) -> tuple[str, str]:
    """Extrae la familia principal del modelo y su número de versión si está presente."""
    match = re.search(r'([a-z]+)(\d+(?:\.\d+)?)', key)
    if match:
        return match.group(1), match.group(2)
    return key, ""


def get_artificial_analysis_data(session: requests.Session | None = None) -> dict[str, dict[str, Any]]:
    """Extrae métricas dinámicas de Artificial Analysis con soporte de reintentos y tolerancia a fallos."""
    url = "https://artificialanalysis.ai/models"
    models_dict: dict[str, dict[str, Any]] = {}
    http = session or create_resilient_session()

    try:
        logger.info("Consultando Artificial Analysis en vivo (%s)...", url)
        res = http.get(url, headers=HEADERS, timeout=(10, 25))
        res.raise_for_status()

        # 1. Intentar extracción por JSON-LD estructurado
        scripts = re.findall(
            r'<script[^>]*type=[\'"]application/ld\+json[\'"][^>]*>([\s\S]*?)</script>',
            res.text,
            re.IGNORECASE
        )

        for s in scripts:
            try:
                data = json.loads(s.strip())
                if isinstance(data, dict) and data.get("@type") == "Dataset" and "data" in data:
                    for item in data["data"]:
                        label = item.get("label") or item.get("name")
                        if not label:
                            continue
                        full_k, base_k = clean_model_name(label)
                        if full_k not in models_dict:
                            models_dict[full_k] = {
                                "name": label,
                                "full_key": full_k,
                                "base_key": base_k
                            }
                        m = models_dict[full_k]

                        # Índice de Inteligencia
                        intel = (
                            item.get("intelligenceIndex") or
                            item.get("artificialAnalysisIntelligenceIndex")
                        )
                        if intel is not None:
                            try:
                                m["intelligence"] = round(float(intel), 2)
                            except (ValueError, TypeError):
                                pass

                        # Velocidad (tokens por segundo)
                        if "medianOutputSpeed" in item and item["medianOutputSpeed"] is not None:
                            try:
                                m["speed"] = round(float(item["medianOutputSpeed"]), 1)
                            except (ValueError, TypeError):
                                pass
                        elif "outputSpeed" in item and item["outputSpeed"] is not None and "speed" not in m:
                            try:
                                m["speed"] = round(float(item["outputSpeed"]), 1)
                            except (ValueError, TypeError):
                                pass

                        # Costo por Tarea ($ USD)
                        if "costPerIntelligenceIndexTask" in item and item["costPerIntelligenceIndexTask"] is not None:
                            try:
                                m["cost"] = round(float(item["costPerIntelligenceIndexTask"]), 4)
                            except (ValueError, TypeError):
                                pass

                        # Ventana de Contexto
                        if "contextWindowTokens" in item and item["contextWindowTokens"] is not None:
                            try:
                                tokens = int(item["contextWindowTokens"])
                                m["context_str"] = f"{tokens // 1000}k" if tokens >= 1000 else f"{tokens}"
                            except (ValueError, TypeError):
                                pass
            except json.JSONDecodeError:
                continue

        logger.info("Artificial Analysis: %d modelos cargados.", len(models_dict))
    except Exception as e:
        logger.warning("Error consultando Artificial Analysis: %s", e)

    return models_dict


def get_arena_data(session: requests.Session | None = None) -> dict[str, list[dict[str, str]]]:
    """Extrae rankings actualizados desde Arena Leaderboard en las 11 categorías de uso práctico."""
    url = "https://arena.ai/leaderboard"
    logger.info("Consultando Arena Leaderboard en vivo (%s)...", url)

    categories: dict[str, list[dict[str, str]]] = {
        "text": [],          # Tesis, Investigación Académica & Redacción
        "code": [],          # Programación, Terminal & WebDev
        "search": [],        # Búsqueda Web & Consultas en Vivo
        "agent": [],         # Agentes Autónomos & Flujos Multi-Paso
        "document": [],      # Extracción & Análisis de Documentos/PDFs
        "vision": [],        # Visión Multimodal & Análisis de Gráficos
        "image_to_code": [], # Conversión de Diseños UI a Código Frontend
        "image_gen": [],     # Generación de Imágenes (Text-to-Image)
        "image_edit": [],    # Edición de Imágenes
        "video_gen": [],     # Generación de Video
        "video_edit": [],    # Edición de Video
    }

    http = session or create_resilient_session()

    try:
        res = http.get(url, headers=HEADERS, timeout=(10, 25))
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        # Buscar contenedores con aria-label de arena
        containers = soup.find_all(
            "div",
            {"aria-label": lambda x: bool(x and "arena: top" in x.lower())}
        )

        for container in containers:
            aria_label = container.get("aria-label", "").lower()
            cat_key = None

            if "image-to-webdev" in aria_label:
                cat_key = "image_to_code"
            elif "webdev" in aria_label or "coding" in aria_label:
                cat_key = "code"
            elif "image-to-video" in aria_label or "text-to-video" in aria_label:
                cat_key = "video_gen"
            elif "video edit" in aria_label:
                cat_key = "video_edit"
            elif "text-to-image" in aria_label:
                cat_key = "image_gen"
            elif "image edit" in aria_label:
                cat_key = "image_edit"
            elif "search" in aria_label:
                cat_key = "search"
            elif "agent" in aria_label:
                cat_key = "agent"
            elif "vision" in aria_label:
                cat_key = "vision"
            elif "document" in aria_label:
                cat_key = "document"
            elif "text" in aria_label:
                cat_key = "text"

            if not cat_key or cat_key not in categories:
                continue

            if len(categories[cat_key]) >= 10:
                continue

            # Buscar filas de modelos
            rows = container.find_all(
                "div",
                class_=lambda x: bool(x and ("flex flex-col" in x or "contents" in x))
            )
            if not rows:
                rows = container.find_all("div", recursive=False)

            seen_names = {m["name"] for m in categories[cat_key]}

            for row in rows:
                if len(categories[cat_key]) >= 10:
                    break

                name_span = row.find("span", title=True)
                model_name = name_span["title"].strip() if name_span else None
                if not model_name or model_name in seen_names or model_name.lower() == "desconocido":
                    continue

                # Extraer puntaje / score
                score_span = row.find(
                    "span",
                    class_=lambda x: bool(x and "text-text-primary" in x and "tabular-nums" in x)
                )
                score = score_span.text.strip() if score_span else "-"

                # Extraer margen de error / CI
                err_span = row.find(
                    "span",
                    class_=lambda x: bool(x and "text-text-secondary" in x and "tabular-nums" in x)
                )
                margin = err_span.text.strip() if err_span else "-"

                # Para agentes, el score viene con porcentaje o indicador interactivo
                if cat_key == "agent":
                    agent_score_span = row.find(
                        "span",
                        class_=lambda x: bool(x and "text-interactive-positive" in x)
                    )
                    if not agent_score_span:
                        # Fallback por contenido de texto que tenga %
                        for sp in row.find_all("span"):
                            if "%" in sp.get_text():
                                agent_score_span = sp
                                break

                    if agent_score_span:
                        clean_agent_score = re.sub(r'[^0-9\.%+-]', '', agent_score_span.get_text().strip())
                        if clean_agent_score:
                            score = clean_agent_score

                seen_names.add(model_name)
                categories[cat_key].append({
                    "name": model_name,
                    "score": score,
                    "margin": margin
                })

        total = sum(len(v) for v in categories.values())
        logger.info("Arena Leaderboard: %d modelos extraídos en %d categorías.", total, len(categories))
    except Exception as e:
        logger.warning("Error consultando Arena Leaderboard: %s", e)

    return categories


def find_aa_match(model_name: str, aa_dict: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """
    Cruza con alta precisión un modelo de Arena con su métrica en Artificial Analysis.
    Aplica una estrategia multi-nivel:
    1. Coincidencia exacta de clave completa.
    2. Coincidencia exacta de clave base (sin modificadores de razonamiento).
    3. Coincidencia por familia y versión idéntica.
    """
    if not model_name or not aa_dict:
        return None

    full_k, base_k = clean_model_name(model_name)

    # 1. Coincidencia exacta de clave completa
    if full_k in aa_dict:
        return aa_dict[full_k]

    # 2. Coincidencia por clave base
    if base_k:
        for m in aa_dict.values():
            if m.get("base_key") == base_k:
                return m

    # 3. Coincidencia por familia y versión idéntica (evitando falsos positivos)
    fam_b, ver_b = extract_model_family_and_version(base_k)
    if fam_b and len(fam_b) >= 3:
        for m in aa_dict.values():
            aa_fam, aa_ver = extract_model_family_and_version(m.get("base_key", ""))
            if aa_fam == fam_b and aa_ver == ver_b and ver_b != "":
                return m

    # 4. Coincidencia secundaria con normalización de versión (puntos vs sin puntos)
    norm_base = base_k.replace(".", "")
    for m in aa_dict.values():
        target_norm = m.get("base_key", "").replace(".", "")
        if target_norm == norm_base and len(norm_base) >= 4:
            return m

    return None


def get_top_model_name(categories: dict[str, list[dict[str, str]]], cat_key: str, default: str) -> str:
    """Obtiene de manera segura el nombre del modelo líder de una categoría sin riesgo de IndexError."""
    items = categories.get(cat_key, [])
    if items and isinstance(items, list) and len(items) > 0:
        return items[0].get("name", default)
    return default


def generate_resultados_markdown(
    aa_dict: dict[str, dict[str, Any]],
    arena_categories: dict[str, list[dict[str, str]]],
    now_utc: str
) -> str:
    """Genera el reporte integral enriquecido RESULTADOS.md con todas las categorías y manejo de degradación."""
    aa_available = bool(aa_dict)
    arena_available = any(bool(v) for v in arena_categories.values())

    status_notes = []
    if not aa_available:
        status_notes.append("⚠️ **Aviso:** No se pudieron sincronizar datos de Artificial Analysis en esta ejecución.")
    if not arena_available:
        status_notes.append("⚠️ **Aviso:** No se pudieron sincronizar datos de Arena Leaderboard en esta ejecución.")

    notes_block = "\n".join([f"> {n}" for n in status_notes]) + ("\n\n" if status_notes else "")

    md = [
        "# 🏆 Leaderboard Consolidado de Modelos de IA",
        "",
        f"> 🔄 **Última actualización automática:** `{now_utc}`",
        "> 🌐 **Fuentes de datos:** Datos dinámicos en vivo de [Artificial Analysis](https://artificialanalysis.ai) y [Arena Leaderboard (LMSYS)](https://arena.ai).",
        "",
        notes_block.strip() if notes_block else "",
        "---",
        "",
        "## 🧭 Índice Rápido de Categorías",
        "1. [🌟 Fusión Cruzada: Top Modelos Globales (AA + Arena)](#1-🌟-fusión-cruzada-top-modelos-globales-aa--arena)",
        "2. [🎓 Tesis, Investigación Académica & Razonamiento Profundo](#2-🎓-tesis-investigación-académica--razonamiento-profundo)",
        "3. [💻 Programación, Terminal & Desarrollo de Software](#3-💻-programación-terminal--desarrollo-de-software)",
        "4. [⚡ Consultas Rápidas, Dudas Cotidianas & Búsqueda Web en Vivo](#4-⚡-consultas-rápidas-dudas-cotidianas--búsqueda-web-en-vivo)",
        "5. [🤖 Agentes Autónomos & Tareas Multi-Paso](#5-🤖-agentes-autónomos--tareas-multi-paso)",
        "6. [📄 Extracción & Análisis de Documentos / PDFs](#6-📄-extracción--análisis-de-documentos--pdfs)",
        "7. [👁️ Visión Multimodal & Análisis de Gráficos](#7-👁️-visión-multimodal--análisis-de-gráficos)",
        "8. [🎨 De Diseño UI / Mockup a Código Frontend](#8-🎨-de-diseño-ui--mockup-a-código-frontend)",
        "9. [🖼️ Generación & Edición Creativa de Imágenes](#9-🖼️-generación--edición-creativa-de-imágenes)",
        "10. [🎬 Generación & Edición de Video](#10-🎬-generación--edición-de-video)",
        "11. [💰 Campeones de Eficiencia (Calidad/Precio & Velocidad)](#11-💰-campeones-de-eficiencia-calidadprecio--velocidad)",
        "",
        "---",
        "",
        "## 1. 🌟 Fusión Cruzada: Top Modelos Globales (AA + Arena)",
        "Esta tabla combina la **inteligencia y velocidad** de Artificial Analysis con las **puntuaciones de combate humano (Elo)** de Arena Leaderboard.",
        "",
        "| Puesto | Modelo | Inteligencia (AA) | Velocidad | Costo / Tarea | Arena Pts (Text) | Contexto | Mejor Para |",
        "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |"
    ]

    aa_sorted = sorted(
        [m for m in aa_dict.values() if "intelligence" in m],
        key=lambda x: x.get("intelligence", 0),
        reverse=True
    )

    arena_text_map = {
        clean_model_name(m["name"])[1]: m["score"]
        for m in arena_categories.get("text", [])
        if "name" in m and "score" in m
    }

    if aa_sorted:
        for i, m in enumerate(aa_sorted[:12], start=1):
            intel = str(m.get("intelligence", "-"))
            speed = f"{m['speed']} t/s" if "speed" in m else "-"
            cost = f"${m['cost']:.4f}" if "cost" in m else "-"
            ctx = str(m.get("context_str", "-"))

            # Buscar score de Arena
            arena_pts = arena_text_map.get(m.get("base_key", ""), "-")

            # Caso de uso recomendado
            use_case = "Razonamiento Avanzado & Tesis"
            if "speed" in m and isinstance(m["speed"], (int, float)) and m["speed"] > 150:
                use_case = "Uso Diario, APIs & Velocidad"
            elif "cost" in m and isinstance(m["cost"], (int, float)) and m["cost"] < 0.3:
                use_case = "Alta Eficiencia / Económico"
            elif i <= 3:
                use_case = "Máximo Rendimiento & Problemas Complejos"

            md.append(f"| {i} | **{m['name']}** | {intel} | {speed} | {cost} | {arena_pts} | {ctx} | {use_case} |")
    else:
        md.append("| - | *Sin datos disponibles de Artificial Analysis en esta ejecución* | - | - | - | - | - | - |")

    # 2. Tesis
    md.extend([
        "",
        "---",
        "",
        "## 2. 🎓 Tesis, Investigación Académica & Razonamiento Profundo",
        "*(Ideal para redacción de marcos teóricos, análisis de artículos científicos, deducción lógica y síntesis compleja)*",
        "",
        "| Puesto | Modelo | Puntuación Arena (Text) | Margen / CI | Inteligencia AA | Velocidad | Costo |",
        "| :---: | :--- | :---: | :---: | :---: | :---: | :---: |"
    ])
    text_models = arena_categories.get("text", [])
    if text_models:
        for i, m in enumerate(text_models, start=1):
            aa_info = find_aa_match(m["name"], aa_dict)
            intel = str(aa_info.get("intelligence", "-")) if aa_info else "-"
            speed = f"{aa_info['speed']} t/s" if aa_info and "speed" in aa_info else "-"
            cost = f"${aa_info['cost']:.4f}" if aa_info and "cost" in aa_info else "-"
            md.append(f"| {i} | **{m['name']}** | {m['score']} | {m['margin']} | {intel} | {speed} | {cost} |")
    else:
        md.append("| - | *Sin datos disponibles en esta categoría* | - | - | - | - | - |")

    # 3. Código
    md.extend([
        "",
        "---",
        "",
        "## 3. 💻 Programación, Terminal & Desarrollo de Software",
        "*(Ideal para crear aplicaciones, debugging, scripting, arquitectura de software y desarrollo Web/FullStack)*",
        "",
        "| Puesto | Modelo | Puntuación Arena (WebDev) | Margen / CI | Velocidad AA | Costo AA |",
        "| :---: | :--- | :---: | :---: | :---: | :---: |"
    ])
    code_models = arena_categories.get("code", [])
    if code_models:
        for i, m in enumerate(code_models, start=1):
            aa_info = find_aa_match(m["name"], aa_dict)
            speed = f"{aa_info['speed']} t/s" if aa_info and "speed" in aa_info else "-"
            cost = f"${aa_info['cost']:.4f}" if aa_info and "cost" in aa_info else "-"
            md.append(f"| {i} | **{m['name']}** | {m['score']} | {m['margin']} | {speed} | {cost} |")
    else:
        md.append("| - | *Sin datos disponibles en esta categoría* | - | - | - | - |")

    # 4. Búsqueda
    md.extend([
        "",
        "---",
        "",
        "## 4. ⚡ Consultas Rápidas, Dudas Cotidianas & Búsqueda Web en Vivo",
        "*(Ideal para preguntas del día a día, resúmenes rápidos de noticias e información reciente con navegación web)*",
        "",
        "| Puesto | Modelo | Puntuación Arena (Search) | Margen / CI | Velocidad | Costo |",
        "| :---: | :--- | :---: | :---: | :---: | :---: |"
    ])
    search_models = arena_categories.get("search", [])
    if search_models:
        for i, m in enumerate(search_models, start=1):
            aa_info = find_aa_match(m["name"], aa_dict)
            speed = f"{aa_info['speed']} t/s" if aa_info and "speed" in aa_info else "-"
            cost = f"${aa_info['cost']:.4f}" if aa_info and "cost" in aa_info else "-"
            md.append(f"| {i} | **{m['name']}** | {m['score']} | {m['margin']} | {speed} | {cost} |")
    else:
        md.append("| - | *Sin datos disponibles en esta categoría* | - | - | - | - |")

    # 5. Agentes
    md.extend([
        "",
        "---",
        "",
        "## 5. 🤖 Agentes Autónomos & Tareas Multi-Paso",
        "*(Ideal para workflows de agentes, llamadas a APIs, interacción con herramientas y ejecución autónoma)*",
        "",
        "| Puesto | Modelo | Mejora Neta (Agent) | Margen | Inteligencia AA |",
        "| :---: | :--- | :---: | :---: | :---: |"
    ])
    agent_models = arena_categories.get("agent", [])
    if agent_models:
        for i, m in enumerate(agent_models, start=1):
            aa_info = find_aa_match(m["name"], aa_dict)
            intel = str(aa_info.get("intelligence", "-")) if aa_info else "-"
            md.append(f"| {i} | **{m['name']}** | {m['score']} | {m['margin']} | {intel} |")
    else:
        md.append("| - | *Sin datos disponibles en esta categoría* | - | - | - |")

    # 6. Documentos
    md.extend([
        "",
        "---",
        "",
        "## 6. 📄 Extracción & Análisis de Documentos / PDFs",
        "*(Ideal para procesar balances, contratos, libros enteros y documentos con tablas densas)*",
        "",
        "| Puesto | Modelo | Puntuación Arena (Document) | Margen / CI | Ventana Contexto |",
        "| :---: | :--- | :---: | :---: | :---: |"
    ])
    doc_models = arena_categories.get("document", [])
    if doc_models:
        for i, m in enumerate(doc_models, start=1):
            aa_info = find_aa_match(m["name"], aa_dict)
            ctx = str(aa_info.get("context_str", "-")) if aa_info else "-"
            md.append(f"| {i} | **{m['name']}** | {m['score']} | {m['margin']} | {ctx} |")
    else:
        md.append("| - | *Sin datos disponibles en esta categoría* | - | - | - |")

    # 7. Visión
    md.extend([
        "",
        "---",
        "",
        "## 7. 👁️ Visión Multimodal & Análisis de Gráficos",
        "*(Ideal para analizar capturas de pantalla, diagramas arquitectónicos, imágenes médicas y fotos)*",
        "",
        "| Puesto | Modelo | Puntuación Arena (Vision) | Margen / CI |",
        "| :---: | :--- | :---: | :---: |"
    ])
    vision_models = arena_categories.get("vision", [])
    if vision_models:
        for i, m in enumerate(vision_models, start=1):
            md.append(f"| {i} | **{m['name']}** | {m['score']} | {m['margin']} |")
    else:
        md.append("| - | *Sin datos disponibles en esta categoría* | - | - |")

    # 8. Image to Code
    md.extend([
        "",
        "---",
        "",
        "## 8. 🎨 De Diseño UI / Mockup a Código Frontend",
        "*(Convierte capturas de pantalla, bocetos de Figma o imágenes directamente en código HTML/React/Tailwind)*",
        "",
        "| Puesto | Modelo | Puntuación Arena (Image-to-WebDev) | Margen / CI |",
        "| :---: | :--- | :---: | :---: |"
    ])
    i2c_models = arena_categories.get("image_to_code", [])
    if i2c_models:
        for i, m in enumerate(i2c_models, start=1):
            md.append(f"| {i} | **{m['name']}** | {m['score']} | {m['margin']} |")
    else:
        md.append("| - | *Sin datos disponibles en esta categoría* | - | - |")

    # 9. Imágenes
    md.extend([
        "",
        "---",
        "",
        "## 9. 🖼️ Generación & Edición Creativa de Imágenes",
        "",
        "### 9.1 Generación de Imágenes (Prompt a Imagen)",
        "| Puesto | Modelo | Puntuación Arena | Margen / CI |",
        "| :---: | :--- | :---: | :---: |"
    ])
    img_gen_models = arena_categories.get("image_gen", [])
    if img_gen_models:
        for i, m in enumerate(img_gen_models, start=1):
            md.append(f"| {i} | **{m['name']}** | {m['score']} | {m['margin']} |")
    else:
        md.append("| - | *Sin datos disponibles en esta sub-categoría* | - | - |")

    md.extend([
        "",
        "### 9.2 Edición y Modificación de Imágenes",
        "| Puesto | Modelo | Puntuación Arena | Margen / CI |",
        "| :---: | :--- | :---: | :---: |"
    ])
    img_edit_models = arena_categories.get("image_edit", [])
    if img_edit_models:
        for i, m in enumerate(img_edit_models, start=1):
            md.append(f"| {i} | **{m['name']}** | {m['score']} | {m['margin']} |")
    else:
        md.append("| - | *Sin datos disponibles en esta sub-categoría* | - | - |")

    # 10. Video
    md.extend([
        "",
        "---",
        "",
        "## 10. 🎬 Generación & Edición de Video",
        "",
        "### 10.1 Generación y Animación de Video",
        "| Puesto | Modelo | Puntuación Arena | Margen / CI |",
        "| :---: | :--- | :---: | :---: |"
    ])
    video_gen_models = arena_categories.get("video_gen", [])
    if video_gen_models:
        for i, m in enumerate(video_gen_models, start=1):
            md.append(f"| {i} | **{m['name']}** | {m['score']} | {m['margin']} |")
    else:
        md.append("| - | *Sin datos disponibles en esta sub-categoría* | - | - |")

    md.extend([
        "",
        "### 10.2 Edición de Video con IA",
        "| Puesto | Modelo | Puntuación Arena | Margen / CI |",
        "| :---: | :--- | :---: | :---: |"
    ])
    video_edit_models = arena_categories.get("video_edit", [])
    if video_edit_models:
        for i, m in enumerate(video_edit_models, start=1):
            md.append(f"| {i} | **{m['name']}** | {m['score']} | {m['margin']} |")
    else:
        md.append("| - | *Sin datos disponibles en esta sub-categoría* | - | - |")

    # 11. Eficiencia
    md.extend([
        "",
        "---",
        "",
        "## 11. 💰 Campeones de Eficiencia (Calidad/Precio & Velocidad)",
        "Modelos con la mayor velocidad de generación (tokens/s) y menor costo por tarea, ideales para uso intensivo y producción.",
        "",
        "| Modelo | Velocidad (tokens/s) | Costo / Tarea ($ USD) | Inteligencia AA | Ventana Contexto |",
        "| :--- | :---: | :---: | :---: | :---: |"
    ])
    fast_models = sorted(
        [m for m in aa_dict.values() if "speed" in m],
        key=lambda x: x.get("speed", 0),
        reverse=True
    )
    if fast_models:
        for m in fast_models[:10]:
            speed = f"{m['speed']} t/s"
            cost = f"${m['cost']:.4f}" if "cost" in m else "-"
            intel = str(m.get("intelligence", "-"))
            ctx = str(m.get("context_str", "-"))
            md.append(f"| **{m['name']}** | {speed} | {cost} | {intel} | {ctx} |")
    else:
        md.append("| *Sin datos de velocidad disponibles* | - | - | - | - |")

    md.append("\n---\n")
    return "\n".join([line for line in md if line is not None])


def generate_readme_markdown(
    aa_dict: dict[str, dict[str, Any]],
    arena_categories: dict[str, list[dict[str, str]]],
    now_utc: str
) -> str:
    """Genera la portada del repositorio (README.md) con guía de uso diario y resumen ejecutivo."""
    aa_sorted = sorted(
        [m for m in aa_dict.values() if "intelligence" in m],
        key=lambda x: x.get("intelligence", 0),
        reverse=True
    )

    # Uso de safe accessor para prevenir IndexError en caso de degradación
    top_text = get_top_model_name(arena_categories, "text", "Claude Fable 5")
    top_code = get_top_model_name(arena_categories, "code", "Claude Opus 5")
    top_search = get_top_model_name(arena_categories, "search", "Claude Opus 4.6 Search")
    top_agent = get_top_model_name(arena_categories, "agent", "Claude Opus 5 (High)")
    top_image = get_top_model_name(arena_categories, "image_gen", "GPT Image 2")
    top_video = get_top_model_name(arena_categories, "video_gen", "Gemini Omni Flash")

    md = [
        "# 🤖 Monitor Inteligente de Modelos de IA",
        "",
        "[![Actualizar Leaderboard](https://github.com/eluisjonathann/monitor-modelos-ia/actions/workflows/update-leaderboard.yml/badge.svg)](https://github.com/eluisjonathann/monitor-modelos-ia/actions/workflows/update-leaderboard.yml)",
        "![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)",
        "![Data Sources](https://img.shields.io/badge/Fuentes-Artificial%20Analysis%20%7C%20Arena%20LMSYS-orange)",
        "![Update Frequency](https://img.shields.io/badge/Actualizaci%C3%B3n-3x%20al%20d%C3%ADa-green)",
        "",
        f"> 🔄 **Última sincronización automática:** `{now_utc}`",
        "",
        "Sistema automatizado mediante **GitHub Actions** que monitorea, fusiona y clasifica en tiempo real las métricas de los modelos de inteligencia artificial líderes del mercado.",
        "",
        "👉 **[📊 Explorar el Leaderboard Completo y Detallado en RESULTADOS.md](RESULTADOS.md)**",
        "",
        "---",
        "",
        "## 🎯 Guía Rápida de Recomendación (¿Qué modelo usar hoy?)",
        "",
        "| Caso de Uso | Modelo Recomendado Líder | Por qué elegirlo |",
        "| :--- | :--- | :--- |",
        f"| 🎓 **Tesis & Redacción Académica** | **{top_text}** | Máximo razonamiento, síntesis conceptual y profundidad lógica. |",
        f"| 💻 **Programación & Desarrollo Web** | **{top_code}** | Mayor precisión en generación de código, refactorización y terminal. |",
        f"| ⚡ **Consultas Diarias & Búsqueda Web** | **{top_search}** | Respuestas precisas conectadas a internet en tiempo real. |",
        f"| 🤖 **Agentes Autónomos & Workflows** | **{top_agent}** | Mejor resolución autónoma en tareas multi-paso complejas. |",
        f"| 🎨 **Generación de Imágenes** | **{top_image}** | Máxima fidelidad de instrucciones y calidad visual. |",
        f"| 🎬 **Generación de Video** | **{top_video}** | Consistencia temporal y calidad de movimiento. |",
        "",
        "---",
        "",
        "## 🧠 Top 10 - Inteligencia General & Eficiencia (Artificial Analysis)",
        "",
        "| Puesto | Modelo | Índice Inteligencia | Velocidad (t/s) | Costo / Tarea ($ USD) | Ventana Contexto |",
        "| :---: | :--- | :---: | :---: | :---: | :---: |"
    ]

    if aa_sorted:
        for i, m in enumerate(aa_sorted[:10], start=1):
            speed = f"{m['speed']} t/s" if "speed" in m else "-"
            cost = f"${m['cost']:.4f}" if "cost" in m else "-"
            intel = str(m.get("intelligence", "-"))
            ctx = str(m.get("context_str", "-"))
            md.append(f"| {i} | **{m['name']}** | {intel} | {speed} | {cost} | {ctx} |")
    else:
        md.append("| - | *Sin datos de Artificial Analysis disponibles* | - | - | - | - |")

    md.extend([
        "",
        "---",
        "",
        "## 📂 Categorías Especializadas en `RESULTADOS.md`",
        "- 🌟 **Fusión Cruzada:** Tabla global con inteligencia, velocidad, costo y Elo cruzados.",
        "- 🎓 **Tesis e Investigación:** Para papers, redacción académica y deducción lógica.",
        "- 💻 **Programación y Terminal:** Para apps, debugging y código frontend/backend.",
        "- ⚡ **Consultas Cotidianas:** Búsqueda en vivo y respuestas rápidas para el día a día.",
        "- 🤖 **Agentes Autónomos:** Para automatización de flujos y herramientas.",
        "- 📄 **Documentos y PDFs:** Extracción en balances y textos de más de 1M de tokens.",
        "- 👁️ **Visión Multimodal:** Interpretación de capturas, planos y fotos.",
        "- 🎨 **De Diseño UI a Código:** Conversión directa de imágenes a HTML/Tailwind/React.",
        "- 🖼️ **Imágenes & Video:** Generación y edición multimedia con IA.",
        "- 💰 **Campeones de Eficiencia:** Modelos más veloces y económicos para producción.",
        "",
        "---",
        "",
        "## ⚙️ Arquitectura y Automatización",
        "- **Workflow:** [`.github/workflows/update-leaderboard.yml`](.github/workflows/update-leaderboard.yml) se ejecuta automáticamente cada 8 horas (10:00 PM, 6:00 AM y 2:00 PM hora Perú).",
        "- **Web Scraping Dinámico:** Extrae datos en vivo sin dependencias pesadas mediante `requests` y `beautifulsoup4`.",
        "- **Auto-Commit Seguro:** Si los datos cambian, el bot de GitHub actualiza `RESULTADOS.md` y `README.md` automáticamente sin colisiones."
    ])

    return "\n".join(md)


def main() -> None:
    logger.info("Iniciando ciclo de extracción y fusión de datos...")
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    session = create_resilient_session()

    # 1. Obtener datos en vivo con reintentos y tolerancia a fallos
    aa_data = get_artificial_analysis_data(session=session)
    arena_data = get_arena_data(session=session)

    # 2. Generar RESULTADOS.md (Reporte integral y categorizado)
    resultados_content = generate_resultados_markdown(aa_data, arena_data, now_utc)
    with open("RESULTADOS.md", "w", encoding="utf-8") as f:
        f.write(resultados_content)
    logger.info("RESULTADOS.md actualizado con éxito.")

    # 3. Generar README.md (Portada con guía de uso diario y resumen)
    readme_content = generate_readme_markdown(aa_data, arena_data, now_utc)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    logger.info("README.md actualizado con éxito.")

    logger.info("¡Proceso completado exitosamente!")


if __name__ == "__main__":
    main()
