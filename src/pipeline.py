"""Pipeline de preparación: tabla de clientes -> matriz X lista para clustering.

Pasos:
  1. CountryMedianImputer  -> rellena poder adquisitivo / población con la mediana de su país
                              y crea ppi_rel (poder adquisitivo relativo a su país)
  2. ColumnTransformer     -> por tipo de variable:
       - con cola larga: mediana -> log1p -> recorte p1-p99 -> escalado
       - numéricas:      mediana -> recorte p1-p99 -> escalado
       - binarias:       tal cual (0/1)
       - categóricas:    one-hot
  3. (opcional) KMeans

build_full_pipeline() añade delante la construcción de la tabla, así el pipeline va del CSV a X.
"""
import json

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, OneToOneFeatureMixin, TransformerMixin
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from src import clean, config

# --- Qué entra al modelo ----------------------------------------------------

LOG_COLS = ["n_vehicles", "n_connected_now", "population", "workshop_visits_mean", "ppi_rel"]
NUM_COLS = ["age_ord", "tenure_months", "main_vehicle_age", "share_plugin_ev"]
BIN_COLS = ["is_ch", "is_b2b", "tenure_is_default", "has_telemetry"]
CAT_COLS = ["main_class_group", "main_engine", "finance_leasing_status"]

# Variante con telemetría (ablación del reto 3)
TELEMETRY_LOG_COLS = ["trip_dist_avg", "fuel_cons_avg", "op_hours_mean"]
TELEMETRY_NUM_COLS = ["speed_avg"]


def feature_columns(telemetry=False):
    """Columnas de la tabla de clientes que usa el modelo, por bloque."""
    log_cols = LOG_COLS + (TELEMETRY_LOG_COLS if telemetry else [])
    num_cols = NUM_COLS + (TELEMETRY_NUM_COLS if telemetry else [])
    return log_cols, num_cols, BIN_COLS, CAT_COLS


# --- Transformers propios ---------------------------------------------------

class CountryMedianImputer(BaseEstimator, TransformerMixin):
    """Rellena nulos con la mediana del país del cliente (AT y CH tienen niveles
    muy distintos) y crea `<col>_rel` = valor / mediana de su país."""

    def __init__(self, cols=("ppi", "population"), relative=("ppi",), country_col="country_code"):
        self.cols = cols
        self.relative = relative
        self.country_col = country_col

    def fit(self, X, y=None):
        self.medians_ = X.groupby(self.country_col)[list(self.cols)].median()
        self.feature_names_out_ = np.array(list(X.columns) + [f"{c}_rel" for c in self.relative])
        return self

    def get_feature_names_out(self, input_features=None):
        return self.feature_names_out_

    def transform(self, X):
        X = X.copy()
        med = self.medians_.reindex(X[self.country_col])
        med.index = X.index
        for c in self.cols:
            X[c] = X[c].fillna(med[c])
        for c in self.relative:
            X[f"{c}_rel"] = X[c] / med[c]
        return X


class QuantileClipper(OneToOneFeatureMixin, BaseEstimator, TransformerMixin):
    """Recorta cada columna a sus percentiles [low, high], aprendidos en fit."""

    def __init__(self, low=0.01, high=0.99):
        self.low = low
        self.high = high

    def fit(self, X, y=None):
        X = np.asarray(X, dtype=float)
        self.lo_ = np.nanquantile(X, self.low, axis=0)
        self.hi_ = np.nanquantile(X, self.high, axis=0)
        self.n_features_in_ = X.shape[1]
        return self

    def transform(self, X):
        return np.clip(np.asarray(X, dtype=float), self.lo_, self.hi_)


# --- Pipelines --------------------------------------------------------------

def build_preprocessor(telemetry=False):
    log_cols, num_cols, bin_cols, cat_cols = feature_columns(telemetry)
    log1p = FunctionTransformer(np.log1p, feature_names_out="one-to-one")
    columns = ColumnTransformer(
        [
            ("log", Pipeline([("imputar", SimpleImputer(strategy="median")), ("log1p", log1p),
                              ("recortar", QuantileClipper()), ("escalar", StandardScaler())]), log_cols),
            ("num", Pipeline([("imputar", SimpleImputer(strategy="median")),
                              ("recortar", QuantileClipper()), ("escalar", StandardScaler())]), num_cols),
            ("bin", "passthrough", bin_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
        ],
        verbose_feature_names_out=False,
    )
    return Pipeline([("pais", CountryMedianImputer()), ("columnas", columns)])


def build_pipeline(k, telemetry=False, random_state=config.RANDOM_STATE):
    """Preprocesado + K-Means. Es lo que re-entrena el Jackknife."""
    return Pipeline([
        ("prep", build_preprocessor(telemetry)),
        ("kmeans", KMeans(n_clusters=k, n_init=10, random_state=random_state)),
    ])


def build_full_pipeline(telemetry=False):
    """Del CSV crudo a X: construcción de la tabla de clientes + preprocesado."""
    return Pipeline([
        ("tabla_clientes", FunctionTransformer(clean.build_client_table)),
        ("prep", build_preprocessor(telemetry)),
    ])


# --- Guardar / cargar X -----------------------------------------------------

def save_X(X, feature_names, index):
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    np.save(config.X_NPY, X)
    with open(config.FEATURE_NAMES_JSON, "w") as f:
        json.dump({"features": list(feature_names), "client_id": list(index)}, f)


def load_X():
    """Devuelve (X, nombres de columnas, client_id de cada fila)."""
    X = np.load(config.X_NPY)
    with open(config.FEATURE_NAMES_JSON) as f:
        meta = json.load(f)
    return X, meta["features"], pd.Index(meta["client_id"], name="client_id")
