from alertaAD import obtener_alertas_activas, obtener_totales_alertas
from productosAD import leer_productos

#menu
MENU_PRINCIPAL = (
    "Hola, soy el Asistente del SGI DeyFarma.\n"
    "Elige una opcion:\n\n"
    "1. Stock bajo / critico\n"
    "2. Alertas urgentes\n"
    "3. Preguntas frecuentes (FAQ)\n\n"
    "Escribe el numero de tu opcion."
)

#preguntas
FAQ = {
    "3.1": "Para registrar un nuevo producto, ve al modulo Inventario > Catalogo y presiona 'Nuevo Producto'.",
    "3.2": "Las alertas se generan automaticamente cuando el stock baja del minimo configurado en cada producto.",
    "3.3": "Para cambiar tu contrasena, ingresa a Perfil > Cambiar Clave y sigue los pasos.",
    "3.4": "El conteo manual se registra en el modulo Escanear. Escanea el SKU y actualiza el stock contado.",
    "3.5": "La segmentacion divide el stock entre clientes finales y revendedores. Accede desde Inventario > Segmentacion.",
    "3.6": "El historial de ajustes se encuentra en el modulo Inventario > Historial, donde se registran todas las modificaciones de stock.",

}

MENU_FAQ = (
    "Preguntas Frecuentes:\n\n"
    "3.1 Como registro un nuevo producto?\n"
    "3.2 Como se generan las alertas de stock?\n"
    "3.3 Como cambio mi contrasena?\n"
    "3.4 Como registro un conteo manual?\n"
    "3.5 Que es la segmentacion de inventario?\n\n"
    "3.6 Como ver el historial de ajustes?\n\n"
    "Escribe el numero (ej: 3.1) o '0' para volver al menu."
)

#funcion
def _respuesta_stock_bajo():
    try:
        productos = leer_productos() or []
        bajos = sorted(productos, key=lambda p: p.get('stock_total', 0))[:8]
        if not bajos:
            return "No se encontraron productos en el catalogo."
        lineas = ["Productos con menor stock:\n"]
        for p in bajos:
            lineas.append(
                f"- {p.get('nombre','N/A')} | Stock: {p.get('stock_total',0)} unid."
            )
        lineas.append("\nEscribe '0' para volver al menu principal.")
        return "\n".join(lineas)
    except Exception:
        return "Error al consultar la base de datos. Intenta nuevamente."

#funcion
def _respuesta_alertas_urgentes():
    try:
        alertas = obtener_alertas_activas() or []
        urgentes = [a for a in alertas if a.get('nivel') in ('critico', 'urgente')]
        if not urgentes:
            return "No hay alertas criticas o urgentes en este momento.\n\nEscribe '0' para volver."
        lineas = [f"Alertas activas ({len(urgentes)} encontradas):\n"]
        for a in urgentes[:10]:
            lineas.append(
                f"- {a.get('producto','N/A')} (SKU: {a.get('sku','-')}) | "
                f"Stock: {a.get('unidades',0)} | Nivel: {a.get('nivel','?').upper()}"
            )
        if len(urgentes) > 10:
            lineas.append(f"...y {len(urgentes)-10} mas. Ve al modulo Alertas.")
        lineas.append("\nEscribe '0' para volver al menu principal.")
        return "\n".join(lineas)
    except Exception:
        return "Error al consultar alertas. Intenta nuevamente."

#funcion
def procesar_mensaje(texto, historial):
    entrada = texto.strip().lower()

    if entrada == '0' or entrada in ('menu', 'inicio', 'volver'):
        return MENU_PRINCIPAL

    if entrada == '1':
        return _respuesta_stock_bajo()

    if entrada == '2':
        return _respuesta_alertas_urgentes()

    if entrada == '3':
        return MENU_FAQ

    #respuestas
    if entrada in FAQ:
        respuesta = FAQ[entrada]
        return f"{respuesta}\n\nEscribe otro numero de FAQ o '0' para volver al menu."

    return (
        f"Opcion no valida: '{texto}'.\n"
        "Por favor elige un numero del menu (1, 2, 3) o '0' para ver el menu principal."
    )
