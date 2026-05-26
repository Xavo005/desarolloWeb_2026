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


# ════════════════════════════════════════════════════════════
# CLASES DE ENTIDAD — SEGMENTACION Y ALERTA
# ════════════════════════════════════════════════════════════

class clsSegmentacion:
    def __init__(self, p_id=None, p_producto_id=None, p_usuario_id=None,
                 p_stock_cliente_final=None, p_stock_revendedor=None,
                 p_limite_compra_final=None, p_limite_compra_revendedor=None,
                 p_motivo=None, p_activo=None):
        self.id                      = p_id
        self.producto_id             = p_producto_id
        self.usuario_id              = p_usuario_id
        self.stock_cliente_final     = p_stock_cliente_final
        self.stock_revendedor        = p_stock_revendedor
        self.limite_compra_final     = p_limite_compra_final
        self.limite_compra_revendedor = p_limite_compra_revendedor
        self.motivo                  = p_motivo
        self.activo                  = p_activo


class clsAlerta:
    def __init__(self, p_id=None, p_producto_id=None, p_sku=None,
                 p_producto=None, p_nivel=None, p_horas_restantes=None,
                 p_estado_transf=None, p_activo=None):
        self.id              = p_id
        self.producto_id     = p_producto_id
        self.sku             = p_sku
        self.producto        = p_producto
        self.nivel           = p_nivel
        self.horas_restantes = p_horas_restantes
        self.estado_transf   = p_estado_transf
        self.activo          = p_activo


# ════════════════════════════════════════════════════════════
# CRUD — SEGMENTACIONES
# ════════════════════════════════════════════════════════════

def leer_segmentaciones():
    """
    Retorna lista de segmentaciones con datos del producto asociado,
    ordenadas por fecha de creacion descendente.
    """
    try:
        conn = obtenerconexion()
        result = None
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT s.id, s.producto_id, s.usuario_id, "
                    sql += "        s.stock_cliente_final, s.stock_revendedor, "
                    sql += "        s.limite_compra_final, s.limite_compra_revendedor, "
                    sql += "        s.motivo, s.activo, s.fecha_creacion, "
                    sql += "        p.nombre, p.sku, p.stock_total "
                    sql += "   FROM segmentacion_inventario s "
                    sql += "   JOIN productos p ON s.producto_id = p.id "
                    sql += "  ORDER BY s.fecha_creacion DESC "
                    cursor.execute(sql)
                    result = cursor.fetchall()
        return result
    except Exception:
        raise


def leer_segmentacion_por_id(p_id):
    """
    Retorna un dict con la segmentacion y datos del producto o None si no existe.
    """
    try:
        conn = obtenerconexion()
        result = None
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT s.id, s.producto_id, s.usuario_id, "
                    sql += "        s.stock_cliente_final, s.stock_revendedor, "
                    sql += "        s.limite_compra_final, s.limite_compra_revendedor, "
                    sql += "        s.motivo, s.activo, s.fecha_creacion, "
                    sql += "        p.nombre, p.sku, p.stock_total "
                    sql += "   FROM segmentacion_inventario s "
                    sql += "   JOIN productos p ON s.producto_id = p.id "
                    sql += "  WHERE s.id = %s "
                    cursor.execute(sql, (p_id,))
                    result = cursor.fetchone()
        return result
    except Exception:
        raise


