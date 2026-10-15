"""Perfil de los segmentos: todas las cifras del reto 4 salen de aquí.

El notebook 04 y el dashboard leen este perfil, así que no pueden dar números distintos.
Cada segmento se compara siempre con el total de clientes ("base").
"""
import pandas as pd

from src import config

# Indicadores que enseñamos por segmento: etiqueta, unidad y decimales al mostrarlos
KPIS = {
    "antiguedad_meses": {"short": "Antigüedad", "label": "Antigüedad como cliente", "unit": "meses", "decimals": 0},
    "edad_coche": {"short": "Edad coche", "label": "Edad del coche principal", "unit": "años", "decimals": 1},
    "n_vehiculos": {"short": "Vehículos", "label": "Vehículos que ha tenido", "unit": "", "decimals": 1},
    "vehiculos_activos": {"short": "Activos", "label": "Vehículos activos", "unit": "", "decimals": 1},
    "visitas_taller": {"short": "Taller", "label": "Visitas al taller por coche", "unit": "", "decimals": 1},
    "riqueza_relativa": {"short": "Riqueza rel.", "label": "Poder adquisitivo frente a su país", "unit": "×", "decimals": 2},
    "pct_electrificado": {"short": "Electrificado", "label": "Con eléctrico o enchufable", "unit": "%", "decimals": 1},
    "pct_telemetria": {"short": "Conectado", "label": "Con coche conectado", "unit": "%", "decimals": 1},
    "pct_sin_activo": {"short": "Sin coche activo", "label": "Sin ningún coche activo", "unit": "%", "decimals": 1},
    "pct_leasing_activo": {"short": "Leasing activo", "label": "Con leasing activo", "unit": "%", "decimals": 1},
    "pct_leasing_terminado": {"short": "Leasing terminado", "label": "Con leasing terminado", "unit": "%", "decimals": 1},
}

# Columnas de la tabla de clientes que van tal cual como indicador
_DIRECT = {
    "antiguedad_meses": "tenure_months",
    "edad_coche": "main_vehicle_age",
    "n_vehiculos": "n_vehicles",
    "vehiculos_activos": "n_connected_now",
    "visitas_taller": "workshop_visits_mean",
}

# Distribuciones que enseñamos (segmento frente a total)
DIMS = {
    "edad": "age_range",
    "pais": "country_code",
    "clase": "main_class_group",
    "motor": "main_engine",
    "leasing": "finance_leasing_status",
}

_CANALES = {"telefono": "consent_phone", "email": "consent_epost", "correo": "consent_post"}
N_RASGOS = 3


def fmt_num(x, decimals):
    """Número en formato español: 1.234,5. Nulos → «—»."""
    if x is None or pd.isna(x):
        return "—"
    x = round(float(x), decimals)
    if x == 0:
        x = 0.0  # evita «-0,0»
    return f"{x:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_kpi(key, value):
    """Valor de un indicador con sus decimales y su unidad («11,7 %», «17 meses», «1,82×»)."""
    spec = KPIS[key]
    num = fmt_num(value, spec["decimals"])
    if spec["unit"] == "×":
        return f"{num}×"
    return f"{num} {spec['unit']}" if spec["unit"] else num


def add_profile_columns(clients):
    """Añade una columna por indicador. Las pct_* van en 0/1 (se pasan a % al agregar)."""
    df = clients.copy()
    for key, col in _DIRECT.items():
        df[key] = df[col]
    df["riqueza_relativa"] = df["ppi"] / df.groupby("country_code")["ppi"].transform("median")
    df["pct_electrificado"] = (df["share_plugin_ev"] > 0).astype(float)
    df["pct_telemetria"] = df["has_telemetry"].astype(float)
    df["pct_sin_activo"] = (df["has_current_vehicle"] == 0).astype(float)
    df["pct_leasing_activo"] = df["finance_leasing_status"].str.startswith("active").astype(float)
    df["pct_leasing_terminado"] = (df["finance_leasing_status"] == "was_active").astype(float)
    return df


def _categories(df):
    """Categorías de cada distribución, fijadas a partir del total."""
    cats = {}
    for dim, col in DIMS.items():
        if dim == "edad":
            cats[dim] = [a for a in config.AGE_ORDER if a in set(df[col])]
        else:
            cats[dim] = list(df[col].value_counts().index)
    return cats


def _stats(df, seg_id, n_total, base_mean, base_std, cats):
    means = df[list(KPIS)].mean()
    kpis = {k: float(means[k] * 100 if KPIS[k]["unit"] == "%" else means[k]) for k in KPIS}
    if seg_id is None:
        z = {k: 0.0 for k in KPIS}
    else:
        z = {k: float((means[k] - base_mean[k]) / base_std[k]) for k in KPIS}
    dist = {
        dim: {str(c): float(v) for c, v in
              (df[col].value_counts(normalize=True) * 100).reindex(cats[dim], fill_value=0.0).items()}
        for dim, col in DIMS.items()
    }
    return {
        "id": seg_id,
        "n": int(len(df)),
        "pct": float(len(df) / n_total * 100),
        "kpis": kpis,
        "z": z,
        "dist": dist,
        "uso": {
            "cobertura": float(df["has_telemetry"].mean() * 100),
            "horas_mediana": float(df["op_hours_mean"].median()),
            "consumo_mediana": float(df["fuel_cons_avg"].median()),
        },
        "canales": {k: float(df[col].mean() * 100) for k, col in _CANALES.items()},
        "rasgos": [] if seg_id is None else sorted(z, key=lambda k: abs(z[k]), reverse=True)[:N_RASGOS],
    }


def build_profile(clients, labels):
    """Perfil del total y de cada segmento. `labels` se alinea por client_id."""
    aligned = labels.reindex(clients.index)
    missing = int(aligned.isna().sum())
    if missing:
        raise ValueError(f"{missing} clientes sin etiqueta de segmento")
    df = add_profile_columns(clients).assign(segmento=aligned.astype(int).values)

    n_total = len(df)
    base_mean = df[list(KPIS)].mean()
    base_std = df[list(KPIS)].std(ddof=1)
    cats = _categories(df)
    seg_ids = sorted(df["segmento"].unique())
    return {
        "meta": {"n": int(n_total), "k": len(seg_ids)},
        "base": _stats(df, None, n_total, base_mean, base_std, cats),
        "segmentos": [_stats(df[df["segmento"] == s], int(s), n_total, base_mean, base_std, cats)
                      for s in seg_ids],
    }


def check_profile(profile):
    """Comprobaciones de coherencia: si algo no cuadra, falla."""
    total = sum(s["n"] for s in profile["segmentos"])
    assert total == profile["meta"]["n"], f"los segmentos suman {total}, no {profile['meta']['n']}"
    for stats in [profile["base"], *profile["segmentos"]]:
        for dim, dist in stats["dist"].items():
            suma = sum(dist.values())
            assert abs(suma - 100) <= 0.1, f"segmento {stats['id']}, {dim}: suma {suma:.2f} %"
