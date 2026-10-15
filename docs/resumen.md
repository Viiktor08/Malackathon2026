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
