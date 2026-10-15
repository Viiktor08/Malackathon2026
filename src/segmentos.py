"""Lo que escribimos nosotros de cada segmento: nombre, frase, etiquetas y plan de acción.

Las cifras nunca van escritas a mano: van como huecos {clave} (las claves de profiling.KPIS,
más {n} y {pct}) y se rellenan con el perfil. Si el dato cambia, el texto cambia solo.
Los ids son los del reto 3 (0 = el segmento más grande).
"""
import re

from src.profiling import fmt_kpi, fmt_num

PLAN_KEYS = ["objetivo", "oferta", "mantenimiento", "fidelizacion", "comunicacion", "medir"]

SEGMENTOS = {
    0: {
        "slug": "fieles-taller",
        "nombre": "Fieles de taller",
        "frase": "Clientes de hace tiempo ({antiguedad_meses} de media) que pasan por el taller más que nadie: "
                 "{visitas_taller} visitas por coche. Casi no tienen coches electrificados.",
        "accion": "Fidelizar",
        "etiquetas": ["{visitas_taller} visitas al taller por coche", "{antiguedad_meses} con nosotros",
                      "solo {pct_electrificado} electrificados"],
        "plan": {
            "objetivo": "Mantener y premiar su relación con el servicio oficial, que es lo que los define.",
            "oferta": "Renovación con prioridad y valoración de su coche actual cuando se acerque el cambio; "
                      "primera prueba de un híbrido, porque casi no tienen.",
            "mantenimiento": "Contrato de mantenimiento con precio cerrado: ya vienen mucho al taller y así les "
                             "damos tranquilidad y nos aseguramos de que sigan viniendo.",
            "fidelizacion": "Ventajas por antigüedad: revisiones prioritarias, coche de sustitución, regalos de "
                            "aniversario como clientes.",
            "comunicacion": "Email y teléfono con un tono de agradecimiento por su confianza; recordatorios de "
                            "servicio personalizados.",
            "medir": "Contratos de mantenimiento firmados y cuántos siguen viniendo al taller oficial.",
        },
    },
    1: {
        "slug": "recien-llegados",
        "nombre": "Recién llegados",
        "frase": "Llevan poco con nosotros ({antiguedad_meses}) y tienen un coche casi nuevo ({edad_coche}). "
                 "Todavía apenas han pisado el taller.",
        "accion": "Vincular",
        "etiquetas": ["{antiguedad_meses} como clientes", "coche de {edad_coche}", "{visitas_taller} visitas al taller por coche"],
        "plan": {
            "objetivo": "Convertir la primera compra en una relación: que vuelvan al taller oficial y que su "
                        "próximo coche también sea un Mercedes.",
            "oferta": "Todavía no es momento de cambiar de coche: accesorios, extensiones de garantía y servicios "
                      "conectados.",
            "mantenimiento": "Primera revisión con cita propuesta por nosotros, para que la hagan en el taller oficial.",
            "fidelizacion": "Programa de bienvenida durante el primer año: activar la app y los servicios "
                            "conectados, y una experiencia de entrega cuidada.",
            "comunicacion": "Email con una secuencia de bienvenida; mensajes cortos y prácticos sobre su coche.",
            "medir": "Cuántos hacen la primera revisión en el taller oficial y cuántos activan la app.",
        },
    },
    2: {
        "slug": "coche-veterano",
        "nombre": "Coche veterano",
        "frase": "Tienen el coche más antiguo de la cartera ({edad_coche}), sobre todo de combustión y comprado "
                 "sin leasing. Ojo: en muchos la antigüedad como cliente es un valor por defecto, así que "
                 "pueden llevar con nosotros más tiempo del que dice el dato.",
        "accion": "Renovar",
        "etiquetas": ["coche de {edad_coche}", "solo {pct_leasing_activo} con leasing", "{visitas_taller} visitas al taller por coche"],
        "plan": {
            "objetivo": "Que cuando cambien de coche, el siguiente sea un Mercedes.",
            "oferta": "Renovación con buena valoración de su coche actual; financiación o leasing, que casi no "
                      "han probado; seminuevos certificados para los más jóvenes del grupo.",
            "mantenimiento": "Revisión específica para coches con años: mantenerlos en el taller oficial hasta "
                             "que llegue el cambio.",
            "fidelizacion": "Invitación a probar los modelos actuales (incluidos híbridos) para que vean el salto.",
            "comunicacion": "Email y correo postal con ofertas de renovación concretas.",
            "medir": "Pruebas de conducción solicitadas y renovaciones cerradas.",
        },
    },
    3: {
        "slug": "electrificados",
        "nombre": "Electrificados",
        "frase": "Ya se han pasado a la electrificación: prácticamente todos ({pct_electrificado}) tienen un eléctrico o un enchufable, "
                 "con un coche reciente ({edad_coche}). Son algo mayores que la media.",
        "accion": "Acompañar",
        "etiquetas": ["{pct_electrificado} con eléctrico o enchufable", "coche de {edad_coche}",
                      "{pct_leasing_activo} con leasing activo"],
        "plan": {
            "objetivo": "Que su siguiente coche siga siendo eléctrico y Mercedes, y cuidar su experiencia de carga.",
            "oferta": "Siguiente eléctrico de la gama EQ; paso de enchufable a eléctrico puro al terminar su leasing.",
            "mantenimiento": "Revisión específica de batería y sistema de carga; instalación y revisión del wallbox.",
            "fidelizacion": "Ventajas en carga pública y servicios conectados pensados para eléctricos.",
            "comunicacion": "Email con contenido práctico sobre carga, autonomía y novedades eléctricas.",
            "medir": "Cuántos repiten con un eléctrico y cuánto usan los servicios de carga.",
        },
    },
    4: {
        "slug": "desconectados",
        "nombre": "Desconectados",
        "frase": "Han tenido coche con nosotros, pero hoy no tienen ninguno activo. Eso no prueba que se hayan "
                 "ido (pueden haberlo vendido o desvinculado), pero es la señal de alarma más clara. El "
                 "{pct_leasing_terminado} tiene un leasing ya terminado.",
        "accion": "Recuperar",
        "etiquetas": ["{pct_sin_activo} sin coche activo", "{antiguedad_meses} como clientes",
                      "{pct_leasing_terminado} con leasing terminado"],
        "plan": {
            "objetivo": "Averiguar quién se ha ido de verdad y recuperar a los que todavía se puede.",
            "oferta": "Oferta de vuelta para quienes terminaron su leasing: un coche nuevo con condiciones de "
                      "reenganche.",
            "mantenimiento": "Si aún tienen el coche, invitación a una revisión en el taller oficial.",
            "fidelizacion": "Encuesta corta de por qué ya no tienen coche activo, para aprender y personalizar.",
            "comunicacion": "Teléfono para los que terminaron leasing y email para el resto; tono cercano, sin presión.",
            "medir": "Cuántos vuelven a tener un vehículo activo.",
        },
    },
    5: {
        "slug": "multivehiculo",
        "nombre": "Multivehículo",
        "frase": "Tienen muchos coches ({n_vehiculos} de media) y son los clientes más antiguos ({antiguedad_meses}). "
                 "Aquí están casi todas las flotas y cuentas grandes, y son los que más usan el leasing.",
        "accion": "Ampliar",
        "etiquetas": ["{n_vehiculos} vehículos de media", "{antiguedad_meses} con nosotros",
                      "{pct_leasing_activo} con leasing activo"],
        "plan": {
            "objetivo": "Tratarlos como cuentas clave y crecer dentro de cada una.",
            "oferta": "Renovación de flota con condiciones por volumen, incluidas furgonetas y eléctricos para empresa.",
            "mantenimiento": "Contrato de mantenimiento de flota con un único punto de contacto.",
            "fidelizacion": "Un gestor de cuenta y condiciones que mejoran con el tiempo.",
            "comunicacion": "Teléfono, con su gestor de cuenta; nada de campañas masivas.",
            "medir": "Vehículos renovados por cuenta y cuentas que siguen con nosotros.",
        },
    },
    6: {
        "slug": "zonas-premium",
        "nombre": "Zonas premium",
        "frase": "Viven en las zonas más ricas de su país ({riqueza_relativa} el poder adquisitivo típico), casi "
                 "todos en Suiza, y van mucho al taller. Más gama alta que la media.",
        "accion": "Elevar",
        "etiquetas": ["{riqueza_relativa} la riqueza de su país", "{visitas_taller} visitas al taller por coche",
                      "{pct_leasing_activo} con leasing activo"],
        "plan": {
            "objetivo": "Subirles de gama y darles un trato a la altura.",
            "oferta": "Modelos de gama alta (Clase S, EQS, AMG, Clase G) y configuraciones a medida.",
            "mantenimiento": "Servicio premium: recogida y entrega del coche en casa.",
            "fidelizacion": "Eventos y experiencias exclusivas, acceso anticipado a lanzamientos.",
            "comunicacion": "Teléfono con un asesor personal y correo postal cuidado.",
            "medir": "Cuántos suben de gama y el valor medio de su compra.",
        },
    },
}


