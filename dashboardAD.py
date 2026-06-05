from bd import obtenerconexion

def obtener_stats_dashboard():
    try:
        stats = {'alertas_criticas': 0, 'total_productos': 0}
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) AS n FROM alertas_quiebre WHERE activo=1 AND nivel='critico'")
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
                    cursor.execute("""
                        SELECT sku, producto, nivel, horas_restantes
                        FROM alertas_quiebre WHERE activo=1 
                        ORDER BY horas_restantes ASC LIMIT 3
                    """)
                    alertas = cursor.fetchall()
        return alertas
    except Exception as e:
        print(repr(e))
        return []

def obtener_datos_graficos_dashboard():
    """
    Retorna los tres conjuntos de datos necesarios para los graficos del dashboard:
      - stock_por_categoria: SUM de stock_total agrupado por categoria.
      - tendencia_ajustes:   Conteo de ajustes de los ultimos 7 dias.
      - alertas_por_nivel:   Conteo de alertas activas agrupadas por nivel.
    Sin SQL en el controlador (cumple regla de 3 capas).
    """
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

                # 3. Alertas por nivel
                sql =  " SELECT nivel, COUNT(*) AS total "
                sql += "   FROM alertas_quiebre "
                sql += "  WHERE activo = 1 "
                sql += "  GROUP BY nivel "
                cursor.execute(sql)
                alertas_por_nivel = cursor.fetchall()

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
