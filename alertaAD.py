from datetime import datetime
from bd import obtenerconexion

class clsAlerta:
    def __init__(self, id=None, producto_id=None, producto=None, sku=None, 
                 categoria=None, unidades=None, venta_dia=None, estado_transf=None):
        self.id = id
        self.producto_id = producto_id
        self.producto = producto
        self.sku = sku
        self.categoria = categoria
        self.unidades = unidades
        self.venta_dia = venta_dia
        self.estado_transf = estado_transf

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

def obtener_alertas_dinamicas():
    """
    Calcula alertas con prediccion dinamica basada en historial.
    Sin SQL en el controlador (regla 3 capas).
    """
    try:
        conn = obtenerconexion()
        if not conn:
            return [], {'critico': 0, 'urgente': 0, 'ok': 0}
            
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT a.id, a.producto_id, a.producto, a.sku, a.categoria,
                           p.stock_total AS unidades, p.venta_dia, a.estado_transf,
                           a.stock_minimo
                    FROM alertas_quiebre a
                    JOIN productos p ON a.producto_id = p.id
                    WHERE a.activo = 1
                """)
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
                        'id': a['id'],
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

def obtener_alertas_activas():
    try:
        conn = obtenerconexion()
        alertas = []
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql  = " SELECT a.id, a.sku, a.producto, "
                    sql += "        a.categoria, a.nivel, p.stock_total AS unidades, "
                    sql += "        a.stock_minimo, a.venta_dia, "
                    sql += "        a.horas_restantes, a.estado_transf, "
                    sql += "        p.stock_total, p.ubicacion_gondola "
                    sql += "   FROM alertas_quiebre a "
                    sql += "   JOIN productos p ON a.producto_id = p.id "
                    sql += "  WHERE a.activo = 1 "
                    sql += "  ORDER BY a.horas_restantes ASC "
                    cursor.execute(sql)
                    alertas = cursor.fetchall()
        return alertas
    except Exception as e:
        print(repr(e))
        return []

def obtener_totales_alertas():
    try:
        conn = obtenerconexion()
        totales = {'critico': 0, 'urgente': 0, 'ok': 0}
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT nivel, COUNT(*) AS n FROM alertas_quiebre 
                        WHERE activo=1 GROUP BY nivel
                    """)
                    for fila in cursor.fetchall():
                        totales[fila['nivel']] = fila['n']
        return totales
    except Exception as e:
        print(repr(e))
        return {'critico': 0, 'urgente': 0, 'ok': 0}

def eliminar_alerta(p_alerta_id):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE alertas_quiebre SET activo=0 WHERE id=%s", (p_alerta_id,))
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False

def actualizar_alerta(p_Alerta):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        UPDATE alertas_quiebre 
                        SET unidades=%s, venta_dia=%s, estado_transf=%s, updated_at=NOW()
                        WHERE id=%s
                    """
                    cursor.execute(sql, (p_Alerta.unidades, p_Alerta.venta_dia, 
                                        p_Alerta.estado_transf, p_Alerta.id))
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False

def actualizar_alerta_sincronizada(p_alerta_id, p_unidades, p_venta_dia, p_estado_transf, p_motivo='Ajuste desde edicion de alerta'):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql_info = """
                        SELECT a.producto_id, p.stock_total 
                        FROM alertas_quiebre a
                        JOIN productos p ON a.producto_id = p.id
                        WHERE a.id = %s AND a.activo = 1
                    """
                    cursor.execute(sql_info, (p_alerta_id,))
                    row = cursor.fetchone()
                    if not row:
                        return False
                    
                    producto_id = row['producto_id']
                    stock_anterior = row['stock_total']

                    sql_alerta = """
                        UPDATE alertas_quiebre
                           SET unidades = %s, venta_dia = %s, estado_transf = %s, updated_at = NOW()
                         WHERE id = %s
                    """
                    cursor.execute(sql_alerta, (p_unidades, p_venta_dia, p_estado_transf, p_alerta_id))

                    sql_producto = """
                        UPDATE productos
                           SET stock_total = %s
                         WHERE id = %s
                    """
                    cursor.execute(sql_producto, (p_unidades, producto_id))

                    # Import local para evitar circularidad
                    from procutosAD import _registrar_historial
                    _registrar_historial(
                        cursor, producto_id, 'UPDATE',
                        campo='stock_total_alerta',
                        anterior=stock_anterior,
                        nuevo=p_unidades,
                        motivo=p_motivo
                    )
                conn.commit()
            return True
        return False
    except Exception as e:
        print("Error en actualizar_alerta_sincronizada:", repr(e))
        return False

def contar_alertas():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql  = " SELECT COUNT(*) AS n "
                    sql += "   FROM alertas_quiebre "
                    sql += "  WHERE activo = 1 "
                    sql += "    AND nivel IN ('critico', 'urgente') "
                    cursor.execute(sql)
                    row = cursor.fetchone()
                    return row['n'] if row else 0
        return 0
    except Exception as e:
        print(repr(e))
        return 0
