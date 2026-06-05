from bd import obtenerconexion

class clsSegmentacion:
    def __init__(self, id=None, producto_id=None, stock_cliente_final=0, 
                 stock_revendedor=0, limite_compra_final=0, 
                 limite_compra_revendedor=0, motivo=None):
        self.id = id
        self.producto_id = producto_id
        self.stock_cliente_final = stock_cliente_final
        self.stock_revendedor = stock_revendedor
        self.limite_compra_final = limite_compra_final
        self.limite_compra_revendedor = limite_compra_revendedor
        self.motivo = motivo

def obtener_segmentaciones():
    try:
        conn = obtenerconexion()
        lista = []
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql  = " SELECT s.id, s.producto_id, s.usuario_id, "
                    sql += "        s.stock_cliente_final, s.stock_revendedor, "
                    sql += "        s.limite_compra_final, s.limite_compra_revendedor, "
                    sql += "        s.motivo, s.activo, "
                    sql += "        p.nombre, p.sku, p.stock_total "
                    sql += "   FROM segmentacion_inventario s "
                    sql += "   JOIN productos p ON s.producto_id = p.id "
                    sql += "  ORDER BY s.fecha_creacion DESC "
                    cursor.execute(sql)
                    lista = cursor.fetchall()
        return lista
    except Exception as e:
        print(repr(e))
        return []

def obtener_segmentacion_xID(p_seg_id):
    try:
        conn = obtenerconexion()
        fila = None
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql  = " SELECT s.id, s.producto_id, s.usuario_id, "
                    sql += "        s.stock_cliente_final, s.stock_revendedor, "
                    sql += "        s.limite_compra_final, s.limite_compra_revendedor, "
                    sql += "        s.motivo, s.activo, "
                    sql += "        p.nombre, p.sku, p.stock_total "
                    sql += "   FROM segmentacion_inventario s "
                    sql += "   JOIN productos p ON s.producto_id = p.id "
                    sql += "  WHERE s.id = %s "
                    cursor.execute(sql, (p_seg_id,))
                    fila = cursor.fetchone()
        return fila
    except Exception as e:
        print(repr(e))
        return None

def insertar_segmentacion(p_Segmentacion):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO segmentacion_inventario
                        (producto_id, usuario_id, stock_cliente_final, stock_revendedor,
                         limite_compra_final, limite_compra_revendedor, motivo)
                        VALUES (%s, 1, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (p_Segmentacion.producto_id, p_Segmentacion.stock_cliente_final,
                                         p_Segmentacion.stock_revendedor, p_Segmentacion.limite_compra_final,
                                         p_Segmentacion.limite_compra_revendedor, p_Segmentacion.motivo))
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False

def actualizar_segmentacion(p_Segmentacion):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        UPDATE segmentacion_inventario
                        SET stock_cliente_final=%s, stock_revendedor=%s,
                            limite_compra_final=%s, limite_compra_revendedor=%s,
                            motivo=%s, updated_at=NOW()
                        WHERE id=%s
                    """
                    cursor.execute(sql, (p_Segmentacion.stock_cliente_final, p_Segmentacion.stock_revendedor,
                                         p_Segmentacion.limite_compra_final, p_Segmentacion.limite_compra_revendedor,
                                         p_Segmentacion.motivo, p_Segmentacion.id))
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False

def eliminar_segmentacion(p_seg_id):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM segmentacion_inventario WHERE id=%s", (p_seg_id,))
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False

def toggle_segmentacion(p_seg_id):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE segmentacion_inventario SET activo = 1 - activo WHERE id = %s", (p_seg_id,))
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False

def validar_stock_disponible(p_producto_id, p_stock_requerido):
    try:
        conn = obtenerconexion()
        if not conn:
            return "Error de conexion al verificar stock."
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT stock_total FROM productos WHERE id=%s AND activo=1", (p_producto_id,))
                prod = cursor.fetchone()
                if not prod:
                    return "Producto no encontrado o inactivo."

                if p_stock_requerido > prod['stock_total']:
                    return f"Stock insuficiente. Disponible: {prod['stock_total']}, Solicitado: {p_stock_requerido}"
        return None
    except Exception as e:
        return f"Error al validar stock: {repr(e)}"
