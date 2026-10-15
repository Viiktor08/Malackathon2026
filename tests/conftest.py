import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def clientes():
    """6 clientes inventados: segmento 0 = c1-c3, segmento 1 = c4-c6.
    Solo el segmento 1 tiene FURGONETA y c2 no tiene telemetría."""
    return pd.DataFrame(
        {
            "tenure_months": [10, 20, 60, 30, 40, 50],
            "main_vehicle_age": [1.0, 2.0, 3.0, 8.0, 9.0, 7.0],
            "n_vehicles": [1, 1, 2, 1, 3, 1],
            "n_connected_now": [1, 1, 2, 0, 1, 1],
            "workshop_visits_mean": [0.0, 1.0, 2.0, 4.0, 3.0, 5.0],
            "ppi": [40000.0, 50000.0, 60000.0, 30000.0, 30000.0, 45000.0],
            "country_code": ["CH", "CH", "CH", "AT", "AT", "CH"],
            "share_plugin_ev": [1.0, 0.0, 0.5, 0.0, 0.0, np.nan],
            "has_current_vehicle": [1, 1, 1, 0, 1, 1],
            "finance_leasing_status": ["active_FL_only", "never_active", "never_active",
                                       "was_active", "never_active", "active_FL_and_CASH"],
            "has_telemetry": [1, 0, 1, 1, 1, 1],
            "op_hours_mean": [100.0, np.nan, 300.0, 50.0, 70.0, 90.0],
            "fuel_cons_avg": [6.0, np.nan, 8.0, 9.0, 10.0, 11.0],
            "consent_phone": [1, 1, 0, 1, 1, 1],
            "consent_epost": [1, 1, 1, 1, 1, 0],
            "consent_post": [0, 1, 1, 1, 0, 1],
            "age_range": ["25-34", "35-44", "65+", "45-54", "45-54", "55-64"],
            "main_class_group": ["COMPACTO", "MEDIO", "COMPACTO", "FURGONETA", "MEDIO", "COMPACTO"],
            "main_engine": ["ELECTRIC", "COMBUSTION", "PLUGIN_HYBRID", "COMBUSTION", "UNKNOWN", "COMBUSTION"],
        },
        index=pd.Index(["c1", "c2", "c3", "c4", "c5", "c6"], name="client_id"),
    )


@pytest.fixture
def etiquetas():
    """Etiquetas en orden distinto al de la tabla de clientes."""
    return pd.Series([1, 0, 1, 0, 1, 0], index=pd.Index(["c6", "c3", "c4", "c1", "c5", "c2"], name="client_id"),
                     name="cluster")