def insertar_segmentacion(p_segmentacion):
    """
    Inserta un nuevo registro de segmentacion de inventario.
    Valida que la suma no supere el stock total del producto.
    Retorna True si se inserto, False si fallo la validacion o hubo error.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # Obtener stock total del producto
                    sql =  " SELECT stock_total FROM productos "
                    sql += "  WHERE id = %s AND activo = 1 "
                    cursor.execute(sql, (p_segmentacion.producto_id,))
                    prod = cursor.fetchone()
                    if not prod:
                        return False
                    total_asignado = (p_segmentacion.stock_cliente_final or 0) + \
                                     (p_segmentacion.stock_revendedor or 0)
                    if total_asignado > prod['stock_total']:
                        return False  # Supera stock disponible

                    sql  = " INSERT INTO `segmentacion_inventario` "
                    sql += "   (`producto_id`, `usuario_id`, `stock_cliente_final`, "
                    sql += "    `stock_revendedor`, `limite_compra_final`, "
                    sql += "    `limite_compra_revendedor`, `motivo`) "
                    sql += " VALUES (%s, %s, %s, %s, %s, %s, %s) "
                    cursor.execute(sql, (
                        p_segmentacion.producto_id,
                        p_segmentacion.usuario_id or 1,
                        p_segmentacion.stock_cliente_final or 0,
                        p_segmentacion.stock_revendedor or 0,
                        p_segmentacion.limite_compra_final or 0,
                        p_segmentacion.limite_compra_revendedor or 0,
                        p_segmentacion.motivo or '',
                    ))
                    _registrar_historial(
                        cursor, p_segmentacion.producto_id, 'CREATE',
                        motivo=p_segmentacion.motivo or 'Segmentacion creada'
                    )
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False


def actualizar_segmentacion(p_segmentacion):
    """
    Actualiza los campos de una segmentacion existente.
    Valida que la suma no supere el stock total del producto.
    Retorna True si actualizo, False si no encontro el registro o hubo error.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # Obtener datos anteriores
                    sql =  " SELECT s.stock_cliente_final, s.producto_id, "
                    sql += "        p.stock_total "
                    sql += "   FROM segmentacion_inventario s "
                    sql += "   JOIN productos p ON s.producto_id = p.id "
                    sql += "  WHERE s.id = %s "
                    cursor.execute(sql, (p_segmentacion.id,))
                    anterior = cursor.fetchone()
                    if not anterior:
                        return False

                    total_asignado = (p_segmentacion.stock_cliente_final or 0) + \
                                     (p_segmentacion.stock_revendedor or 0)
                    if total_asignado > anterior['stock_total']:
                        return False  # Supera stock disponible

                    sql  = " UPDATE `segmentacion_inventario` "
                    sql += "    SET `stock_cliente_final` = %s, "
                    sql += "        `stock_revendedor` = %s, "
                    sql += "        `limite_compra_final` = %s, "
                    sql += "        `limite_compra_revendedor` = %s, "
                    sql += "        `motivo` = %s, "
                    sql += "        `usuario_id` = %s, "
                    sql += "        `updated_at` = NOW() "
                    sql += "  WHERE `id` = %s "
                    cursor.execute(sql, (
                        p_segmentacion.stock_cliente_final or 0,
                        p_segmentacion.stock_revendedor or 0,
                        p_segmentacion.limite_compra_final or 0,
                        p_segmentacion.limite_compra_revendedor or 0,
                        p_segmentacion.motivo or '',
                        p_segmentacion.usuario_id or 1,
                        p_segmentacion.id,
                    ))
                    _registrar_historial(
                        cursor, anterior['producto_id'], 'UPDATE',
                        campo='stock_cliente_final',
                        anterior=anterior['stock_cliente_final'],
                        nuevo=p_segmentacion.stock_cliente_final,
                        motivo=p_segmentacion.motivo or 'Edicion de segmentacion'
                    )
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False


def eliminar_segmentacion(p_id):
    """
    Elimina fisicamente un registro de segmentacion de inventario.
    Retorna True si elimino, False si no existia o hubo error.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # Verificar que existe y obtener producto_id para historial
                    sql =  " SELECT producto_id FROM segmentacion_inventario "
                    sql += "  WHERE id = %s "
                    cursor.execute(sql, (p_id,))
                    row = cursor.fetchone()
                    if not row:
                        return False

                    _registrar_historial(
                        cursor, row['producto_id'], 'DELETE',
                        motivo='Segmentacion eliminada'
                    )
                    sql = " DELETE FROM `segmentacion_inventario` WHERE `id` = %s "
                    cursor.execute(sql, (p_id,))
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False


def toggle_segmentacion(p_id):
    """
    Activa o desactiva (toggle) una segmentacion de inventario.
    Retorna True si cambio el estado, False si no existia o hubo error.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # Obtener estado actual
                    sql =  " SELECT producto_id, activo "
                    sql += "   FROM segmentacion_inventario "
                    sql += "  WHERE id = %s "
                    cursor.execute(sql, (p_id,))
                    row = cursor.fetchone()
                    if not row:
                        return False

                    nuevo_estado = 0 if row['activo'] else 1
                    sql  = " UPDATE `segmentacion_inventario` "
                    sql += "    SET `activo` = %s "
                    sql += "  WHERE `id` = %s "
                    cursor.execute(sql, (nuevo_estado, p_id))

                    _registrar_historial(
                        cursor, row['producto_id'], 'TOGGLE',
                        campo='activo',
                        anterior=row['activo'],
                        nuevo=nuevo_estado,
                        motivo='Toggle de segmentacion'
                    )
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False


