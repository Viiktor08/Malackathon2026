# Resumen · Malackathon 2026 · Mercedes-Benz "Clustering the Star"

## Reto 1 · Exploración y calidad de datos

Notebook: [`notebooks/01_eda_calidad.ipynb`](../notebooks/01_eda_calidad.ipynb). Las cifras son por cliente (173.456 clientes) y salen de la misma tabla de clientes que usamos en el reto 2.

### ¿Cómo son los clientes?

| Tema | Lo que vemos | Qué significa para marketing |
|---|---|---|
| Mercado | 66 % Suiza y 34 % Austria. Poder adquisitivo mediano por habitante: 51.000 € en Suiza y 30.000 € en Austria | Dos mercados con niveles muy distintos; ofertas y precios hay que pensarlos por país |
| Edad | El 61 % tiene 45 años o más y el 20 % más de 65. Menores de 25, solo un 5 % | Lo prioritario es fidelizar al cliente sénior; el joven es un nicho para captar |
| Género (inferido) | 65 % hombres, 18 % mujeres y un 17 % que no sabemos | Solo para describir, no para dirigir campañas |
| Vehículos | El 73 % solo ha tenido un coche. 908 cuentas (0,5 %) tienen 20 o más y acumulan el 16 % de las filas | La palanca principal es la recompra; las flotas van por otro canal |
| Gama | Mandan los SUV (GLC, GLA/GLB, GLE/GLS) y los C y A. Hay un bloque importante de furgonetas (Vito/V-Class, Sprinter, Citan) | Particular con SUV y profesional con furgoneta piden mensajes distintos |
| Electrificación | El 23 % tiene algún eléctrico o enchufable. Crece con la edad (del 12 % en menores de 25 al 28 % en 55-64). Austria 31 %, Suiza 20 % | El que se pasa al eléctrico es maduro y con dinero, no joven. En Suiza hay recorrido |
| Financiación | El 26 % tiene un leasing activo (un 33 % entre 35 y 44 años) y un 3 % lo ha terminado. El 84 % de los mayores de 65 nunca ha usado leasing | Los leasing terminados son una ventana clara para renovar |
| Actividad | El 10 % no tiene ningún coche activo | Riesgo de fuga, o clientes a recuperar |
| Taller | El 29 % no ha ido al taller en garantía | Público para planes de mantenimiento |
| Conectividad | El 60 % tiene telemetría | Mantenimiento según uso real, solo en esa parte |
| Consentimientos | Email 98 %, teléfono 86 %, correo 85 %. Nadie los tiene todos cerrados | El email llega a casi todos; el canal no distingue a unos clientes de otros |

### ¿Qué problemas de calidad hemos encontrado y qué hacemos?

| Problema | Qué hacemos |
|---|---|
| Mezcla de niveles: cliente, vehículo y relación cliente-coche | Una fila por cliente (`src/clean.py`) |
| 908 cuentas con 20 o más vehículos (el 92 % de sus filas figuran como B2C) | En el modelo con el nº de vehículos recortado; flag `is_heavy_account` para describirlas |
| Telemetría que falta en el 40 % de los clientes (no tienen coche conectado) | Flag `has_telemetry`; fuera del modelo base y lo comprobamos en el reto 3 |
| Motor vacío en el 44 % de las filas y combustible en el 59 % | Rellenamos el motor por versión comercial (solo versiones con ≥ 90 % de pureza) y por familia EQ; el resto `UNKNOWN`. Fuera `fuel_type` |
| Antigüedad = 36 meses en el 12 % de los clientes, 9 veces más que los meses vecinos | Es un valor por defecto: flag `tenure_is_default` |
| Poder adquisitivo y población vacíos (6 % de filas), población 0, códigos postales raros | Mediana de su país; la población 0 cuenta como vacía. Sin flag de "imputado" |
| Género inferido vacío (11 % de filas) | Desconocido y fuera del modelo |
| Columnas que repiten lo mismo: `role_type` = `role == DRIVER`, vehículos conectados = nº de vehículos actuales, poder adquisitivo y población ×3 | Una sola por concepto |
| `*_mode` con listas y valores en tramos; contadores con extremos de 1,45·10⁹ | Fuera |
| Extremos poco creíbles (velocidad media > 150 km/h, consumo ≥ 40 l/100 km) | Recorte p1-p99 y log en colas largas |

## Reto 4 · Interpretación de los segmentos

Notebook: [`notebooks/04_interpretacion.ipynb`](../notebooks/04_interpretacion.ipynb). Dashboard: [`outputs/dashboard_segmentos.html`](../outputs/dashboard_segmentos.html) (se abre con doble clic, sin conexión). Las cifras del notebook y del dashboard salen del mismo código (`src/profiling.py`).

Cada segmento se describe comparándolo con el total de clientes. Los segmentos los define la **relación con la marca y el ciclo de vida del coche**, no el modelo de coche.

| Segmento | Clientes | Lo que le define (frente a la media) | Acción |
|---|---|---|---|
| Coche en garantía | 24,1 % (41.811) | 4,4 visitas en garantía por coche (media 2,1), coche de 5,2 años y 48 meses de antigüedad (media 34) | Retener |
| Recién llegados | 18,3 % (31.769) | 18 meses como clientes y coche de 2,5 años (media 4,6) | Vincular |
| Coche veterano | 18,2 % (31.611) | Coche de 8,4 años; solo un 4,7 % con leasing (media 26,2 %); más de la mitad sin ninguna visita en garantía | Renovar |
| Electrificados | 15,9 % (27.575) | Todos con eléctrico o enchufable (media 23,4 %), coche de 2,9 años | Acompañar |
| Desconectados | 9,0 % (15.660) | Ningún coche activo; 11,7 % con leasing terminado (media 3,3 %) | Recuperar |
| Multivehículo | 8,8 % (15.327) | 7,2 vehículos de media y 54 meses de antigüedad; aquí están 904 de las 908 cuentas grandes | Ampliar |
| Zonas premium | 5,6 % (9.703) | Zona con 1,79× el poder adquisitivo típico de su país, casi todos en Suiza | Elevar |

Cada segmento tiene en el notebook y en el dashboard su plan en las cuatro palancas del reto (oferta de vehículo, mantenimiento, fidelización y comunicación) y qué mediríamos.

Avisos para usar los segmentos:

- "Sin coche activo" es una señal de posible fuga, no la prueba de que el cliente se haya ido.
- Las visitas al taller del dataset son solo visitas **en garantía**: suben con la edad del coche hasta los 5-6 años y luego bajan. No miden fidelidad al taller, sino uso de la garantía.
- En un 12 % de los clientes la antigüedad (36 meses) es un valor por defecto; afecta sobre todo a Coche veterano.
- Los consentimientos son casi iguales en todos los segmentos (email 98 %, teléfono 86 %, correo 85 %): el canal se elige por el mensaje, no por el segmento.
