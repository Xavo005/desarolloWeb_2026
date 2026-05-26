"""
tottusAD.py — Tottus SGI · Capa de Acceso a Datos
Reglas estrictas del profesor:
  - Sin importaciones de Flask.
  - Conexion via bd.py (from bd import obtenerconexion).
  - SQL construido con patron: sql = " ... " y sql += " ... "
  - Sin SELECT *; columnas explicitas en todo SELECT.
  - Autenticacion: comparacion directa en texto plano (sin werkzeug.security).
"""
from bd import obtenerconexion


# ════════════════════════════════════════════════════════════
# CLASES DE ENTIDAD
# ════════════════════════════════════════════════════════════

class clsProducto:
    def __init__(self, p_id=None, p_sku=None, p_nombre=None,
                 p_categoria=None, p_stock_total=None,
                 p_precio_unitario=None, p_venta_dia=None,
                 p_ubicacion_gondola=None):
        self.id               = p_id
        self.sku              = p_sku
        self.nombre           = p_nombre
        self.categoria        = p_categoria
        self.stock_total      = p_stock_total
        self.precio_unitario  = p_precio_unitario
        self.venta_dia        = p_venta_dia
        self.ubicacion_gondola = p_ubicacion_gondola


class clsUsuario:
    def __init__(self, p_id=None, p_codigo_empleado=None,
                 p_nombre=None, p_rol=None,
                 p_password_hash=None, p_activo=None):
        self.id               = p_id
        self.codigo_empleado  = p_codigo_empleado
        self.nombre           = p_nombre
        self.rol              = p_rol
        self.password_hash    = p_password_hash
        self.activo           = p_activo


# ════════════════════════════════════════════════════════════
# AUTENTICACION
# ════════════════════════════════════════════════════════════

def autenticar_usuario(p_codigo, p_password):
    """
    Busca al usuario por codigo_empleado y compara la contrasena
    directamente en texto plano (sin werkzeug.security).
    Retorna un dict con los datos del usuario o None si falla.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT id, codigo_empleado, nombre, rol, password_hash "
                    sql += "   FROM usuarios "
                    sql += "  WHERE codigo_empleado = %s "
                    sql += "    AND password_hash = %s "
                    sql += "    AND activo = 1 "
                    cursor.execute(sql, (p_codigo, p_password))
                    usuario = cursor.fetchone()
                    if usuario:
                        return dict(usuario)
        return None
    except Exception as e:
        print(repr(e))
        return None


# ════════════════════════════════════════════════════════════
# CRUD — PRODUCTOS
# ════════════════════════════════════════════════════════════

def leer_productos(p_busqueda=None):
    """
    Retorna lista de productos activos.
    Si se pasa p_busqueda, filtra por nombre, SKU o categoria.
    """
    try:
        conn = obtenerconexion()
        result = None
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT id, sku, nombre, categoria, "
                    sql += "        stock_total, precio_unitario, "
                    sql += "        venta_dia, ubicacion_gondola, activo "
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
    """
    Retorna un dict con los datos del producto o None si no existe.
    """
    try:
        conn = obtenerconexion()
        result = None
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT id, sku, nombre, categoria, "
                    sql += "        stock_total, precio_unitario, "
                    sql += "        venta_dia, ubicacion_gondola, activo "
                    sql += "   FROM productos "
                    sql += "  WHERE id = %s AND activo = 1 "
                    cursor.execute(sql, (p_id,))
                    result = cursor.fetchone()
        return result
    except Exception:
        raise


def insertar_producto(p_producto):
    """
    Inserta un producto nuevo.
    Retorna True si se inserto, False si el SKU ya existe o hubo error.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # Verificar duplicado de SKU
                    sql =  " SELECT id FROM productos "
                    sql += "  WHERE sku = %s AND activo = 1 "
                    cursor.execute(sql, (p_producto.sku,))
                    if cursor.fetchone():
                        return False  # SKU ya existe

                    sql  = " INSERT INTO `productos` "
                    sql += "   (`sku`, `nombre`, `categoria`, `stock_total`, "
                    sql += "    `precio_unitario`, `venta_dia`, `ubicacion_gondola`) "
                    sql += " VALUES (%s, %s, %s, %s, %s, %s, %s) "
                    cursor.execute(sql, (
                        p_producto.sku,
                        p_producto.nombre,
                        p_producto.categoria or '',
                        p_producto.stock_total or 0,
                        p_producto.precio_unitario or 0,
                        p_producto.venta_dia or 0,
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
    """
    Actualiza los campos de un producto existente.
    Retorna True si actualizo, False si no lo encontro o hubo error.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # Verificar que existe
                    sql =  " SELECT id, sku, stock_total FROM productos "
                    sql += "  WHERE id = %s "
                    cursor.execute(sql, (p_producto.id,))
                    anterior = cursor.fetchone()
                    if not anterior:
                        return False

                    # Verificar que el nuevo SKU no este en uso por otro producto
                    sql =  " SELECT id FROM productos "
                    sql += "  WHERE sku = %s AND id != %s AND activo = 1 "
                    cursor.execute(sql, (p_producto.sku, p_producto.id))
                    if cursor.fetchone():
                        return False  # SKU duplicado

                    sql  = " UPDATE `productos` "
                    sql += "    SET `sku` = %s, `nombre` = %s, "
                    sql += "        `categoria` = %s, `stock_total` = %s, "
                    sql += "        `precio_unitario` = %s, `venta_dia` = %s, "
                    sql += "        `ubicacion_gondola` = %s "
                    sql += "  WHERE `id` = %s "
                    cursor.execute(sql, (
                        p_producto.sku,
                        p_producto.nombre,
                        p_producto.categoria or '',
                        p_producto.stock_total or 0,
                        p_producto.precio_unitario or 0,
                        p_producto.venta_dia or 0,
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
    """
    Desactiva (soft-delete) un producto y sus alertas/segmentaciones asociadas.
    Retorna True si se desactivo, False si no existia o hubo error.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # Verificar que existe
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
    """
    Busca un producto por SKU e incluye informacion de alerta activa.
    Retorna un dict o None. Usada exclusivamente por el escaner (excepcion aprobada).
    """
    try:
        conn = obtenerconexion()
        result = None
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT p.id, p.sku, p.nombre, p.categoria, "
                    sql += "        p.stock_total, p.precio_unitario, "
                    sql += "        p.venta_dia, p.ubicacion_gondola, "
                    sql += "        a.nivel AS alerta_nivel, "
                    sql += "        a.horas_restantes, "
                    sql += "        a.estado_transf "
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


# ════════════════════════════════════════════════════════════
# FUNCION PRIVADA — HISTORIAL
# ════════════════════════════════════════════════════════════

def _registrar_historial(cursor, producto_id, accion,
                         campo=None, anterior=None, nuevo=None, motivo=None):
    """
    Inserta un registro en historial_ajustes.
    Recibe el cursor ya abierto (sin abrir conexion nueva).
    Es privada: uso exclusivo interno de tottusAD.py.
    """
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
