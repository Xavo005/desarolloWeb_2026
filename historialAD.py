from bd import obtenerconexion


def leer_historial(p_accion=None, p_limite=200):
    conn = obtenerconexion()
    try:
        # Quitamos dictionary=True
        cursor = conn.cursor() 
        
        query = "SELECT * FROM v_historial_completo"
        params = []
        
        if p_accion:
            query += " WHERE accion = %s"
            params.append(p_accion)
        
        query += " ORDER BY fecha DESC LIMIT %s"
        params.append(p_limite)
        
        cursor.execute(query, tuple(params))
        
        # Obtenemos los nombres de las columnas manualmente
        columnas = [col[0] for col in cursor.description]
        # Convertimos cada fila en un diccionario
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
        
    except Exception as e:
        print(f"Error en BD: {e}")
        return []
    finally:
        conn.close()