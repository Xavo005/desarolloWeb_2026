from datetime import datetime
from bd import obtenerconexion

class clsAlerta:
    def __init__(self, producto_id=None, producto=None, sku=None,
                 categoria=None, unidades=None, venta_dia=None,
                 estado_transf=None, stock_minimo=None):
        self.producto_id = producto_id
        self.producto = producto
        self.sku = sku
        self.categoria = categoria
        self.unidades = unidades
        self.venta_dia = venta_dia
        self.estado_transf = estado_transf
        self.stock_minimo = stock_minimo

def calcular_prediccion_dinamica(conn, producto_id, stock_actual, static_venta_dia):
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT valor_anterior, valor_nuevo, fecha
                FROM historial_ajustes
                WHERE producto_id = %s
                  AND (campo_modificado = 'stock_total' OR accion = 'CONTEO')
                  AND fecha >= NOW() - INTERVAL 14 DAY
                ORDER BY fecha ASC
            """
            cursor.execute(sql, (producto_id,))
            rows = cursor.fetchall()

            reducciones = 0
            oldest_fecha = None

            for row in rows:
                try:
                    val_ant = int(row['valor_anterior']) if row['valor_anterior'] is not None else 0
                    val_nue = int(row['valor_nuevo'])    if row['valor_nuevo']    is not None else 0
                    if val_ant > val_nue:
                        reducciones += (val_ant - val_nue)
                        if oldest_fecha is None:
                            oldest_fecha = row['fecha']
                except (ValueError, TypeError):
                    continue

            if oldest_fecha and reducciones > 0:
                delta = datetime.now() - oldest_fecha
                days = delta.total_seconds() / 86400.0
                days = max(days, 1.0)  # Al menos 1 dia para evitar valores atipicos
                venta_dia_real = reducciones / days
            else:
                venta_dia_real = float(static_venta_dia or 0)

            if venta_dia_real > 0:
                horas_restantes = (stock_actual / venta_dia_real) * 24.0
            else:
                horas_restantes = 9999.0

            if venta_dia_real <= 0:
                nivel = 'ok'
            elif horas_restantes <= 24:
                nivel = 'critico'
            elif horas_restantes <= 72:
                nivel = 'urgente'
            elif horas_restantes <= 120:
                nivel = 'advertencia'
            else:
                nivel = 'ok'

            return {
                'venta_dia_real': round(venta_dia_real, 2),
                'horas_restantes_real': round(horas_restantes, 1),
                'nivel_real': nivel,
                'usando_historial': oldest_fecha is not None and reducciones > 0
            }
    except Exception:
        # Fallback si ocurre algun error
        venta_dia_real = float(static_venta_dia or 0)
        horas = (stock_actual / venta_dia_real * 24) if venta_dia_real > 0 else 9999.0
        nivel = 'ok'
        if venta_dia_real > 0:
            if horas <= 24:   nivel = 'critico'
            elif horas <= 72: nivel = 'urgente'
            elif horas <= 120: nivel = 'advertencia'
        return {
            'venta_dia_real': round(venta_dia_real, 2),
            'horas_restantes_real': round(horas, 1),
            'nivel_real': nivel,
            'usando_historial': False
        }

def calcular_nivel_estatico(stock_actual, stock_minimo):
    if stock_actual <= 0:
        return 'critico'
    elif stock_actual <= stock_minimo:
        return 'urgente'
    else:
        return 'ok'

def obtener_alertas_activas():
    try:
        conn = obtenerconexion()
        alertas = []
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT p.id AS producto_id, p.sku, p.nombre AS producto,
                               p.categoria, p.stock_total AS unidades,
                               p.stock_minimo, p.venta_dia, p.ubicacion_gondola,
                               COALESCE(a.id, 0) AS alerta_id,
                               COALESCE(a.estado_transf, 'Sin transferencia activa') AS estado_transf
                        FROM productos p
                        LEFT JOIN alertas_quiebre a ON a.producto_id = p.id AND a.activo=1
                        WHERE p.activo = 1 AND p.stock_total <= p.stock_minimo
                        ORDER BY p.stock_total ASC
                    """
                    cursor.execute(sql)
                    filas = cursor.fetchall()
                    for fila in filas:
                        item = dict(fila)
                        item['id'] = item['producto_id'] # Alias para compatibilidad con template
                        item['nivel'] = calcular_nivel_estatico(
                            item['unidades'], item['stock_minimo']
                        )
                        alertas.append(item)
        return alertas
    except Exception as e:
        print(f"Error en obtener_alertas_activas: {repr(e)}")
        return []

