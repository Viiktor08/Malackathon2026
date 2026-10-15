"""Genera el dashboard de segmentos: un único HTML autónomo con los datos agregados dentro.

perfil (profiling) + textos (segmentos) -> payload -> JSON incrustado en la plantilla jinja2.
Solo viajan agregados por segmento: nunca datos de clientes.
"""
import json
import math

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from src import config
from src.profiling import DIMS, KPIS, build_profile, check_profile
from src.segmentos import SEGMENTOS, check_segmentos, fill_texts

MAX_JSON_KB = 200

# Nombres legibles de las distribuciones y de sus categorías
DIM_LABELS = {"edad": "Edad", "pais": "País", "clase": "Clase del coche principal",
              "motor": "Motor del coche principal", "leasing": "Leasing"}
CAT_LABELS = {
    "CH": "Suiza", "AT": "Austria",
    "COMPACTO": "Compacto", "MEDIO": "Medio", "EJECUTIVO": "Ejecutivo", "SUV_GRANDE": "SUV grande",
    "LUJO_DEPORTIVO": "Lujo / deportivo", "FURGONETA": "Furgoneta", "OTRO": "Otro",
    "COMBUSTION": "Combustión", "MILD_HYBRID": "Mild hybrid", "PLUGIN_HYBRID": "Híbrido enchufable",
    "ELECTRIC": "Eléctrico", "UNKNOWN": "Desconocido",
    "never_active": "Nunca", "active_FL_only": "Leasing activo",
    "active_FL_and_CASH": "Leasing activo y contado", "was_active": "Leasing terminado",
}
_TEXT_KEYS = ["slug", "nombre", "frase", "accion", "etiquetas", "plan"]


def _sin_nan(x):
    """Cambia los NaN por None (JSON.parse no acepta NaN)."""
    if isinstance(x, dict):
        return {k: _sin_nan(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_sin_nan(v) for v in x]
    if isinstance(x, float) and math.isnan(x):
        return None
    return x


def build_payload(profile, segmentos):
    """Perfil + textos rellenados + todo lo que la plantilla necesita para dibujar."""
    check_segmentos(segmentos, profile["meta"]["k"])
    segs = []
    for stats in profile["segmentos"]:
        textos = fill_texts(segmentos[stats["id"]], stats)
        segs.append({**stats, **{k: textos[k] for k in _TEXT_KEYS}, "color_idx": stats["id"]})
    return _sin_nan({
        "meta": profile["meta"],
        "kpis": KPIS,
        "dims": {d: DIM_LABELS[d] for d in DIMS},
        "categorias": CAT_LABELS,
        "colores": {"claro": config.SEGMENT_COLORS, "oscuro": config.SEGMENT_COLORS_DARK,
                    "base": config.BASE_GRAY},
        "base": profile["base"],
        "segmentos": segs,
    })


def payload_json(payload):
    """JSON estricto y seguro para ir dentro de <script> (sin «</» literales)."""
    return json.dumps(payload, ensure_ascii=False, allow_nan=False).replace("</", "<\\/")


def check_payload(payload, json_text):
    assert "client_id" not in json_text, "el dashboard no puede llevar client_id"
    kb = len(json_text.encode("utf-8")) / 1024
    assert kb < MAX_JSON_KB, f"el JSON pesa {kb:.0f} KB (máximo {MAX_JSON_KB})"
    assert len(payload["segmentos"]) == payload["meta"]["k"], "faltan segmentos"


def render(payload):
    env = Environment(loader=FileSystemLoader(config.TEMPLATES_DIR),
                      autoescape=select_autoescape(enabled_extensions=("html", "j2")))
    plantilla = env.get_template("dashboard.html.j2")
    # El JSON ya va escapado para <script>; si jinja lo escapara como HTML, dejaría de ser JSON válido
    return plantilla.render(payload=payload, data_json=Markup(payload_json(payload)))


def write_dashboard(clients, labels, path=config.DASHBOARD_HTML, segmentos=None):
    """De la tabla de clientes y las etiquetas al fichero HTML. Devuelve la ruta."""
    segmentos = SEGMENTOS if segmentos is None else segmentos
    profile = build_profile(clients, labels)
    check_profile(profile)
    payload = build_payload(profile, segmentos)
    check_payload(payload, payload_json(payload))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(payload), encoding="utf-8")
    return path
