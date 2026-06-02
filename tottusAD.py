from bd import obtenerconexion
# ==============================================================================
# DASHBOARD
# ==============================================================================

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

# ==============================================================================
# DASHBOARD — GRAFICOS (Gianella Torres — migrado desde app.py, regla 3 capas)
# ==============================================================================

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
    """
    Retorna id, nombre, sku y stock_total de los productos activos.
    Usado por la ruta de segmentacion para poblar el select de productos.
    Columnas explicitas (sin SELECT *).
    """
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


# ==============================================================================
# CLASES DE ENTIDAD - PRODUCTO Xavier Ruiz Guevara
# ==============================================================================

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

# ==============================================================================
# AUTENTICACION
# ==============================================================================

def autenticar_usuario(p_codigo, p_password):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # 1. Consulta SQL corregida con 'password' y 'sede' apuntando a 'usuarios'
                    sql = """
                        SELECT id, codigo_empleado, nombre, rol, password, sede 
                        FROM usuarios 
                        WHERE codigo_empleado = %s AND activo = 1
                    """
                    cursor.execute(sql, (p_codigo,))
                    usuario = cursor.fetchone()
                    
                    if usuario:
                        # 2. Convertimos a diccionario si el conector devuelve una tupla
                        if not isinstance(usuario, dict):
                            columnas = ['id', 'codigo_empleado', 'nombre', 'rol', 'password', 'sede']
                            usuario = dict(zip(columnas, usuario))
                        
                        # 3. Comparamos contra la columna real 'password' en texto plano
                        if usuario['password'] == p_password:
                            return usuario
        return None
    except Exception as e:
        print("Error en autenticación:", repr(e))
        return None

# ==============================================================================
# CRUD — PRODUCTOS - Xavier Ruiz Guevara 
# ==============================================================================

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


# ==============================================================================
# FUNCION PRIVADA — HISTORIAL
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


# ==============================================================================
# CLASES DE ENTIDAD — SEGMENTACION Y ALERTA
# ==============================================================================

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


# ==============================================================================
# CLASE DE ENTIDAD — CONTEO MANUAL
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

# ==============================================================================
# CRUD — SEGMENTACIONES
# ==============================================================================

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
# ==============================================================================
# ALERTAS
# ==============================================================================

def obtener_alertas_activas():
    try:
        conn = obtenerconexion()
        alertas = []
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql  = " SELECT id, sku, producto, "
                    sql += "        categoria, nivel, unidades, venta_dia, "
                    sql += "        horas_restantes, estado_transf, "
                    sql += "        stock_total, ubicacion_gondola "
                    sql += "   FROM v_alertas_activas "
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

def actualizar_alerta_sincronizada(p_alerta_id, p_unidades, p_venta_dia, p_estado_transf, p_motivo='Ajuste desde edición de alerta'):
    """
    Actualiza una alerta, sincroniza el stock del producto de forma global,
    y registra el cambio en el historial recuperando el stock anterior.
    Garantiza la regla de 3 capas bajo una única transacción atómica.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # 1. Obtener producto_id y el stock actual para la auditoría
                    sql_info = """
                        SELECT a.producto_id, p.stock_total 
                        FROM alertas_quiebre a
                        JOIN productos p ON a.producto_id = p.id
                        WHERE a.id = %s AND a.activo = 1
                    """
                    cursor.execute(sql_info, (p_alerta_id,))
                    row = cursor.fetchone()
                    if not row:
                        return False # Alerta no encontrada
                    
                    producto_id = row['producto_id']
                    stock_anterior = row['stock_total']

                    # 2. Actualizar tabla alertas_quiebre
                    sql_alerta = """
                        UPDATE alertas_quiebre
                           SET unidades = %s, venta_dia = %s, estado_transf = %s, updated_at = NOW()
                         WHERE id = %s
                    """
                    cursor.execute(sql_alerta, (p_unidades, p_venta_dia, p_estado_transf, p_alerta_id))

                    # 3. Sincronizar el stock en la tabla productos
                    sql_producto = """
                        UPDATE productos
                           SET stock_total = %s
                         WHERE id = %s
                    """
                    cursor.execute(sql_producto, (p_unidades, producto_id))

                    # 4. Registrar en Historial usando el mismo cursor abierto (sin duplicar conexiones)
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
# ==============================================================================
# HISTORIAL — FUNCIONES PUBLICAS
# ==============================================================================

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

# ==============================================================================
# FUNCIONES CONTEO
# ==============================================================================
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
    """
    Inserta un nuevo registro en la tabla conteos_manuales.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " INSERT INTO conteos_manuales "
                    sql += " (producto_id, usuario_id, stock_sistema, "
                    sql += "  stock_contado, diferencia, motivo, estado, fecha) "
                    sql += " VALUES (%s, %s, %s, %s, %s, %s, %s, NOW()) "
                    
                    cursor.execute(sql, (
                        p_conteo.producto_id,
                        p_conteo.usuario_id,
                        p_conteo.stock_sistema,
                        p_conteo.stock_contado,
                        p_conteo.diferencia,
                        p_conteo.motivo,
                        p_conteo.estado or 'aplicado'
                    ))
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False


