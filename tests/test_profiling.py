import pytest

from src import profiling


def test_tamanos_y_pct(clientes, etiquetas):
    p = profiling.build_profile(clientes, etiquetas)
    assert [s["n"] for s in p["segmentos"]] == [3, 3]
    assert [s["pct"] for s in p["segmentos"]] == [50.0, 50.0]
    assert p["meta"]["n"] == 6
    assert p["meta"]["k"] == 2


def test_kpi_es_media_del_segmento(clientes, etiquetas):
    p = profiling.build_profile(clientes, etiquetas)
    assert p["segmentos"][0]["kpis"]["antiguedad_meses"] == pytest.approx((10 + 20 + 60) / 3)


def test_z_es_diferencia_en_desviaciones(clientes, etiquetas):
    p = profiling.build_profile(clientes, etiquetas)
    total = clientes["tenure_months"]
    esperado = ((10 + 20 + 60) / 3 - total.mean()) / total.std(ddof=1)
    assert p["segmentos"][0]["z"]["antiguedad_meses"] == pytest.approx(esperado)


def test_categoria_ausente_sale_con_cero(clientes, etiquetas):
    p = profiling.build_profile(clientes, etiquetas)
    assert p["segmentos"][0]["dist"]["clase"]["FURGONETA"] == 0.0
    for dim, base_dist in p["base"]["dist"].items():
        for seg in p["segmentos"]:
            assert list(seg["dist"][dim]) == list(base_dist)


def test_distribuciones_suman_100(clientes, etiquetas):
    p = profiling.build_profile(clientes, etiquetas)
    for stats in [p["base"], *p["segmentos"]]:
        for dist in stats["dist"].values():
            assert sum(dist.values()) == pytest.approx(100, abs=0.1)


def test_uso_solo_con_dato(clientes, etiquetas):
    seg0 = profiling.build_profile(clientes, etiquetas)["segmentos"][0]
    assert seg0["uso"]["cobertura"] == pytest.approx(2 / 3 * 100)
    assert seg0["uso"]["horas_mediana"] == pytest.approx(200.0)  # mediana de 100 y 300 (c2 no tiene dato)


def test_rasgos_son_los_de_mayor_z_absoluto(clientes, etiquetas):
    seg = profiling.build_profile(clientes, etiquetas)["segmentos"][1]
    esperado = sorted(seg["z"], key=lambda k: abs(seg["z"][k]), reverse=True)[:3]
    assert seg["rasgos"] == esperado
    assert profiling.build_profile(clientes, etiquetas)["base"]["rasgos"] == []


def test_etiquetas_desordenadas_se_alinean(clientes, etiquetas):
    p1 = profiling.build_profile(clientes, etiquetas)
    p2 = profiling.build_profile(clientes, etiquetas.sort_index())
    assert p1 == p2
    assert p1["segmentos"][0]["kpis"]["antiguedad_meses"] == pytest.approx(30.0)


def test_cliente_sin_etiqueta_falla(clientes, etiquetas):
    with pytest.raises(ValueError, match="sin etiqueta"):
        profiling.build_profile(clientes, etiquetas.drop("c4"))


def test_check_profile_detecta_suma_mala(clientes, etiquetas):
    p = profiling.build_profile(clientes, etiquetas)
    profiling.check_profile(p)
    p["segmentos"][0]["n"] += 1
    with pytest.raises(AssertionError):
        profiling.check_profile(p)
