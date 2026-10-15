"""Rutas y constantes compartidas por todos los notebooks."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Datos
RAW_CSV = ROOT / "datos_reto_mercedes_benz_malackathon.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
CLIENTS_PKL = PROCESSED_DIR / "clients.pkl"
X_NPY = PROCESSED_DIR / "X.npy"
FEATURE_NAMES_JSON = PROCESSED_DIR / "feature_names.json"

# Salidas
OUTPUTS_DIR = ROOT / "outputs"
FIG_DIR = OUTPUTS_DIR / "figuras"
LABELS_V0 = OUTPUTS_DIR / "labels_v0.csv"
LABELS_FINAL = OUTPUTS_DIR / "labels_final.csv"

# Constantes del análisis
REF_DATE = "2026-10-15"   # fecha de referencia para calcular antigüedades
RANDOM_STATE = 42
SILHOUETTE_SAMPLE = 20_000
K_RANGE = range(2, 13)
K_FINAL = 7               # elegido en el reto 3 (notebook 03_kmeans)

AGE_ORDER = ["<25", "25-34", "35-44", "45-54", "55-64", "65+"]

# Colores de los segmentos (0-6), los mismos en el notebook 04 y en el dashboard.
# Paleta categórica validada (slots 1-7) para fondo claro y oscuro; el total va en gris.
SEGMENT_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]
SEGMENT_COLORS_DARK = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9"]
BASE_GRAY = "#a3a29c"
