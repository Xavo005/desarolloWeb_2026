"""
chatbotAD.py — Capa de Lógica del Chatbot Híbrido
===================================================
Patrón: Intent Router con Árbol de Decisiones por Regex + Fallback Gemini AI
Sistema: El Hueco SGI v2.0
Arquitectura: 3 capas (este módulo vive en la capa de Lógica de Negocio)

Responsabilidades:
  1. Clasificar el texto del usuario en una "intención" conocida (Intent Router).
  2. Ejecutar la función de datos correspondiente (*AD.py) si hay match.
  3. Delegar a Gemini 1.5 Flash si no hay coincidencia (Fallback IA).
  4. Formatear la respuesta como texto plano legible para el widget de chat.
"""

import re
import os
import json

# ── Importaciones de la capa de datos (módulos *AD.py) ──────────────────────
from alertaAD import obtener_alertas_activas, obtener_totales_alertas
from dashboardAD import obtener_stats_dashboard, obtener_alertas_recientes
from productosAD import leer_productos


# ==============================================================================
# SECCIÓN 1: ÁRBOL DE INTENCIONES — Catálogo de Patrones Regex
# ==============================================================================
# Cada entrada del catálogo es una tupla:
#   (nombre_intencion, patron_regex, funcion_manejadora)
#
# Orden: De más específico a más general. El primer match gana.
# Flags:  re.IGNORECASE para ignorar mayúsculas/minúsculas.
# ==============================================================================

def _manejar_alertas_criticas():
    """Retorna un resumen de alertas en nivel CRITICO."""
    alertas = obtener_alertas_activas()
    criticas = [a for a in alertas if a.get('nivel') == 'critico']
    if not criticas:
        return "✅ No hay alertas críticas en este momento. Todos los stocks están dentro del rango seguro."
    
    lineas = [f"🚨 *{len(criticas)} alerta(s) CRÍTICA(S) detectada(s):*\n"]
    for a in criticas[:5]:  # Máximo 5 para no saturar el chat
        lineas.append(
            f"• **{a.get('producto', 'N/A')}** (SKU: {a.get('sku', '-')})\n"
            f"  Stock actual: {a.get('unidades', 0)} unid. | Mínimo: {a.get('stock_minimo', 0)} unid."
        )
    if len(criticas) > 5:
        lineas.append(f"\n_...y {len(criticas) - 5} más. Ve al módulo de Alertas para el listado completo._")
    return "\n".join(lineas)


def _manejar_alertas_urgentes():
    """Retorna un resumen de alertas en nivel URGENTE."""
    alertas = obtener_alertas_activas()
    urgentes = [a for a in alertas if a.get('nivel') == 'urgente']
    if not urgentes:
        return "✅ No hay alertas urgentes en este momento."
    
    lineas = [f"⚠️ *{len(urgentes)} alerta(s) URGENTE(S) detectada(s):*\n"]
    for a in urgentes[:5]:
        lineas.append(
            f"• **{a.get('producto', 'N/A')}** (SKU: {a.get('sku', '-')})\n"
            f"  Stock actual: {a.get('unidades', 0)} unid."
        )
    if len(urgentes) > 5:
        lineas.append(f"\n_...y {len(urgentes) - 5} más._")
    return "\n".join(lineas)


def _manejar_resumen_alertas():
    """Retorna el conteo total de alertas por nivel."""
    totales = obtener_totales_alertas()
    critico  = totales.get('critico', 0)
    urgente  = totales.get('urgente', 0)
    ok       = totales.get('ok', 0)
    total    = critico + urgente + ok

    return (
        f"📊 *Resumen de Alertas de Stock:*\n\n"
        f"🔴 Críticas:   {critico}\n"
        f"🟡 Urgentes:   {urgente}\n"
        f"🟢 OK / Normal: {ok}\n"
        f"────────────────\n"
        f"Total monitoreadas: {total}"
    )


def _manejar_stats_dashboard():
    """Retorna estadísticas generales del dashboard."""
    stats = obtener_stats_dashboard()
    return (
        f"📈 *Estado General del Sistema:*\n\n"
        f"📦 Total de productos activos: {stats.get('total_productos', 0)}\n"
        f"🚨 Alertas críticas activas:   {stats.get('alertas_criticas', 0)}\n\n"
        f"_Consulta el Dashboard para ver gráficos y tendencias completas._"
    )


def _manejar_productos_bajo_stock():
    """Lista los 5 productos con menor stock."""
    try:
        productos = leer_productos() or []
        # Ordenar por stock_total ascendente
        ordenados = sorted(productos, key=lambda p: p.get('stock_total', 0))
        bajos = ordenados[:5]
        if not bajos:
            return "📦 No se encontraron productos en el catálogo."
        
        lineas = ["📉 *Productos con menor stock:*\n"]
        for p in bajos:
            lineas.append(
                f"• **{p.get('nombre', 'N/A')}** — {p.get('stock_total', 0)} unid. "
                f"(Cat: {p.get('categoria', 'Sin cat.')})"
            )
        return "\n".join(lineas)
    except Exception as e:
        return f"❌ Error al consultar productos: {str(e)}"


