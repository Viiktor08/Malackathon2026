# Resumen · Malackathon 2026 · Mercedes-Benz "Clustering the Star"

## B1 · Hallazgos del EDA

Notebook: [`notebooks/01_eda_calidad.ipynb`](../notebooks/01_eda_calidad.ipynb). Cada cifra de esta sección está verificada en el notebook con un `assert` o una tabla. Las cifras son a nivel cliente (173.456 clientes) salvo que se indique lo contrario.

### ¿Cuáles son las principales características de los clientes?

| Dimensión | Dato | Lectura para marketing |
|---|---|---|
| Mercado | 66 % Suiza, 34 % Austria. Poder adquisitivo mediano por habitante: 51k € (CH) frente a 30k € (AT) | Dos mercados con niveles económicos muy distintos. Ofertas, precios y gama se calibran por país |
| Edad | 61 % tiene 45+ años y el 20 % tiene 65+. Solo un 4,7 % tiene menos de 25 | Prioridad: fidelizar al cliente sénior. El cliente joven es un nicho de captación (gama compacta, renting) |
| Género (inferido) | 65 % hombres, 18 % mujeres, 17 % desconocido | Solo para describir, no para dirigir campañas (D4) |
| Vehículos | 73 % tiene un solo coche en su histórico. 908 cuentas (0,5 %) con ≥20 vehículos acumulan el 16 % de las filas | La palanca principal es el ciclo de recompra. Las flotas van por otro canal |
| Gama | Dominan los SUV (GLC, GLA/GLB, GLE/GLS) y C/A-Class. Hay un bloque relevante de comerciales (Vito/V-Class, Sprinter, Citan) | Particular SUV frente a profesional de furgoneta: mensajes distintos |
| Electrificación | 21 % tiene algún eléctrico o PHEV. Crece con la edad (11,5 % en <25, 25 % en 55-64). AT 29 % frente a CH 17 % | El early adopter de EQ es maduro y de alto valor. Suiza tiene recorrido para campañas de transición |
| Financiación | 26 % con leasing activo (pico en 35-44 años); 3,3 % con leasing ya terminado | Los leasing terminados son una ventana de renovación. Los mayores de 65 compran casi siempre al contado |
| Actividad | 10,4 % sin ningún vehículo activo | Riesgo de fuga, objetivo de reconquista |
| Taller | 29 % sin visitas en garantía | Objetivo para planes de mantenimiento y recordatorios de servicio |
| Conectividad | 52 % con telemática | Mantenimiento predictivo según uso real, solo en esa mitad |
| Consentimientos | Email 98 %, teléfono 86 %, correo postal 85 % | El email es el canal universal; el canal no discrimina entre segmentos |

### ¿Qué problemas de calidad hemos encontrado y cómo los resolvemos?

| Problema | Resolución |
|---|---|
| Granularidad mixta: los datos de cliente son constantes por cliente, los de vehículo por vehículo, y rol, taller y telemática varían por relación | Una fila por cliente (D1, `src/clean.py`) |
| 908 cuentas de gran volumen (≥20 vehículos), mayoritariamente B2C | `log1p` + winsorización (D5); vigilar si forman un cluster propio |
| Telemática ausente en el ~48 % de los clientes. Es un nulo estructural (vehículo no conectado, roles DRIVER/LEGACY/TEMP_USER) | Flag `has_telemetry` + ablación D3. La evidencia favorece no usarla en el modelo base |
| `engine_concept` nulo en el 44 % y `fuel_type` en el 59 % (cuando falta el motor falta siempre el combustible) | Hoy: EQ → `ELECTRIC`, resto `UNKNOWN`. **Propuesta:** imputar desde `vehicle_type` (pureza del 99 %, recupera el 54 % de los nulos). Excluir `fuel_type` |
| **Antigüedad = 36 meses en el 12 % de los clientes**, unas 9 veces más que los meses vecinos y con coches más viejos | Es un valor por defecto de carga, no fidelidad real. **Propuesta:** flag `tenure_is_default`. El 120 es un tope con muy pocos casos |
| Socioeconómicos nulos (6,3 %), `population == 0` (73 filas), CP con longitud ≠ 4 (5 filas) | Mediana por país + flag |
| Género inferido nulo (11 % de las filas) | Categoría `unknown`, fuera del modelo |
| Redundancias: `role_type` ≡ `role == DRIVER`; `currently_connected_vehicles` = nº de vehículos actuales (salvo 4 clientes); poder adquisitivo y población ×3 (Spearman ≥ 0,96) | Una sola variable por concepto |
| Columnas `*_mode` con listas y valores en bins; `*_all_counter` con extremos de 1,45·10⁹ | Excluir |
| Extremos físicamente dudosos (velocidad media > 150 km/h, consumo ≥ 40 l/100 km) | Winsorizar p1-p99 (D6) |

Las propuestas en negrita afectan a `src/clean.py` y se aplican con el visto bueno de su dueño.
