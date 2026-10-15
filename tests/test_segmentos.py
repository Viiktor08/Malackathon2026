import re

import pytest

from src import config, profiling
from src.profiling import fmt_kpi, fmt_num
from src.segmentos import SEGMENTOS, check_segmentos, fill_texts


def _stats(**kpis):
    valores = {k: 1.0 for k in profiling.KPIS}
    valores.update(kpis)
    return {"id": 4, "n": 15660, "pct": 9.03, "kpis": valores}


def _textos(seg):
    yield seg["slug"]
    yield seg["nombre"]
    yield seg["frase"]
    yield seg["accion"]
    yield from seg["etiquetas"]
    yield from seg["plan"].values()


def test_fmt_num():
    assert fmt_num(173456, 0) == "173.456"
    assert fmt_num(1234.56, 1) == "1.234,6"
    assert fmt_num(-0.54, 1) == "-0,5"
    assert fmt_num(float("nan"), 1) == "—"
    assert fmt_num(None, 1) == "—"


def test_fmt_kpi():
    assert fmt_kpi("pct_leasing_terminado", 11.66) == "11,7 %"
    assert fmt_kpi("antiguedad_meses", 17.36) == "17 meses"
    assert fmt_kpi("riqueza_relativa", 1.823) == "1,82×"
    assert fmt_kpi("vehiculos_activos", 1.04) == "1,0"


def test_fill_texts_rellena_huecos():
    seg = dict(SEGMENTOS[4], frase="el {pct_leasing_terminado} tiene leasing terminado")
    relleno = fill_texts(seg, _stats(pct_leasing_terminado=11.66))
    assert relleno["frase"] == "el 11,7 % tiene leasing terminado"


def test_fill_texts_rellena_etiquetas_y_plan():
    seg = dict(SEGMENTOS[4], etiquetas=["{n} clientes", "{pct}", "x"], plan=dict(SEGMENTOS[4]["plan"], medir="{edad_coche}"))
    relleno = fill_texts(seg, _stats(edad_coche=5.63))
    assert relleno["etiquetas"][:2] == ["15.660 clientes", "9,0 %"]
    assert relleno["plan"]["medir"] == "5,6 años"


def test_fill_texts_hueco_mal_escrito_falla():
    seg = dict(SEGMENTOS[4], frase="{pct_leasing_termindo}")
    with pytest.raises(KeyError) as err:
        fill_texts(seg, _stats())
    assert "4" in str(err.value) and "pct_leasing_termindo" in str(err.value)


def test_check_segmentos_detecta_falta_de_campos():
    roto = {i: dict(s) for i, s in SEGMENTOS.items()}
    roto[2]["frase"] = ""
    with pytest.raises(AssertionError):
        check_segmentos(roto, 7)
    with pytest.raises(AssertionError):
        check_segmentos(SEGMENTOS, 6)


def test_textos_sin_numeros_fijos():
    for seg_id, seg in SEGMENTOS.items():
        for texto in _textos(seg):
            sin_huecos = re.sub(r"\{[^}]*\}", "", texto)
            assert not re.search(r"\d", sin_huecos), f"segmento {seg_id}: número fijo en «{texto}»"


def test_segmentos_reales_completos():
    if not (config.CLIENTS_PKL.exists() and config.LABELS_FINAL.exists()):
        pytest.skip("faltan clients.pkl o labels_final.csv (ejecutar los notebooks 02a y 03)")
    from src import clean, clustering
    perfil = profiling.build_profile(clean.load_clients(), clustering.load_labels())
    check_segmentos(SEGMENTOS, perfil["meta"]["k"])
    for stats in perfil["segmentos"]:
        fill_texts(SEGMENTOS[stats["id"]], stats)