def _manejar_ayuda():
    """Retorna el menú de ayuda con todas las intenciones disponibles."""
    return (
        "🤖 *Soy el Asistente IA del SGI El Hueco.* ¡Puedo ayudarte con:\n\n"
        "📋 **Comandos rápidos:**\n"
        "• _alertas críticas_ → Ver productos en quiebre crítico\n"
        "• _alertas urgentes_ → Ver productos con stock bajo\n"
        "• _resumen de alertas_ → Conteo total por nivel\n"
        "• _estado del sistema_ → Stats generales\n"
        "• _productos bajos_ → Los 5 con menos stock\n\n"
        "💬 **O escríbeme cualquier pregunta** sobre el inventario y usaré IA para responderte."
    )


def _manejar_saludo():
    """Responde a saludos del usuario."""
    from datetime import datetime
    hora = datetime.now().hour
    if hora < 12:
        momento = "Buenos días"
    elif hora < 19:
        momento = "Buenas tardes"
    else:
        momento = "Buenas noches"
    return (
        f"👋 ¡{momento}! Soy el Asistente IA del SGI El Hueco.\n\n"
        "Puedo darte información en tiempo real sobre alertas de stock, "
        "estadísticas del inventario y más.\n\n"
        "Escribe **ayuda** para ver todo lo que puedo hacer, "
        "o hazme una pregunta directamente."
    )


# ==============================================================================
# SECCIÓN 2: REGISTRO DE INTENCIONES (Intent Registry)
# ==============================================================================
# Lista ordenada de tuplas: (patrón_regex, función_manejadora)
# El orden importa: patrones más específicos primero.
# ==============================================================================

INTENT_REGISTRY = [
    # Saludos
    (r'\b(hola|buenos?\s*(días?|tardes?|noches?)|saludos?|hi|hey)\b',
     _manejar_saludo),

    # Alertas críticas (variantes: "criticas", "critico", "quiebre", "rotura")
    (r'\b(alert[ao]s?\s+cr[ií]tic[ao]s?|cr[ií]tic[ao]s?|quiebre|rotura\s*de\s*stock)\b',
     _manejar_alertas_criticas),

    # Alertas urgentes
    (r'\b(alert[ao]s?\s+urgentes?|urgentes?|stock\s+bajo|bajo\s+stock)\b',
     _manejar_alertas_urgentes),

    # Resumen / total de alertas
    (r'\b(resumen|total|cuantas?|cu[aá]ntas?)\s*(de\s*)?(alert[ao]s?|notificaciones?)\b',
     _manejar_resumen_alertas),

    # Estado del sistema / dashboard
    (r'\b(estado|dashboard|stats?|estad[ií]sticas?|indicadores?|sistema)\b',
     _manejar_stats_dashboard),

    # Productos con poco stock
    (r'\b(productos?\s*(con\s*)?(poco|bajo|menos|m[ií]nimo)\s*stock|stock\s+m[ií]nimo|productos?\s+bajos?)\b',
     _manejar_productos_bajo_stock),

    # Ayuda
    (r'\b(ayuda|help|comandos?|que\s+puedes?|qu[eé]\s+haces?|funciones?)\b',
     _manejar_ayuda),
]


# ==============================================================================
# SECCIÓN 3: FUNCIÓN PRINCIPAL — Intent Router
# ==============================================================================

def enrutar_intencion(texto_usuario: str) -> dict:
    """
    Función central del chatbot. Evalúa el texto del usuario contra el
    INTENT_REGISTRY y devuelve una respuesta estructurada.

    Flujo de decisión:
      1. Normalizar el texto (strip + lower).
      2. Iterar INTENT_REGISTRY en orden.
      3. Si hay match → ejecutar la función manejadora → retornar respuesta.
      4. Si no hay match → llamar a _fallback_gemini() → retornar respuesta.

    Args:
        texto_usuario (str): Mensaje enviado por el usuario en el chat.

    Returns:
        dict: {
            'respuesta': str,       # Texto de respuesta para mostrar en el chat
            'intencion': str,       # Nombre de la intención detectada o 'fallback_ia'
            'exito': bool           # True si la operación fue exitosa
        }
    """
    # Paso 1: Normalizar — evitar falsos negativos por mayúsculas o espacios extra
    texto_normalizado = texto_usuario.strip().lower()

    if not texto_normalizado:
        return {
            'respuesta': "Por favor, escribe un mensaje para que pueda ayudarte. 😊",
            'intencion': 'vacio',
            'exito': True
        }

    # Paso 2 + 3: Evaluar cada patrón en orden de prioridad
    for patron, funcion_manejadora in INTENT_REGISTRY:
        # re.search() busca el patrón en cualquier parte del texto (no solo al inicio)
        if re.search(patron, texto_normalizado, re.IGNORECASE):
            try:
                respuesta_texto = funcion_manejadora()
                # Extraer nombre de la intención del nombre de la función
                nombre_intencion = funcion_manejadora.__name__.replace('_manejar_', '')
                return {
                    'respuesta': respuesta_texto,
                    'intencion': nombre_intencion,
                    'exito': True
                }
            except Exception as e:
                return {
                    'respuesta': f"❌ Error al procesar la solicitud: {str(e)}",
                    'intencion': 'error',
                    'exito': False
                }

    # Paso 4: Sin match → Fallback a Gemini AI
    return _fallback_gemini(texto_usuario)