def placeholders(stats):
    """Valores con los que se rellenan los huecos de los textos de un segmento."""
    vals = {k: fmt_kpi(k, v) for k, v in stats["kpis"].items()}
    vals["n"] = fmt_num(stats["n"], 0)
    vals["pct"] = f"{fmt_num(stats['pct'], 1)} %"
    return vals


def fill_texts(seg, stats):
    """Copia del segmento con todos los huecos rellenados. Falla si algún hueco no existe."""
    vals = placeholders(stats)

    def fill(texto):
        try:
            return texto.format(**vals)
        except KeyError as err:
            raise KeyError(f"segmento {stats['id']}: hueco desconocido {{{err.args[0]}}}") from None

    return {
        **seg,
        "nombre": fill(seg["nombre"]),
        "frase": fill(seg["frase"]),
        "accion": fill(seg["accion"]),
        "etiquetas": [fill(e) for e in seg["etiquetas"]],
        "plan": {k: fill(v) for k, v in seg["plan"].items()},
    }


def check_segmentos(segmentos, k):
    """Cada segmento tiene todo lo necesario y los slugs sirven para enlaces."""
    assert set(segmentos) == set(range(k)), f"ids {sorted(segmentos)} en vez de 0..{k - 1}"
    slugs = [s["slug"] for s in segmentos.values()]
    assert len(set(slugs)) == len(slugs), "slugs repetidos"
    for seg_id, seg in segmentos.items():
        assert re.fullmatch(r"[a-z0-9-]+", seg["slug"]), f"segmento {seg_id}: slug no válido"
        for campo in ["nombre", "frase", "accion"]:
            assert seg.get(campo, "").strip(), f"segmento {seg_id}: falta {campo}"
        assert len(seg["etiquetas"]) == 3 and all(e.strip() for e in seg["etiquetas"]), \
            f"segmento {seg_id}: hacen falta 3 etiquetas"
        assert list(seg["plan"]) == PLAN_KEYS and all(v.strip() for v in seg["plan"].values()), \
            f"segmento {seg_id}: plan incompleto"
