from bd import obtenerconexion
from alertaAD import calcular_nivel_estatico

def obtener_stats_dashboard():
    try:
        stats = {'alertas_criticas': 0, 'total_productos': 0}
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # Contamos criticas (stock = 0)
                    cursor.execute("SELECT COUNT(*) AS n FROM productos WHERE activo=1 AND stock_total = 0")
                    stats['alertas_criticas'] = cursor.fetchone()['n']
                    
                    cursor.execute("SELECT COUNT(*) AS n FROM productos WHERE activo=1")
                    stats['total_productos'] = cursor.fetchone()['n']
        return stats
    except Exception as e:
        print(repr(e))
        return {'alertas_criticas': 0, 'total_productos': 0}

def obtener_alertas_recientes():
    try:
        conn = obtenerconexion()
        alertas = []
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # Obtenemos productos en alerta (stock <= stock_minimo) ordenados por menor stock
                    cursor.execute("""
                        SELECT p.sku, p.nombre AS producto, 
                               p.stock_total, p.stock_minimo, p.venta_dia
                        FROM productos p
                        WHERE p.activo=1 AND p.stock_total <= p.stock_minimo
                        ORDER BY p.stock_total ASC LIMIT 3
                    """)
                    rows = cursor.fetchall()
                    for row in rows:
                        stock = row['stock_total']
                        minimo = row['stock_minimo']
                        venta = float(row['venta_dia'] or 0)
                        
                        nivel = calcular_nivel_estatico(stock, minimo)
                        
                        horas = (stock / venta * 24) if venta > 0 else 9999
                        
                        alertas.append({
                            'sku': row['sku'],
                            'producto': row['producto'],
                            'nivel': nivel,
                            'horas_restantes': round(horas, 1)
                        })
        return alertas
    except Exception as e:
        print(repr(e))
        return []

def obtener_datos_graficos_dashboard():
    try:
        conn = obtenerconexion()
        if not conn:
            return {'stock_por_categoria': [], 'tendencia_ajustes': [], 'alertas_por_nivel': []}
        with conn:
            with conn.cursor() as cursor:
                # 1. Stock por categoria
                sql =  " SELECT categoria, SUM(stock_total) AS total_stock "
                sql += "   FROM productos "
                sql += "  WHERE activo = 1 "
                sql += "    AND categoria IS NOT NULL "
                sql += "    AND categoria != '' "
                sql += "  GROUP BY categoria "
                sql += "  ORDER BY total_stock DESC "
                cursor.execute(sql)
                stock_por_categoria = cursor.fetchall()

                # 2. Tendencia de ajustes (ultimos 7 dias)
                sql =  " SELECT DATE_FORMAT(fecha, '%Y-%m-%d') AS dia, "
                sql += "        COUNT(*) AS total "
                sql += "   FROM historial_ajustes "
                sql += "  WHERE fecha >= DATE_SUB(CURDATE(), INTERVAL 6 DAY) "
                sql += "  GROUP BY DATE(fecha) "
                sql += "  ORDER BY DATE(fecha) ASC "
                cursor.execute(sql)
                tendencia_ajustes = cursor.fetchall()

                # 3. Alertas por nivel (calculado en Python)
                cursor.execute("SELECT stock_total, stock_minimo FROM productos WHERE activo=1")
                productos = cursor.fetchall()
                
                niveles_count = {'critico': 0, 'urgente': 0, 'ok': 0}
                for p in productos:
                    stock = p['stock_total']
                    minimo = p['stock_minimo']
                    nivel = calcular_nivel_estatico(stock, minimo)
                    niveles_count[nivel] += 1
                
                alertas_por_nivel = []
                for n in ['critico', 'urgente', 'ok']:
                    if niveles_count[n] > 0:
                        alertas_por_nivel.append({'nivel': n, 'total': niveles_count[n]})

        return {
            'stock_por_categoria': stock_por_categoria,
            'tendencia_ajustes':   tendencia_ajustes,
            'alertas_por_nivel':   alertas_por_nivel,
        }
    except Exception as e:
        print(f"Error en obtener_datos_graficos_dashboard: {repr(e)}")
        return {'stock_por_categoria': [], 'tendencia_ajustes': [], 'alertas_por_nivel': []}

def leer_productos_basico():
    try:
        conn = obtenerconexion()
        if not conn:
            return []
        with conn:
            with conn.cursor() as cursor:
                sql =  " SELECT id, nombre, sku, stock_total "
                sql += "   FROM productos "
                sql += "  WHERE activo = 1 "
                sql += "  ORDER BY nombre "
                cursor.execute(sql)
                return cursor.fetchall()
    except Exception as e:
        print(f"Error en leer_productos_basico: {repr(e)}")
        return []
