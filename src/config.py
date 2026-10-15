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
