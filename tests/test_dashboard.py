import json
import re

import numpy as np
import pytest

from src import dashboard, profiling
from src.segmentos import SEGMENTOS


@pytest.fixture
def segmentos_prueba():
    return {0: dict(SEGMENTOS[0]), 1: dict(SEGMENTOS[1])}


@pytest.fixture
def perfil(clientes, etiquetas):
    return profiling.build_profile(clientes, etiquetas)


def test_payload_sin_nan_y_json_estricto(clientes, etiquetas, segmentos_prueba):
    sin_tele = clientes.copy()
    seg0 = etiquetas[etiquetas == 0].index
    sin_tele.loc[seg0, "has_telemetry"] = 0
    sin_tele.loc[seg0, ["op_hours_mean", "fuel_cons_avg"]] = np.nan
    payload = dashboard.build_payload(profiling.build_profile(sin_tele, etiquetas), segmentos_prueba)
    datos = json.loads(dashboard.payload_json(payload))
    assert datos["segmentos"][0]["uso"]["horas_mediana"] is None


def test_json_escapa_cierre_de_script(perfil, segmentos_prueba):
    segmentos_prueba[0]["frase"] = "texto con </script><script>alert(1)</script> dentro"
    texto = dashboard.payload_json(dashboard.build_payload(perfil, segmentos_prueba))
    assert "</script>" not in texto
    assert json.loads(texto)["segmentos"][0]["frase"].startswith("texto con </script>")


def test_check_payload_rechaza_client_id(perfil, segmentos_prueba):
    payload = dashboard.build_payload(perfil, segmentos_prueba)
    dashboard.check_payload(payload, dashboard.payload_json(payload))
    payload["base"]["client_id"] = "abc"
    with pytest.raises(AssertionError):
        dashboard.check_payload(payload, dashboard.payload_json(payload))


def test_html_autonomo(perfil, segmentos_prueba):
    html = dashboard.render(dashboard.build_payload(perfil, segmentos_prueba))
    externo = re.compile(r"""(src|href)\s*=\s*["']?\s*(https?:)?//|url\(\s*["']?\s*(https?:)?//|@import""", re.I)
    assert not externo.search(html)
    for seg in segmentos_prueba.values():
        assert seg["nombre"] in html


def test_write_dashboard_escribe_fichero(clientes, etiquetas, segmentos_prueba, tmp_path):
    ruta = dashboard.write_dashboard(clientes, etiquetas, tmp_path / "d.html", segmentos=segmentos_prueba)
    assert ruta.exists()
    assert ruta.read_text(encoding="utf-8").lower().startswith("<!doctype html>")
