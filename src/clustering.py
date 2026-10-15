"""Utilidades de clustering que comparten los retos 3 (K-Means), A1 (comparativa) y A3 (Jackknife)."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import davies_bouldin_score, silhouette_score

from src import config


def sample_index(n, size=config.SILHOUETTE_SAMPLE, random_state=config.RANDOM_STATE):
    """Índices de una muestra fija. El silhouette sobre 173k clientes es demasiado lento
    (compara todos con todos), así que lo calculamos siempre sobre la misma muestra."""
    rng = np.random.default_rng(random_state)
    return rng.choice(n, size=min(size, n), replace=False)


def k_sweep(X, k_range=config.K_RANGE, random_state=config.RANDOM_STATE):
    """Entrena K-Means para cada k y devuelve sus métricas en una tabla."""
    idx = sample_index(len(X))
    rows = []
    for k in k_range:
        km = KMeans(n_clusters=k, n_init=10, random_state=random_state).fit(X)
        labels = km.labels_
        rows.append({
            "k": k,
            "inercia": km.inertia_,
            "silhouette": silhouette_score(X[idx], labels[idx]),
            "davies_bouldin": davies_bouldin_score(X, labels),
            "cluster_min_pct": np.bincount(labels).min() / len(labels) * 100,
        })
    return pd.DataFrame(rows).set_index("k")


def relabel_by_size(labels):
    """Renumera los clusters por tamaño (0 = el más grande). K-Means numera al azar,
    así un cluster conserva su número aunque re-entrenemos."""
    labels = np.asarray(labels)
    order = np.argsort(-np.bincount(labels), kind="stable")
    mapping = np.empty_like(order)
    mapping[order] = np.arange(len(order))
    return mapping[labels]


def save_labels(labels, index, path=config.LABELS_FINAL):
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.Series(labels, index=pd.Index(index, name="client_id"), name="cluster").to_csv(path)


def load_labels(path=config.LABELS_FINAL):
    """Serie con el cluster de cada cliente (índice = client_id)."""
    return pd.read_csv(path, index_col="client_id")["cluster"]
