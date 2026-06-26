from datetime import datetime
from bd import obtenerconexion

# ==============================================================================
# CLASES DE ENTIDAD - PRODUCTO Xavier Ruiz Guevara
# ==============================================================================
class clsProducto:
    def __init__(self, p_id=None, p_sku=None, p_nombre=None,
                 p_categoria=None, p_stock_total=None,
                 p_precio_unitario=None, p_venta_dia=None,
                 p_stock_minimo=None, p_ubicacion_gondola=None):
        self.id               = p_id
        self.sku              = p_sku
        self.nombre           = p_nombre
        self.categoria        = p_categoria
        self.stock_total      = p_stock_total
        self.precio_unitario  = p_precio_unitario
        self.venta_dia        = p_venta_dia
        self.stock_minimo     = p_stock_minimo
        self.ubicacion_gondola = p_ubicacion_gondola
# ==============================================================================
# AUTENTICACION
# ==============================================================================
def autenticar_usuario(p_codigo, p_password):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT id, codigo_empleado, nombre, rol, password, sede 
                        FROM usuarios 
                        WHERE codigo_empleado = %s AND activo = 1
                    """
                    cursor.execute(sql, (p_codigo,))
                    usuario = cursor.fetchone()
                    
                    if usuario:
                        if not isinstance(usuario, dict):
                            columnas = ['id', 'codigo_empleado', 'nombre', 'rol', 'password', 'sede']
                            usuario = dict(zip(columnas, usuario))
                        
                        if usuario['password'] == p_password:
                            return usuario
        return None
    except Exception as e:
        print("Error en autenticacion:", repr(e))
        return None

# ==============================================================================
# CRUD — PRODUCTOS - Xavier Ruiz Guevara 
# ==============================================================================
def leer_productos(p_busqueda=None):
    try:
        conn = obtenerconexion()
        result = None
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT id, sku, nombre, categoria, "
                    sql += "        stock_total, precio_unitario, "
                    sql += "        venta_dia, stock_minimo, ubicacion_gondola, activo "
                    sql += "   FROM productos "
                    sql += "  WHERE activo = 1 "
                    params = ()
                    if p_busqueda:
                        sql += "    AND (nombre LIKE %s "
                        sql += "         OR sku LIKE %s "
                        sql += "         OR categoria LIKE %s) "
                        params = (
                            f'%{p_busqueda}%',
                            f'%{p_busqueda}%',
                            f'%{p_busqueda}%',
                        )
                    sql += "  ORDER BY nombre "
                    cursor.execute(sql, params)
                    result = cursor.fetchall()
        return result
    except Exception:
        raise

def leer_producto_por_id(p_id):
    try:
        conn = obtenerconexion()
        result = None
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT id, sku, nombre, categoria, "
                    sql += "        stock_total, precio_unitario, "
                    sql += "        venta_dia, stock_minimo, ubicacion_gondola, activo "
                    sql += "   FROM productos "
                    sql += "  WHERE id = %s AND activo = 1 "
                    cursor.execute(sql, (p_id,))
                    result = cursor.fetchone()
        return result
    except Exception:
        raise

def insertar_producto(p_producto):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT id FROM productos "
                    sql += "  WHERE sku = %s AND activo = 1 "
                    cursor.execute(sql, (p_producto.sku,))
                    if cursor.fetchone():
                        return False

                    sql  = " INSERT INTO `productos` "
                    sql += "   (`sku`, `nombre`, `categoria`, `stock_total`, "
                    sql += "    `precio_unitario`, `venta_dia`, `stock_minimo`, `ubicacion_gondola`) "
                    sql += " VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
                    cursor.execute(sql, (
                        p_producto.sku,
                        p_producto.nombre,
                        p_producto.categoria or '',
                        p_producto.stock_total or 0,
                        p_producto.precio_unitario or 0,
                        p_producto.venta_dia or 0,
                        p_producto.stock_minimo or 0,
                        p_producto.ubicacion_gondola or '',
                    ))
                    nuevo_id = cursor.lastrowid
                    _registrar_historial(
                        cursor, nuevo_id, 'CREATE',
                        motivo=f'Producto "{p_producto.nombre}" agregado al catalogo'
                    )
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False

def actualizar_producto(p_producto):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT id, sku, stock_total FROM productos "
                    sql += "  WHERE id = %s "
                    cursor.execute(sql, (p_producto.id,))
                    anterior = cursor.fetchone()
                    if not anterior:
                        return False

                    sql =  " SELECT id FROM productos "
                    sql += "  WHERE sku = %s AND id != %s AND activo = 1 "
                    cursor.execute(sql, (p_producto.sku, p_producto.id))
                    if cursor.fetchone():
                        return False 

                    sql  = " UPDATE `productos` "
                    sql += "    SET `sku` = %s, `nombre` = %s, "
                    sql += "        `categoria` = %s, `stock_total` = %s, "
                    sql += "        `precio_unitario` = %s, `venta_dia` = %s, "
                    sql += "        `stock_minimo` = %s, `ubicacion_gondola` = %s "
                    sql += "  WHERE `id` = %s "
                    cursor.execute(sql, (
                        p_producto.sku,
                        p_producto.nombre,
                        p_producto.categoria or '',
                        p_producto.stock_total or 0,
                        p_producto.precio_unitario or 0,
                        p_producto.venta_dia or 0,
                        p_producto.stock_minimo or 0,
                        p_producto.ubicacion_gondola or '',
                        p_producto.id,
                    ))
                    if p_producto.stock_total != anterior['stock_total']:
                        _registrar_historial(
                            cursor, p_producto.id, 'UPDATE',
                            campo='stock_total',
                            anterior=anterior['stock_total'],
                            nuevo=p_producto.stock_total,
                            motivo='Edicion desde catalogo'
                        )
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False

def eliminar_producto(p_id):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT id, nombre FROM productos "
                    sql += "  WHERE id = %s "
                    cursor.execute(sql, (p_id,))
                    row = cursor.fetchone()
                    if not row:
                        return False

                    sql = " UPDATE productos SET activo = 0 WHERE id = %s "
                    cursor.execute(sql, (p_id,))

                    sql = " UPDATE alertas_quiebre SET activo = 0 WHERE producto_id = %s "
                    cursor.execute(sql, (p_id,))

                    sql = " UPDATE segmentacion_inventario SET activo = 0 WHERE producto_id = %s "
                    cursor.execute(sql, (p_id,))

                    _registrar_historial(
                        cursor, p_id, 'DELETE',
                        motivo='Producto desactivado'
                    )
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False

def buscar_sku(p_sku):
    try:
        conn = obtenerconexion()
        result = None
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT p.id, p.sku, p.nombre, p.categoria, "
                    sql += "        p.stock_total, p.precio_unitario, "
                    sql += "        p.venta_dia, p.stock_minimo, p.ubicacion_gondola, "
                    sql += "        COALESCE(a.estado_transf, 'Sin transferencia activa') "
                    sql += "            AS estado_transf "
                    sql += "   FROM productos p "
                    sql += "   LEFT JOIN alertas_quiebre a "
                    sql += "          ON a.producto_id = p.id AND a.activo = 1 "
                    sql += "  WHERE p.sku = %s AND p.activo = 1 "
                    sql += "  LIMIT 1 "
                    cursor.execute(sql, (p_sku.upper(),))
                    result = cursor.fetchone()
        return result
    except Exception as e:
        print(repr(e))
        return None

# ==============================================================================
# HISTORIAL
# ==============================================================================
def _registrar_historial(cursor, producto_id, accion,
                         campo=None, anterior=None, nuevo=None, motivo=None):
    sql  = " INSERT INTO historial_ajustes "
    sql += "   (producto_id, usuario_id, empleado_nombre, accion, "
    sql += "    campo_modificado, valor_anterior, valor_nuevo, motivo) "
    sql += " VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
    cursor.execute(sql, (
        producto_id,
        1,
        'Sistema',
        accion,
        campo,
        str(anterior) if anterior is not None else None,
        str(nuevo)    if nuevo    is not None else None,
        motivo,
    ))

def leer_historial(p_accion=None, p_limite=200):
    try:
        conn = obtenerconexion()
        result = None
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT fecha, producto_nombre, sku, "
                    sql += "        empleado_nombre, empleado_rol, accion, "
                    sql += "        campo_modificado, valor_anterior, "
                    sql += "        valor_nuevo, motivo "
                    sql += "   FROM v_historial_completo "
                    params = ()
                    if p_accion:
                        sql += "  WHERE accion = %s "
                        params = (p_accion.upper(),)
                    sql += "  ORDER BY fecha DESC "
                    sql += "  LIMIT %s "
                    params = params + (p_limite,)
                    cursor.execute(sql, params)
                    result = cursor.fetchall()
        return result
    except Exception:
        raise

def registrar_historial(p_producto_id, p_accion,
                        p_campo=None, p_anterior=None,
                        p_nuevo=None, p_motivo=None):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    _registrar_historial(
                        cursor, p_producto_id, p_accion,
                        campo=p_campo,
                        anterior=p_anterior,
                        nuevo=p_nuevo,
                        motivo=p_motivo
                    )
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False

# ==============================================================================
# CONTEOS MANUALES
# ==============================================================================
class clsConteo:
    def __init__(self, p_id=None, p_producto_id=None, p_usuario_id=None,
                 p_stock_sistema=None, p_stock_contado=None,
                 p_diferencia=None, p_motivo=None, p_estado=None):
        self.id            = p_id
        self.producto_id   = p_producto_id
        self.usuario_id    = p_usuario_id
        self.stock_sistema = p_stock_sistema
        self.stock_contado = p_stock_contado
        self.diferencia    = p_diferencia
        self.motivo        = p_motivo
        self.estado        = p_estado

def leer_conteos():
    try:
        conn = obtenerconexion()
        lista_final = []
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql  = " SELECT producto_id, usuario_id, stock_sistema, "
                    sql += "        stock_contado, diferencia, motivo, estado, fecha "
                    sql += "   FROM conteos_manuales "
                    sql += "  ORDER BY fecha DESC "
                    cursor.execute(sql)
                    result = cursor.fetchall()
                    for fila in result:
                        lista_final.append({
                            "producto_id":   fila['producto_id'],
                            "usuario_id":    fila['usuario_id'],
                            "stock_sistema": fila['stock_sistema'],
                            "stock_contado": fila['stock_contado'],
                            "diferencia":    fila['diferencia'],
                            "motivo":        fila['motivo'],
                            "estado":        fila['estado'],
                            "fecha":         str(fila['fecha'])
                        })
        return lista_final
    except Exception as e:
        print(repr(e))
        return []

def insertar_conteo(p_conteo):
    # NOTA: 'diferencia' es columna GENERATED en el schema; se omite del INSERT
    # y MySQL la calcula automáticamente como (stock_contado - stock_sistema).
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " INSERT INTO conteos_manuales "
                    sql += " (producto_id, usuario_id, stock_sistema, "
                    sql += "  stock_contado, motivo, estado, fecha) "
                    sql += " VALUES (%s, %s, %s, %s, %s, %s, NOW()) "

                    cursor.execute(sql, (
                        p_conteo.producto_id,
                        p_conteo.usuario_id,
                        p_conteo.stock_sistema,
                        p_conteo.stock_contado,
                        p_conteo.motivo,
                        p_conteo.estado or 'aplicado'
                    ))
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False

def insertar_conteo_manual(p_prod_id, p_contado, p_motivo=''):
    try:
        conn = obtenerconexion()
        if not conn:
            return False, None
        with conn:
            with conn.cursor() as cursor:
                sql  = " SELECT stock_total FROM productos "
                sql += "  WHERE id = %s AND activo = 1 "
                cursor.execute(sql, (p_prod_id,))
                prod = cursor.fetchone()
                if not prod:
                    return False, None

                stock_anterior = prod['stock_total']

                sql  = " INSERT INTO conteos_manuales "
                sql += "   (producto_id, usuario_id, stock_sistema, "
                sql += "    stock_contado, motivo, estado) "
                sql += " VALUES (%s, %s, %s, %s, %s, 'aplicado') "
                cursor.execute(sql, (
                    p_prod_id, 1, stock_anterior,
                    int(p_contado), p_motivo
                ))

                sql  = " UPDATE productos "
                sql += "    SET stock_total = %s "
                sql += "  WHERE id = %s "
                cursor.execute(sql, (int(p_contado), p_prod_id))

                _registrar_historial(
                    cursor, p_prod_id, 'CONTEO',
                    campo='stock_total',
                    anterior=stock_anterior,
                    nuevo=p_contado,
                    motivo=p_motivo or 'Conteo manual desde escaner'
                )
            conn.commit()
        return True, stock_anterior
    except Exception as e:
        print(repr(e))
        return False, None

# ==============================================================================
# INTEGRIDAD REFERENCIAL
# ==============================================================================
def verificar_dependencias_producto(prod_id):
    try:
        conn = obtenerconexion()
        if not conn: return "Sin conexion"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS n FROM segmentacion_inventario WHERE producto_id=%s AND activo=1", (prod_id,))
                if cursor.fetchone()['n'] > 0: return "El producto tiene segmentaciones activas."
                cursor.execute("SELECT COUNT(*) AS n FROM alertas_quiebre WHERE producto_id=%s AND activo=1", (prod_id,))
                if cursor.fetchone()['n'] > 0: return "El producto tiene alertas activas."
                cursor.execute("SELECT COUNT(*) AS n FROM conteos_manuales WHERE producto_id=%s", (prod_id,))
                if cursor.fetchone()['n'] > 0: return "El producto tiene conteos manuales."
        return None
    except Exception as e: return str(e)

def verificar_dependencias_trabajador(usuario_id):
    try:
        conn = obtenerconexion()
        if not conn: return "Sin conexion"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) AS n FROM conteos_manuales WHERE usuario_id=%s", (usuario_id,))
                if cursor.fetchone()['n'] > 0: return "El trabajador tiene conteos registrados."
                cursor.execute("SELECT COUNT(*) AS n FROM historial_ajustes WHERE usuario_id=%s", (usuario_id,))
                if cursor.fetchone()['n'] > 0: return "El trabajador tiene registros en el historial."
        return None
    except Exception as e: return str(e)