# ==============================================================================
# CONTEOS MANUALES — ESCANER 
# ==============================================================================

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
# UTILIDADES — CONTEO DE ALERTAS (movida desde app.py)
# ==============================================================================

def contar_alertas():
    """
    Retorna el numero de alertas activas de nivel critico o urgente.
    Centralizada aqui para cumplir la regla de 3 capas.
    """
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

# ==============================================================================
# CLASE DE ENTIDAD — TRABAJADOR
# ==============================================================================
class clsTrabajador:
    def __init__(self, p_id=None, p_nombre=None, p_codigo_empleado=None,
                 p_email=None, p_sede=None, p_rol=None,
                 p_palabra_clave=None, p_password=None, p_activo=None):
        self.id = p_id
        self.nombre = p_nombre
        self.codigo_empleado = p_codigo_empleado
        self.email = p_email
        self.sede = p_sede
        self.rol = p_rol
        self.palabra_clave = p_palabra_clave
        self.password = p_password
        self.activo = p_activo

def obtener_sedes_unicas():
    try:
        conn = obtenerconexion()
        lista = []
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = "SELECT DISTINCT sede FROM usuarios WHERE activo = 1 AND sede IS NOT NULL AND sede != '' ORDER BY sede"
                    cursor.execute(sql)
                    resultados = cursor.fetchall() 
                    
                    for r in resultados:
                        if isinstance(r, dict):
                            nombre_sede = r.get('sede')
                        elif isinstance(r, (tuple, list)):
                            nombre_sede = r[0]
                        else:
                            nombre_sede = r
                        
                        if nombre_sede:
                            lista.append({'nombre': nombre_sede.strip()})
        return lista
    except Exception as e:
        print(f"Error en obtener_sedes_unicas: {repr(e)}")
        return []

def obtener_roles_unicos():
    try:
        conn = obtenerconexion()
        lista = []
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = "SELECT DISTINCT rol FROM usuarios WHERE activo = 1 AND rol IS NOT NULL AND rol != '' ORDER BY rol"
                    cursor.execute(sql)
                    resultados = cursor.fetchall()
                    
                    for r in resultados:
                        if isinstance(r, dict):
                            nombre_rol = r.get('rol')
                        elif isinstance(r, (tuple, list)):
                            nombre_rol = r[0]
                        else:
                            nombre_rol = r
                        
                        if nombre_rol:
                            lista.append({'nombre': nombre_rol.strip()})
        return lista
    except Exception as e:
        print(f"Error en obtener_roles_unicos: {repr(e)}")
        return []

# ==============================================================================
# LEER TRABAJADORES
# ==============================================================================
def leer_trabajadores():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = " SELECT id, nombre, codigo_empleado, email, sede, rol, activo FROM usuarios WHERE activo = 1 ORDER BY nombre "
                    cursor.execute(sql)
                    usuarios = cursor.fetchall()
                    
                    lista = []
                    for u in usuarios:
                        if not isinstance(u, dict):
                            columnas = ['id', 'nombre', 'codigo_empleado', 'email', 'sede', 'rol', 'activo']
                            u = dict(zip(columnas, u))
                        lista.append(u)
                    return lista
        return []
    except Exception as e:
        print(f"Error en leer_trabajadores: {repr(e)}")
        return []

def leer_trabajador_por_id(p_id):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = " SELECT id, nombre, codigo_empleado, email, sede, rol, palabra_clave, password, activo FROM usuarios WHERE id = %s "
                    cursor.execute(sql, (p_id,))
                    usuario = cursor.fetchone()
                    
                    if usuario and not isinstance(usuario, dict):
                        columnas = ['id', 'nombre', 'codigo_empleado', 'email', 'sede', 'rol', 'palabra_clave', 'password', 'activo']
                        usuario = dict(zip(columnas, usuario))
                    return usuario
        return None
    except Exception as e:
        print(f"Error en leer_trabajador_por_id: {repr(e)}")
        return None