# ==============================================================================
# SECCIÓN 4: FALLBACK — Integración con Gemini AI
# ==============================================================================

def _fallback_gemini(texto_usuario: str) -> dict:
    """
    Fallback: Llama a la API de Google Gemini cuando ninguna intención
    del Intent Router hizo match. Envía el mensaje del usuario junto con
    un system prompt contextualizado al negocio de farmacias/inventario.

    Requiere: variable de entorno GEMINI_API_KEY en el archivo .env

    Args:
        texto_usuario (str): Mensaje original del usuario.

    Returns:
        dict con 'respuesta', 'intencion'='fallback_ia', 'exito'
    """
    # Importar aquí para no forzar la dependencia si Gemini no está instalado
    try:
        import google.generativeai as genai
    except ImportError:
        return {
            'respuesta': (
                "🤖 Mi módulo de IA avanzada no está disponible en este momento.\n"
                "Escribe **ayuda** para ver qué comandos directos puedo ejecutar."
            ),
            'intencion': 'fallback_sin_libreria',
            'exito': False
        }

    # Leer la API key desde variables de entorno (cargadas por python-dotenv en app.py)
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        return {
            'respuesta': (
                "🔑 No tengo configurada una clave API para el asistente de IA avanzada.\n\n"
                "Un administrador debe agregar `GEMINI_API_KEY=tu_clave` al archivo `.env`.\n\n"
                "Mientras tanto, escribe **ayuda** para ver los comandos disponibles."
            ),
            'intencion': 'fallback_sin_key',
            'exito': False
        }

    try:
        # Configurar el cliente con la API key
        genai.configure(api_key=api_key)

        # Obtener contexto real del sistema para enriquecer la respuesta de IA
        totales = obtener_totales_alertas()
        stats = obtener_stats_dashboard()

        # System prompt contextualizado al negocio de El Hueco SGI
        # Contiene datos reales en tiempo real para que Gemini pueda razonar sobre ellos
        system_prompt = f"""Eres el Asistente IA del Sistema de Gestión de Inventario (SGI) 
de "El Hueco Restobar". Eres un experto en control de inventario farmacéutico y retail.
Respondes en español, de forma concisa, profesional y útil.
NUNCA inventes datos. Si no sabes algo específico del sistema, dilo claramente.

CONTEXTO ACTUAL DEL SISTEMA (datos en tiempo real):
- Total de productos activos: {stats.get('total_productos', 'N/D')}
- Alertas críticas activas: {totales.get('critico', 0)}
- Alertas urgentes activas: {totales.get('urgente', 0)}
- Productos en estado OK: {totales.get('ok', 0)}

FUNCIONALIDADES DEL SGI:
- Gestión de productos (CRUD con SKU/EAN-13)
- Alertas de quiebre de stock (niveles: crítico, urgente, ok)
- Segmentación de inventario (cliente final vs revendedor)
- Historial de ajustes de stock
- Conteos manuales de inventario
- Gestión de personal y sedes

Responde la siguiente pregunta del usuario de forma útil y breve (máximo 150 palabras):"""

        # Inicializar el modelo Gemini 1.5 Flash (rápido y económico)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Combinar system prompt + mensaje del usuario en una sola llamada
        prompt_completo = f"{system_prompt}\n\nUsuario: {texto_usuario}"

        # Llamada a la API con configuración de seguridad
        response = model.generate_content(
            prompt_completo,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=300,   # Limitar para mantener respuestas concisas
                temperature=0.4,         # Baja temperatura = respuestas más deterministas
            )
        )

        respuesta_ia = response.text.strip()
        return {
            'respuesta': f"🤖 *Asistente IA:*\n\n{respuesta_ia}",
            'intencion': 'fallback_ia',
            'exito': True
        }

    except Exception as e:
        # Capturar errores de API (rate limit, red, etc.) sin romper el chat
        return {
            'respuesta': (
                f"⚠️ El servicio de IA no está disponible ahora mismo.\n\n"
                f"Escribe **ayuda** para ver los comandos directos disponibles."
            ),
            'intencion': 'fallback_error',
            'exito': False
        }