# ════════════════════════════════════════════════════════════
# ALERTAS
# ════════════════════════════════════════════════════════════

def contar_alertas():
    """
    Retorna el numero entero de alertas activas de nivel critico o urgente.
    Retorna 0 ante cualquier fallo.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT COUNT(*) AS n "
                    sql += "   FROM alertas_quiebre "
                    sql += "  WHERE activo = 1 "
                    sql += "    AND nivel IN ('critico', 'urgente') "
                    cursor.execute(sql)
                    row = cursor.fetchone()
                    return row['n'] if row else 0
        return 0
    except Exception:
        return 0


def leer_alertas():
    """
    Retorna lista completa de alertas activas desde la vista v_alertas_activas.
    """
    try:
        conn = obtenerconexion()
        result = None
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT id, producto_id, sku, producto, "
                    sql += "        nivel, horas_restantes, estado_transf "
                    sql += "   FROM v_alertas_activas "
                    cursor.execute(sql)
                    result = cursor.fetchall()
        return result
    except Exception:
        raise


def eliminar_alerta(p_id):
    """
    Desactiva (soft-delete) una alerta de quiebre.
    Retorna True si desactivo, False si no existia o hubo error.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT producto_id FROM alertas_quiebre "
                    sql += "  WHERE id = %s "
                    cursor.execute(sql, (p_id,))
                    row = cursor.fetchone()
                    if not row:
                        return False

                    sql  = " UPDATE `alertas_quiebre` "
                    sql += "    SET `activo` = 0 "
                    sql += "  WHERE `id` = %s "
                    cursor.execute(sql, (p_id,))

                    _registrar_historial(
                        cursor, row['producto_id'], 'DELETE',
                        motivo='Alerta descartada manualmente'
                    )
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False


# ════════════════════════════════════════════════════════════
# HISTORIAL — FUNCIONES PUBLICAS
# ════════════════════════════════════════════════════════════

def leer_historial(p_accion=None, p_limite=200):
    """
    Retorna registros del historial de ajustes desde la vista v_historial_completo.
    Filtra opcionalmente por tipo de accion.
    """
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
    """
    Version publica de _registrar_historial: abre su propia conexion.
    Util para llamadas externas desde app.py si fuera necesario.
    Retorna True si inserto, False si hubo error.
    """
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


# ════════════════════════════════════════════════════════════
# SEGURIDAD — CAMBIO DE CONTRASEÑA
# ════════════════════════════════════════════════════════════

def cambiar_clave(p_usuario_id, p_clave_actual, p_nueva_clave):
    """
    Verifica la clave actual por comparacion directa en texto plano y
    actualiza la contrasena sin usar werkzeug ni hashes avanzados.
    Retorna True si cambio, False si la clave actual no coincide o hubo error.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # Verificar que el usuario existe y la clave actual es correcta
                    sql =  " SELECT id, password_hash FROM usuarios "
                    sql += "  WHERE id = %s AND activo = 1 "
                    cursor.execute(sql, (p_usuario_id,))
                    usuario = cursor.fetchone()
                    if not usuario:
                        return False
                    if usuario['password_hash'] != p_clave_actual:
                        return False  # Clave actual incorrecta

                    sql  = " UPDATE `usuarios` "
                    sql += "    SET `password_hash` = %s "
                    sql += "  WHERE `id` = %s "
                    cursor.execute(sql, (p_nueva_clave, p_usuario_id))
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False

