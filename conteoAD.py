from bd import obtenerconexion


def registrar_conteo(p_producto_id, p_usuario_id, p_stock_sistema, p_stock_contado, p_motivo, p_estado):
    conn = obtenerconexion()
    try:
        with conn.cursor() as cursor:
            # He añadido el campo 'estado' explícitamente
            query = """
                INSERT INTO conteos_manuales 
                (producto_id, usuario_id, stock_sistema, stock_contado, motivo, estado, fecha) 
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(query, (p_producto_id, p_usuario_id, p_stock_sistema, p_stock_contado, p_motivo, p_estado))
            conn.commit()
            return True
    except Exception as e:
        print(f"ERROR EN REGISTRAR: {e}")
        return False
    finally:
        conn.close()

def listar_conteos_reales(p_limite=100):
    conn = obtenerconexion()
    try:
        with conn.cursor() as cursor:
            # Consulta ultra simple sin filtros
            cursor.execute("SELECT id, producto_id, usuario_id, stock_sistema, stock_contado, motivo, estado, fecha FROM conteos_manuales LIMIT %s", (p_limite,))
            
            # Recuperamos los datos
            filas = cursor.fetchall()
            
            # Si no hay filas, devolvemos lista vacía
            if not filas:
                return []
            
            # Creamos la lista manualmente para estar 100% seguros
            columnas = ['id', 'producto_id', 'usuario_id', 'stock_sistema', 'stock_contado', 'motivo', 'estado', 'fecha']
            resultados = []
            
            for fila in filas:
                # Convertimos la tupla fila a dict
                registro = dict(zip(columnas, fila))
                resultados.append(registro)
            
            return resultados
    except Exception as e:
        print(f"ERROR CRÍTICO EN LISTAR: {e}")
        return []
    finally:
        conn.close()