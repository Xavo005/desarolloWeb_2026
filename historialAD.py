from bd import obtenerconexion

# ==============================================================================
# CLASE DE ENTIDAD - HISTORIAL
# ==============================================================================
class clsHistorial:
    def __init__(self, p_id=None, p_producto_id=None, p_usuario_id=None, 
                 p_empleado_nombre=None, p_empleado_rol=None, p_accion=None, 
                 p_campo=None, p_anterior=None, p_nuevo=None, p_motivo=None, p_fecha=None):
        self.id = p_id
        self.producto_id = p_producto_id
        self.usuario_id = p_usuario_id
        self.empleado_nombre = p_empleado_nombre
        self.empleado_rol = p_empleado_rol
        self.accion = p_accion
        self.campo_modificado = p_campo
        self.valor_anterior = p_anterior
        self.valor_nuevo = p_nuevo
        self.motivo = p_motivo
        self.fecha = p_fecha

# ==============================================================================
# CRUD — HISTORIAL - Diego Calderon
# ==============================================================================

def leer():
    try:
        conn = obtenerconexion()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM v_historial_completo ORDER BY fecha DESC")
            return cursor.fetchall()
    except Exception: raise

def leer_por_id(p_id):
    try:
        conn = obtenerconexion()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM v_historial_completo WHERE id = %s", (p_id,))
            return cursor.fetchone()
    except Exception: raise

def guardar(p_historial):
    try:
        conn = obtenerconexion()
        with conn.cursor() as cursor:
            # Quitamos 'empleado_rol' de aquí
            sql = """INSERT INTO historial_ajustes 
                     (producto_id, usuario_id, empleado_nombre, accion, 
                      campo_modificado, valor_anterior, valor_nuevo, motivo) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            
            # Quitamos 'p_historial.empleado_rol' de aquí
            cursor.execute(sql, (p_historial.producto_id, 
                                 p_historial.usuario_id, 
                                 p_historial.empleado_nombre, 
                                 p_historial.accion, 
                                 p_historial.campo_modificado, 
                                 p_historial.valor_anterior, 
                                 p_historial.valor_nuevo, 
                                 p_historial.motivo))
        conn.commit()
        return True
    except Exception as e:
        print(f"ERROR EN GUARDAR: {e}")
        return False

def actualizar(p_id, p_historial):
    try:
        conn = obtenerconexion()
        with conn.cursor() as cursor:
            sql = """UPDATE historial_ajustes 
                     SET accion = %s, campo_modificado = %s, valor_anterior = %s, 
                         valor_nuevo = %s, motivo = %s 
                     WHERE id = %s"""
            cursor.execute(sql, (p_historial.accion, p_historial.campo_modificado, 
                                 p_historial.valor_anterior, p_historial.valor_nuevo, 
                                 p_historial.motivo, p_id))
        conn.commit()
        return True
    except Exception: return False

def eliminar(p_id):
    try:
        conn = obtenerconexion()
        with conn.cursor() as cursor:
            sql = "DELETE FROM historial_ajustes WHERE id = %s"
            cursor.execute(sql, (p_id,))
        conn.commit()
        return True
    except Exception: return False