# ==============================================================================
# INSERTAR TRABAJADOR
# ==============================================================================
def insertar_trabajador(p_trabajador):
    """
    Inserta un nuevo trabajador en la tabla usuarios.
    Columna correcta en la BD: 'password' (no 'password_hash').
    """
    try:
        conn = obtenerconexion()
        if not conn: return False
        
        with conn.cursor() as cursor:
            sql = "INSERT INTO usuarios (nombre, codigo_empleado, email, sede, rol, palabra_clave, password) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            valores = (
                p_trabajador.nombre, 
                p_trabajador.codigo_empleado, 
                p_trabajador.email or '', 
                p_trabajador.sede, 
                p_trabajador.rol, 
                p_trabajador.palabra_clave or '', 
                p_trabajador.password
            )
            
            cursor.execute(sql, valores)
            conn.commit()
        return True
    except Exception as e:
        print(f"--- ERROR DETECTADO EN INSERTAR BD: {str(e)} ---")
        return False
# ==============================================================================
# ACTUALIZAR TRABAJADOR
# ==============================================================================
def actualizar_trabajador(p_trabajador):
    """
    Actualiza los datos de un trabajador existente en la tabla usuarios.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT id FROM usuarios "
                    sql += "  WHERE id = %s "
                    cursor.execute(sql, (p_trabajador.id,))
                    if not cursor.fetchone():
                        return False

                    sql =  " SELECT id FROM usuarios "
                    sql += "  WHERE codigo_empleado = %s AND id != %s "
                    cursor.execute(sql, (p_trabajador.codigo_empleado, p_trabajador.id))
                    if cursor.fetchone():
                        return False 

                    sql  = " UPDATE `usuarios` "
                    sql += "    SET `nombre` = %s, "
                    sql += "        `codigo_empleado` = %s, "
                    sql += "        `email` = %s, "
                    sql += "        `sede` = %s, "
                    sql += "        `rol` = %s, "
                    sql += "        `palabra_clave` = %s "
                    sql += "  WHERE `id` = %s "
                    cursor.execute(sql, (
                        p_trabajador.nombre,
                        p_trabajador.codigo_empleado,
                        p_trabajador.email or '',
                        p_trabajador.sede or 'Chiclayo',
                        p_trabajador.rol or 'operario',
                        p_trabajador.palabra_clave or '',
                        p_trabajador.id,
                    ))

                    if p_trabajador.password:
                        sql  = " UPDATE `usuarios` "
                        sql += "    SET `password` = %s "
                        sql += "  WHERE `id` = %s "
                        cursor.execute(sql, (p_trabajador.password, p_trabajador.id))

                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False

# ==============================================================================
# ELIMINAR TRABAJADOR
# ==============================================================================
def eliminar_trabajador(p_id):
    """
    Desactiva (soft-delete) un trabajador estableciendo activo=0.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT id FROM usuarios "
                    sql += "  WHERE id = %s "
                    cursor.execute(sql, (p_id,))
                    if not cursor.fetchone():
                        return False

                    sql  = " UPDATE `usuarios` "
                    sql += "    SET `activo` = 0 "
                    sql += "  WHERE `id` = %s "
                    cursor.execute(sql, (p_id,))
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False

# ==============================================================================
# CAMBIO DE CONTRASEÑA
# ==============================================================================
def cambiar_contrasena(p_trabajador_id, p_clave_actual, p_nueva_clave):
    """
    Verifica la clave actual por comparación directa en la tabla usuarios.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = " SELECT id, password FROM usuarios WHERE id = %s AND activo = 1 "
                    cursor.execute(sql, (p_trabajador_id,))
                    row = cursor.fetchone()
                    
                    if not row:
                        return False
                    
                    if isinstance(row, dict):
                        password_bd = row.get('password')
                    else:
                        password_bd = row[1] 

                    if password_bd != p_clave_actual:
                        return False 

                    sql  = " UPDATE `usuarios` SET `password` = %s WHERE `id` = %s "
                    cursor.execute(sql, (p_nueva_clave, p_trabajador_id))
                    
                conn.commit()
            return True
        return False
    except Exception as e:
        print(f"Error en cambiar_clave AD: {repr(e)}")
        return False

# ==============================================================================
# RESTABLECER CONTRASEÑA (Desde el Login usando Palabra Clave)
# ==============================================================================
def restablecer_contrasena(p_codigo_empleado, p_palabra_clave, p_nueva_clave):
    """
    Verifica la identidad mediante el codigo de empleado y su palabra clave.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT id, palabra_clave FROM usuarios "
                    sql += "  WHERE codigo_empleado = %s AND activo = 1 "
                    cursor.execute(sql, (p_codigo_empleado,))
                    row = cursor.fetchone()
                    
                    if not row:
                        return False 
                    if row['palabra_clave'] != p_palabra_clave:
                        return False 

                    sql  = " UPDATE `usuarios` "
                    sql += "    SET `password` = %s "
                    sql += "  WHERE `id` = %s "
                    cursor.execute(sql, (p_nueva_clave, row['id']))
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False