"""Construcción de la tabla a nivel cliente (una fila por client_id).

El CSV viene a nivel cliente-vehículo. Aquí lo pasamos a nivel cliente en 4 pasos:
  1. load_raw            -> leer el CSV
  2. prepare_vehicles    -> columnas nuevas por vehículo (antigüedad, grupo de clase, motor)
  3. client_attributes   -> columnas que ya son del cliente (constantes en todas sus filas)
     pick_main_vehicle   -> el vehículo que representa al cliente
     aggregate_vehicles  -> resúmenes de todos sus vehículos
  4. build_client_table  -> junta todo

La tabla NO imputa ni escala: deja los nulos tal cual. Eso lo hace el pipeline de sklearn.
"""
import numpy as np
import pandas as pd

from src import config

# --- Constantes -------------------------------------------------------------

# Columnas que son constantes dentro de cada cliente (lo comprobamos en el notebook 00)
CLIENT_COLS = [
    "age_range", "gender_derived", "country_code", "months_as_mb_customer",
    "currently_connected_vehicles", "finance_leasing_status",
    "consent_phone_communication_channel", "consent_epost_communication_channel",
    "consent_post_communication_channel", "purchasing_power_per_inhabitant_eur",
    "population",
]

TELEMETRY_COLS = {
    "trip_distance_average": "trip_dist_avg",
    "speed_average": "speed_avg",
    "fuel_consumption_average": "fuel_cons_avg",
    "operating_hours_total": "op_hours_mean",
}

# Agrupamos las 42 clases por segmento de mercado (tamaño / precio / uso).
# La electrificación NO entra aquí: va en la columna de motor.
CLASS_GROUPS = {
    "COMPACTO": [
        "A-Class", "B-Class", "B-/GLA-/GLB-Class", "GLA-Class", "CLA-Class",
        "A-Class/CLA-Class", "EQA-/EQB-Class", "fortwo / forfour",
    ],
    "MEDIO": ["C-Class", "GLC-Class", "CLE-Class", "EQC-Class", "CLK-Class"],
    "EJECUTIVO": ["E-Class", "E-Class Coupé/Cabriolet", "CLS-Class", "EQE-Class"],
    "SUV_GRANDE": [
        "GLE-/GLS-Class", "GLE-Class", "M-/GL-/GLE-/GLS-Class", "M-/GL-Class",
        "M-Class", "R-Class",
    ],
    "LUJO_DEPORTIVO": [
        "S-Class", "S-Class Coupé/Cabriolet", "EQS-Class", "G-Class", "AMG GT",
        "AMG GT 4-Door", "SL-Class", "SLK-/SLC-Class", "SLK-Class", "SLS AMG",
        "AMG ONE", "CL-Class", "SLR McLaren", "Maybach",
    ],
    "FURGONETA": ["V-Class / Vito", "Viano/Vito", "Sprinter", "Citan", "X-Class"],
}
CLASS_TO_GROUP = {cls: grp for grp, classes in CLASS_GROUPS.items() for cls in classes}

# Clases 100 % eléctricas por definición (familia EQ): sirven para rellenar el motor
EV_CLASSES = ["EQA-/EQB-Class", "EQC-Class", "EQE-Class", "EQS-Class"]
PLUGIN_OR_EV = ["PLUGIN_HYBRID", "ELECTRIC"]

# Imputación del motor desde vehicle_type: solo versiones fiables
ENGINE_MAP_MIN_PURITY = 0.90   # el motor más frecuente de la versión cubre >= 90 % de sus filas conocidas
ENGINE_MAP_MIN_ROWS = 5        # y la versión tiene al menos 5 filas con motor conocido

# months_as_mb_customer = 36 aparece ~9 veces más que sus vecinos (lo vio el EDA): valor por defecto
TENURE_DEFAULT = 36
HEAVY_ACCOUNT_MIN_VEHICLES = 20


# --- Paso 1 -----------------------------------------------------------------

def load_raw(path=config.RAW_CSV):
    """Lee el CSV. La primera columna es un índice sin nombre de la exportación."""
    df = pd.read_csv(path, index_col=0, low_memory=False)
    df["date_of_first_registration"] = pd.to_datetime(df["date_of_first_registration"])
    return df


# --- Paso 2 -----------------------------------------------------------------

def engine_map_from_vehicle_type(df):
    """Motor más frecuente de cada vehicle_type, solo para las versiones fiables
    (ver ENGINE_MAP_MIN_PURITY y ENGINE_MAP_MIN_ROWS)."""
    known = df.loc[df["engine_concept"].notna(), ["vehicle_type", "engine_concept"]]
    counts = known.value_counts().rename("n").reset_index()
    total = counts.groupby("vehicle_type")["n"].transform("sum")
    top = counts.assign(total=total, purity=counts["n"] / total).drop_duplicates("vehicle_type")
    ok = top[(top["purity"] >= ENGINE_MAP_MIN_PURITY) & (top["total"] >= ENGINE_MAP_MIN_ROWS)]
    return ok.set_index("vehicle_type")["engine_concept"]


