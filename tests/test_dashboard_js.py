import shutil
import subprocess
from pathlib import Path

import pytest

from src import config, dashboard, profiling
from src.segmentos import SEGMENTOS

SMOKE = Path(__file__).with_name("dashboard_smoke.js")


@pytest.mark.skipif(shutil.which("node") is None, reason="hace falta node para ejecutar el JS del dashboard")
@pytest.mark.parametrize("tema", ["light", "dark"])
def test_dashboard_se_dibuja_bien(clientes, etiquetas, tmp_path, tema):
    ruta = dashboard.write_dashboard(clientes, etiquetas, tmp_path / "d.html",
                                     segmentos={0: dict(SEGMENTOS[0]), 1: dict(SEGMENTOS[1])})
    res = subprocess.run(["node", str(SMOKE), str(ruta), tema], capture_output=True, text=True)
    assert res.returncode == 0, res.stdout + res.stderr


def test_requirements_incluye_jinja2():
    paquetes = {line.split("==")[0].strip().lower()
                for line in (config.ROOT / "requirements.txt").read_text().splitlines() if line.strip()}
    assert "jinja2" in paquetes


def test_telemetria_no_se_llama_conectado():
    # has_telemetry = hay datos de uso; "conectado" choca con "sin coche activo" en Desconectados
    spec = profiling.KPIS["pct_telemetria"]
    assert "conect" not in (spec["label"] + spec["short"]).lower()