def obtener_alertas_dinamicas():
    try:
        conn = obtenerconexion()
        if not conn:
            return [], {'critico': 0, 'urgente': 0, 'ok': 0}
            
        with conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT p.id AS producto_id, p.sku, p.nombre AS producto,
                           p.categoria, p.stock_total AS unidades,
                           p.stock_minimo, p.venta_dia,
                           COALESCE(a.estado_transf, 'Sin transferencia activa') AS estado_transf
                    FROM productos p
                    LEFT JOIN alertas_quiebre a ON a.producto_id = p.id AND a.activo=1
                    WHERE p.activo = 1 AND p.stock_total <= p.stock_minimo
                """
                cursor.execute(sql)
                alertas_raw = cursor.fetchall()

                lista_alertas = []
                total_critico = 0
                total_urgente = 0
                total_ok = 0

                for a in alertas_raw:
                    pred = calcular_prediccion_dinamica(
                        conn,
                        a['producto_id'],
                        a['unidades'],
                        a['venta_dia']
                    )

                    item = {
                        'id': a['producto_id'], # Alias para compatibilidad con template
                        'producto_id': a['producto_id'],
                        'producto': a['producto'],
                        'sku': a['sku'],
                        'categoria': a['categoria'],
                        'unidades': a['unidades'],
                        'stock_minimo': a['stock_minimo'],
                        'venta_dia': pred['venta_dia_real'],
                        'horas_restantes': pred['horas_restantes_real'],
                        'nivel': pred['nivel_real'],
                        'estado_transf': a['estado_transf']
                    }

                    if item['nivel'] == 'critico': total_critico += 1
                    elif item['nivel'] == 'urgente': total_urgente += 1
                    else: total_ok += 1

                    lista_alertas.append(item)

                # Ordenar por horas restantes
                lista_alertas.sort(key=lambda x: x['horas_restantes'])

                totales = {
                    'critico': total_critico,
                    'urgente': total_urgente,
                    'ok': total_ok
                }
                return lista_alertas, totales
    except Exception as e:
        print(f"Error en obtener_alertas_dinamicas: {repr(e)}")
        return [], {'critico': 0, 'urgente': 0, 'ok': 0}

def obtener_totales_alertas():
    try:
        conn = obtenerconexion()
        totales = {'critico': 0, 'urgente': 0, 'ok': 0}
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = "SELECT stock_total AS unidades, stock_minimo FROM productos WHERE activo=1"
                    cursor.execute(sql)
                    for fila in cursor.fetchall():
                        nivel = calcular_nivel_estatico(
                            fila['unidades'], fila['stock_minimo']
                        )
                        totales[nivel] = totales.get(nivel, 0) + 1
        return totales
    except Exception as e:
        print(f"Error en obtener_totales_alertas: {repr(e)}")
        return {'critico': 0, 'urgente': 0, 'ok': 0}

def contar_alertas():
    try:
        totales = obtener_totales_alertas()
        return totales['critico'] + totales['urgente']
    except Exception as e:
        print(f"Error en contar_alertas: {repr(e)}")
        return 0

def eliminar_alerta(p_producto_id):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = "DELETE FROM alertas_quiebre WHERE producto_id = %s"
                    cursor.execute(sql, (p_producto_id,))
                conn.commit()
            return True
        return False
    except Exception as e:
        print(f"Error en eliminar_alerta: {repr(e)}")
        return False

def actualizar_alerta_sincronizada(p_alerta, p_motivo='Ajuste desde edicion de alerta'):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # 1. Leer stock actual para el historial
                    sql_info = "SELECT stock_total FROM productos WHERE id = %s"
                    cursor.execute(sql_info, (p_alerta.producto_id,))
                    row = cursor.fetchone()
                    if not row:
                        return False

                    stock_anterior = row['stock_total']

                    # 2. UPDATE productos — sincroniza stock_total, venta_dia y stock_minimo
                    #    en una sola sentencia para evitar múltiples round-trips y
                    #    asegurar que venta_dia (enviado desde el form de alertas) se persiste.
                    sql_prod = """
                        UPDATE productos
                           SET stock_total  = %s,
                               venta_dia    = %s,
                               stock_minimo = COALESCE(%s, stock_minimo)
                         WHERE id = %s
                    """
                    cursor.execute(sql_prod, (
                        p_alerta.unidades,
                        p_alerta.venta_dia,
                        p_alerta.stock_minimo,
                        p_alerta.producto_id
                    ))

                    # 3. UPSERT alertas_quiebre
                    sql_upsert = """
                        INSERT INTO alertas_quiebre (producto_id, estado_transf)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE
                        estado_transf=VALUES(estado_transf), updated_at=NOW(), activo=1
                    """
                    cursor.execute(sql_upsert, (p_alerta.producto_id, p_alerta.estado_transf))

                    # 4. Historial
                    from productosAD import _registrar_historial
                    _registrar_historial(
                        cursor, p_alerta.producto_id, 'UPDATE',
                        campo='stock_total_alerta',
                        anterior=stock_anterior,
                        nuevo=p_alerta.unidades,
                        motivo=p_motivo
                    )
                conn.commit()
            return True
        return False
    except Exception as e:
        print(f"Error en actualizar_alerta_sincronizada: {repr(e)}")
        return False

# ==============================================================================
# LECTURA POR ID — Alerta (Fix P1: elimina SQL directo en app.py)
# ==============================================================================
def obtener_alerta_xID(p_alerta_id):
    """
    Retorna una alerta por su id propio (alertas_quiebre.id),
    enriquecida con los datos del producto (sku, stock, venta_dia, etc.).
    """
    try:
        conn = obtenerconexion()
        if not conn:
            return None
        with conn:
            with conn.cursor() as cursor:
                sql = """
                    SELECT a.id          AS alerta_id,
                           a.producto_id,
                           a.estado_transf,
                           a.activo,
                           a.updated_at,
                           p.sku,
                           p.nombre      AS producto,
                           p.categoria,
                           p.stock_total AS unidades,
                           p.venta_dia,
                           p.stock_minimo
                    FROM alertas_quiebre a
                    JOIN productos p ON p.id = a.producto_id
                    WHERE a.id = %s
                """
                cursor.execute(sql, (p_alerta_id,))
                return cursor.fetchone()
    except Exception as e:
        print(f"Error en obtener_alerta_xID: {repr(e)}")
        return None


# ==============================================================================
# CREAR O REACTIVAR ALERTA (Fix P3: elimina SQL directo en app.py)
# ==============================================================================
def crear_o_reactivar_alerta(p_producto_id, p_estado_transf='Sin transferencia activa'):
    """
    UPSERT en alertas_quiebre.
    - Si no existe alerta para el producto, la crea (activo=1).
    - Si ya existe, la reactiva y actualiza estado_transf.
    Los datos de stock/venta/stock_minimo viven en 'productos', no aquí.
    Retorna True si tuvo éxito, False en caso contrario.
    """
    try:
        conn = obtenerconexion()
        if not conn:
            return False
        with conn:
            with conn.cursor() as cursor:
                # Verificar que el producto existe y está activo
                cursor.execute(
                    "SELECT id FROM productos WHERE id = %s AND activo = 1",
                    (p_producto_id,)
                )
                if not cursor.fetchone():
                    return False
                cursor.execute(
                    """INSERT INTO alertas_quiebre (producto_id, estado_transf, activo)
                       VALUES (%s, %s, 1)
                       ON DUPLICATE KEY UPDATE
                           estado_transf = VALUES(estado_transf),
                           activo        = 1,
                           updated_at    = NOW()""",
                    (p_producto_id, p_estado_transf)
                )
            conn.commit()
        return True
    except Exception as e:
        print(f"Error en crear_o_reactivar_alerta: {repr(e)}")
        return False