def prepare_vehicles(df, ref_date=config.REF_DATE):
    """Añade columnas a nivel vehículo que luego agregamos por cliente."""
    df = df.copy()
    ref = pd.Timestamp(ref_date)
    df["vehicle_age_years"] = (ref - df["date_of_first_registration"]).dt.days / 365.25
    df["class_group"] = df["model_class"].map(CLASS_TO_GROUP).fillna("OTRO")

    # Motor: 1) el dato original, 2) la versión comercial (vehicle_type), 3) familia EQ
    engine = df["engine_concept"].fillna(df["vehicle_type"].map(engine_map_from_vehicle_type(df)))
    engine[engine.isna() & df["model_class"].isin(EV_CLASSES)] = "ELECTRIC"
    df["engine_known"] = engine.notna()
    df["engine"] = engine.fillna("UNKNOWN")
    df["is_plugin_ev"] = df["engine"].isin(PLUGIN_OR_EV)

    df["has_telemetry_row"] = df[list(TELEMETRY_COLS)].notna().any(axis=1)
    return df


# --- Paso 3 -----------------------------------------------------------------

def client_attributes(df):
    """Columnas del cliente: cogemos la primera fila de cada uno (son constantes)."""
    g = df.groupby("client_id")
    out = g[CLIENT_COLS].first()
    out = out.rename(columns={
        "months_as_mb_customer": "tenure_months",
        "currently_connected_vehicles": "n_connected_now",
        "consent_phone_communication_channel": "consent_phone",
        "consent_epost_communication_channel": "consent_epost",
        "consent_post_communication_channel": "consent_post",
        "purchasing_power_per_inhabitant_eur": "ppi",
    })
    out["age_ord"] = out["age_range"].map({a: i for i, a in enumerate(config.AGE_ORDER)})
    out["is_ch"] = (out["country_code"] == "CH").astype(int)
    # role_type cambia entre vehículos en ~1 % de clientes: es B2B si lo es en alguno
    out["is_b2b"] = (df["role_type"] == "B2B").groupby(df["client_id"]).any().astype(int)
    for c in ["consent_phone", "consent_epost", "consent_post"]:
        out[c] = out[c].astype(int)
    out["n_consents"] = out[["consent_phone", "consent_epost", "consent_post"]].sum(axis=1)
    out["tenure_is_default"] = (out["tenure_months"] == TENURE_DEFAULT).astype(int)
    return out


def pick_main_vehicle(df):
    """Vehículo principal: el actual matriculado más recientemente; si no tiene
    ninguno actual, el más reciente de todos. vehicle_id desempata para que sea
    determinista."""
    main = (
        df.sort_values(
            ["client_id", "is_current_vehicle", "date_of_first_registration", "vehicle_id"],
            ascending=[True, False, False, True],
            na_position="last",
        )
        .drop_duplicates("client_id")
        .set_index("client_id")
    )
    return pd.DataFrame({
        "main_model_class": main["model_class"],
        "main_class_group": main["class_group"],
        "main_engine": main["engine"],
        "main_product_group": main["product_group"],
        "main_vehicle_age": main["vehicle_age_years"],
    })


def aggregate_vehicles(df):
    """Resúmenes de todos los vehículos del cliente."""
    g = df.groupby("client_id")
    # El nº de vehículos actuales coincide con currently_connected_vehicles
    # (salvo 4 clientes), así que no lo guardamos: solo el flag
    out = pd.DataFrame({
        "n_vehicles": g.size(),
        "has_current_vehicle": g["is_current_vehicle"].any().astype(int),
        "fleet_age_mean": g["vehicle_age_years"].mean(),
        "workshop_visits_mean": g["workshop_visits_warranty_goodwill"].mean(),
        "has_telemetry": g["has_telemetry_row"].any().astype(int),
    })
    out["is_heavy_account"] = (out["n_vehicles"] >= HEAVY_ACCOUNT_MIN_VEHICLES).astype(int)

    # % plug-in/eléctricos sobre los vehículos con motor conocido (NaN si no hay ninguno)
    n_known = g["engine_known"].sum()
    n_pe = g["is_plugin_ev"].sum()
    out["share_plugin_ev"] = (n_pe / n_known).where(n_known > 0)

    # Telemetría: media de cada campo entre los vehículos que lo tienen
    for raw, new in TELEMETRY_COLS.items():
        out[new] = g[raw].mean()
    return out


# --- Paso 4 -----------------------------------------------------------------

def build_client_table(df_raw):
    """CSV crudo -> tabla con una fila por cliente (índice = client_id)."""
    veh = prepare_vehicles(df_raw)
    clients = (
        client_attributes(veh)
        .join(pick_main_vehicle(veh))
        .join(aggregate_vehicles(veh))
    )
    assert clients.index.is_unique
    return clients


def save_clients(clients, path=config.CLIENTS_PKL):
    path.parent.mkdir(parents=True, exist_ok=True)
    clients.to_pickle(path)


def load_clients(path=config.CLIENTS_PKL):
    return pd.read_pickle(path)
