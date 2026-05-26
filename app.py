"""
app.py — Tottus SGI · Backend Unificado
"""
import csv
import io
from datetime import datetime
from flask import Flask, render_template, request, Response
from bd import obtenerconexion

app = Flask(__name__)

@app.context_processor
def inject_session():
    return dict(session={
        'nombre': 'Administrador Sistema',
        'rol': 'gerente',
        'codigo_empleado': 'ADMIN-001'
    })

# ── Conexión BD: ver bd.py ───────────────────────────────────

def contar_alertas():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) AS n FROM alertas_quiebre WHERE activo=1 AND nivel IN ('critico','urgente')")
                    row = cursor.fetchone()
                    return row['n'] if row else 0
        return 0
    except:
        return 0

def registrar_historial(conn, producto_id, accion,
                        campo=None, anterior=None, nuevo=None, motivo=None):
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO historial_ajustes
                (producto_id, usuario_id, empleado_nombre, accion,
                 campo_modificado, valor_anterior, valor_nuevo, motivo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (producto_id, 1, 'Sistema',
              accion, campo, str(anterior) if anterior is not None else None,
              str(nuevo) if nuevo is not None else None, motivo))

# ════════════════════════════════════════════════════════════
# RUTAS PÚBLICAS
# ════════════════════════════════════════════════════════════
@app.route('/')
def index():
    return render_template('login.html', error=None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        error = None
        if request.method == 'POST':
            codigo = request.form['codigo_empleado'].strip()
            clave  = request.form['password']

            conn = obtenerconexion()
            usuario = None
            if conn:
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "SELECT * FROM usuarios WHERE codigo_empleado=%s AND password_hash=%s AND activo=1",
                            (codigo, clave)
                        )
                        usuario = cursor.fetchone()

                if usuario:
                    return render_template('dashboard.html',
                                           active_page='dashboard',
                                           alertas_count=contar_alertas(),
                                           stats={'alertas_criticas': 0, 'total_productos': 0},
                                           alertas_recientes=[])
                else:
                    error = 'Código o contraseña incorrectos.'
        return render_template('login.html', error=error)
    except Exception as e:
        return "<p>Excepción superior: " + repr(e) + "</p>"

@app.route('/logout')
def logout():
    return render_template('login.html', error=None)

# ════════════════════════════════════════════════════════════
# RUTAS — VISTAS
# ════════════════════════════════════════════════════════════
@app.route('/dashboard')
def dashboard():
    stats = {'alertas_criticas': 0, 'productos_ok': 0, 'total_productos': 0}
    alertas_recientes = []
    conn = obtenerconexion()
    if conn:
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) AS n FROM alertas_quiebre WHERE activo=1 AND nivel='critico'")
                    stats['alertas_criticas'] = cursor.fetchone()['n']
                    cursor.execute("SELECT COUNT(*) AS n FROM productos WHERE activo=1")
                    stats['total_productos'] = cursor.fetchone()['n']
                    cursor.execute("""
                        SELECT sku, producto, nivel, horas_restantes
                        FROM alertas_quiebre WHERE activo=1 ORDER BY horas_restantes ASC LIMIT 3
                    """)
                    alertas_recientes = cursor.fetchall()
        except Exception:
            pass

    return render_template('dashboard.html',
                           active_page='dashboard',
                           alertas_count=contar_alertas(),
                           stats=stats,
                           alertas_recientes=alertas_recientes)

# ==============================================================================
# UC4 - ALERTAS DE QUIEBRE (Gianella)
# Vista principal para visualizar alertas de stock crítico y urgente.
# ==============================================================================
@app.route('/alertas')
def alertas():
    lista_alertas = []
    totales_por_nivel = {'critico': 0, 'urgente': 0, 'ok': 0}
    conn = obtenerconexion()
    if conn:
        try:
            with conn:
                with conn.cursor() as cursor:
                    # Obtenemos todas las alertas activas con detalles de producto
                    cursor.execute("SELECT * FROM v_alertas_activas")
                    lista_alertas = cursor.fetchall()

                    # Calculamos los totales (cuántas críticas, urgentes, etc.)
                    cursor.execute("""
                        SELECT nivel, COUNT(*) AS n FROM alertas_quiebre
                        WHERE activo=1 GROUP BY nivel
                    """)
                    for fila in cursor.fetchall():
                        totales_por_nivel[fila['nivel']] = fila['n']
        except Exception:
            pass

    return render_template('alertas.html',
                           active_page='alertas',
                           alertas_count=contar_alertas(),
                           alertas=lista_alertas,
                           totales=totales_por_nivel)

# ==============================================================================
# UC6 - SEGMENTAR STOCK
# ==============================================================================

@app.route('/historial')
def historial():
    registros = []
    conn = obtenerconexion()
    if conn:
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM v_historial_completo LIMIT 100")
                    registros = cursor.fetchall()
        except Exception:
            pass

    return render_template('historial.html',
                           active_page='dashboard',
                           alertas_count=contar_alertas(),
                           registros=registros)

@app.route('/perfil')
def perfil():
    usuario = None
    conn = obtenerconexion()
    if conn:
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM usuarios LIMIT 1")
                    usuario = cursor.fetchone()
        except Exception:
            pass

    return render_template('perfil.html',
                           active_page='perfil',
                           alertas_count=contar_alertas(),
                           usuario=usuario)

@app.route('/escanear')
def escanear():
    return render_template('escanear.html',
                           active_page='escanear',
                           alertas_count=contar_alertas())

@app.route('/productos')
def productos():
    try:
        conn = obtenerconexion()
        q = request.args.get('q', '').strip()
        resultado = []
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    if q:
                        cursor.execute("""
                            SELECT * FROM productos 
                            WHERE (nombre LIKE %s OR sku LIKE %s OR categoria LIKE %s) AND activo=1
                            ORDER BY nombre
                        """, (f'%{q}%', f'%{q}%', f'%{q}%'))
                    else:
                        cursor.execute("SELECT * FROM productos WHERE activo=1 ORDER BY nombre")
                    resultado = cursor.fetchall()
        return render_template('productos.html',
                               active_page='productos',
                               alertas_count=contar_alertas(),
                               productos=resultado,
                               edit_prod=None,
                               q_search=q)
    except Exception as e:
        return "<p>Excepción superior: " + repr(e) + "</p>"

@app.route('/productos/editar/<int:prod_id>')
def editar_producto_vista(prod_id):
    try:
        conn = obtenerconexion()
        productos_lista = []
        edit_prod = None
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # Traer todos los productos para la tabla
                    cursor.execute("SELECT * FROM productos WHERE activo=1 ORDER BY nombre")
                    productos_lista = cursor.fetchall()
                    # Traer el producto específico a editar
                    cursor.execute("SELECT * FROM productos WHERE id=%s AND activo=1", (prod_id,))
                    edit_prod = cursor.fetchone()
        return render_template('productos.html',
                               active_page='productos',
                               alertas_count=contar_alertas(),
                               productos=productos_lista,
                               edit_prod=edit_prod)
    except Exception as e:
        return "<p>Excepción superior: " + repr(e) + "</p>"

@app.route('/guardar_producto', methods=['POST'])
def api_crear_producto():
    try:
        sku    = request.form['sku'].strip().upper()
        nombre = request.form['nombre'].strip()
        if not sku or not nombre:
            return "<p>Error: SKU y nombre son obligatorios</p>"

        try:
            stock  = int(request.form.get('stock_total', 0))
            precio = float(request.form.get('precio_unitario', 0))
            venta  = float(request.form.get('venta_dia', 0))
        except ValueError:
            return "<p>Error: Valores numéricos inválidos</p>"

        if stock < 0 or precio < 0 or venta < 0:
            return "<p>Error: El stock, precio y venta diaria no pueden ser negativos</p>"

        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id FROM productos WHERE sku=%s AND activo=1", (sku,))
                    if cursor.fetchone():
                        return f'<p>Error: El SKU "{sku}" ya existe en el catálogo.</p>'

                    cursor.execute("""
                        INSERT INTO productos
                            (sku, nombre, categoria, stock_total, precio_unitario, venta_dia, ubicacion_gondola)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (sku, nombre,
                          request.form.get('categoria', ''),
                          stock, precio, venta,
                          request.form.get('ubicacion_gondola', '')))
                    nuevo_id = cursor.lastrowid
                    registrar_historial(conn, nuevo_id, 'CREATE',
                                        motivo=f'Producto "{nombre}" agregado al catálogo')
                conn.commit()
            return render_template('exito.html', mensaje='Producto registrado correctamente en el catálogo.', volver='/productos')
        return "<p>Error al conectar con la base de datos.</p>"
    except Exception as e:
        return "<p>Excepción superior: " + repr(e) + "</p>"

@app.route('/actualizar_producto', methods=['POST'])
def api_actualizar_producto():
    try:
        prod_id = int(request.form['prod_id'])
        nombre  = request.form['nombre'].strip()
        if not nombre:
            return "<p>Error: Nombre obligatorio</p>"

        try:
            stock  = int(request.form.get('stock_total', 0))
            precio = float(request.form.get('precio_unitario', 0))
            venta  = float(request.form.get('venta_dia', 0))
        except ValueError:
            return "<p>Error: Valores numéricos inválidos</p>"

        if stock < 0 or precio < 0 or venta < 0:
            return "<p>Error: El stock, precio y venta diaria no pueden ser negativos</p>"

        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM productos WHERE id=%s", (prod_id,))
                    anterior = cursor.fetchone()
                    if not anterior:
                        return "<p>Error: Producto no encontrado</p>"

                    nuevo_sku = request.form.get('sku', anterior['sku']).strip().upper()
                    cursor.execute("SELECT id FROM productos WHERE sku=%s AND id!=%s AND activo=1", (nuevo_sku, prod_id))
                    if cursor.fetchone():
                        return f'<p>Error: El SKU "{nuevo_sku}" ya está en uso por otro producto.</p>'

                    nuevo_stock = int(request.form.get('stock_total', anterior['stock_total']))
                    cursor.execute("""
                       UPDATE productos SET
                            sku=%s, nombre=%s, categoria=%s, stock_total=%s,
                            precio_unitario=%s, venta_dia=%s, ubicacion_gondola=%s
                        WHERE id=%s
                    """, (nuevo_sku, nombre,
                          request.form.get('categoria', anterior['categoria']),
                          nuevo_stock,
                          float(request.form.get('precio_unitario', anterior['precio_unitario'] or 0)),
                          float(request.form.get('venta_dia', anterior['venta_dia'] or 0)),
                          request.form.get('ubicacion_gondola', anterior['ubicacion_gondola'] or ''),
                          prod_id))
                    if nuevo_stock != anterior['stock_total']:
                        registrar_historial(conn, prod_id, 'UPDATE',
                                            'stock_total', anterior['stock_total'], nuevo_stock,
                                            'Edición desde catálogo')
                conn.commit()
            return render_template('exito.html', mensaje='Producto actualizado correctamente.', volver='/productos')
        return "<p>Error al conectar con la base de datos.</p>"
    except Exception as e:
        return "<p>Excepción superior: " + repr(e) + "</p>"

@app.route('/eliminar_producto/<int:prod_id>')
def api_eliminar_producto(prod_id):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT nombre FROM productos WHERE id=%s", (prod_id,))
                    row = cursor.fetchone()
                    if not row:
                        return "<p>Error: Producto no encontrado</p>"
                    cursor.execute("UPDATE productos SET activo=0 WHERE id=%s", (prod_id,))
                    cursor.execute("UPDATE alertas_quiebre SET activo=0 WHERE producto_id=%s", (prod_id,))
                    cursor.execute("UPDATE segmentacion_inventario SET activo=0 WHERE producto_id=%s", (prod_id,))
                    registrar_historial(conn, prod_id, 'DELETE',
                                        motivo='Producto desactivado')
                conn.commit()
            return render_template('exito.html', mensaje='Producto desactivado del catálogo correctamente.', volver='/productos')
        return "<p>Error al conectar con la base de datos.</p>"
    except Exception as e:
        return "<p>Excepción superior: " + repr(e) + "</p>"


@app.route('/api/productos/buscar-sku/<sku>', methods=['GET'])
def api_buscar_sku(sku):
    try:
        conn = obtenerconexion()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT p.*,
                           a.nivel AS alerta_nivel,
                           a.horas_restantes,
                           a.estado_transf
                    FROM productos p
                    LEFT JOIN alertas_quiebre a
                        ON a.producto_id = p.id AND a.activo = 1
                    WHERE p.sku = %s AND p.activo = 1
                    LIMIT 1
                """, (sku.upper(),))
                prod = cursor.fetchone()
        if not prod:
            return "<p>Error: SKU no encontrado</p>", 404
        import json
        return Response(json.dumps({'success': True, 'data': prod}, default=str),
                        mimetype='application/json')
    except Exception as e:
        return "<p>Excepción: " + repr(e) + "</p>", 500


# ════════════════════════════════════════════════════════════
# API — CONTEOS MANUALES  (desde el escáner)
# ════════════════════════════════════════════════════════════
@app.route('/api/conteos', methods=['POST'])
def api_crear_conteo():
    try:
        data       = request.get_json() or {}
        prod_id    = data.get('producto_id')
        contado    = data.get('stock_contado')
        motivo     = data.get('motivo', '')

        if prod_id is None or contado is None:
            return "<p>Error: producto_id y stock_contado son requeridos</p>", 400

        conn = obtenerconexion()

        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT stock_total FROM productos WHERE id=%s AND activo=1", (prod_id,))
                prod = cursor.fetchone()
                if not prod:
                    return "<p>Error: Producto no encontrado</p>", 404

                stock_sistema = prod['stock_total']
                cursor.execute("""
                    INSERT INTO conteos_manuales
                        (producto_id, usuario_id, stock_sistema, stock_contado, motivo, estado)
                    VALUES (%s, %s, %s, %s, %s, 'aplicado')
                """, (prod_id, 1, stock_sistema, int(contado), motivo))

                # Actualizar stock_total del producto con el valor contado
                cursor.execute("UPDATE productos SET stock_total=%s WHERE id=%s", (int(contado), prod_id))

                registrar_historial(conn, prod_id, 'CONTEO',
                                    'stock_total', stock_sistema, contado,
                                    motivo or 'Conteo manual desde escáner')
            conn.commit()
        import json
        return Response(json.dumps({'success': True, 'message': 'Conteo registrado'}),
                        mimetype='application/json')
    except Exception as e:
        return "<p>Excepción: " + repr(e) + "</p>", 500

# ════════════════════════════════════════════════════════════
# API — SEGMENTACIONES  (CRUD completo)
# ════════════════════════════════════════════════════════════
@app.route('/segmentacion')
def segmentacion():
    try:
        conn = obtenerconexion()
        productos = []
        segmentaciones = []
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # Productos para el select
                    cursor.execute("SELECT * FROM productos WHERE activo=1 ORDER BY nombre")
                    productos = cursor.fetchall()
                    # Segmentaciones activas
                    cursor.execute("""
                        SELECT s.*, p.nombre, p.sku, p.stock_total
                        FROM segmentacion_inventario s
                        JOIN productos p ON s.producto_id = p.id
                        ORDER BY s.fecha_creacion DESC
                    """)
                    segmentaciones = cursor.fetchall()
        return render_template('segmentacion.html',
                               active_page='productos',
                               alertas_count=contar_alertas(),
                               productos=productos,
                               segmentaciones=segmentaciones,
                               edit_seg=None)
    except Exception as e:
        return "<p>Excepción superior: " + repr(e) + "</p>"

@app.route('/segmentacion/editar/<int:seg_id>')
def editar_segmentacion_vista(seg_id):
    try:
        conn = obtenerconexion()
        productos = []
        segmentaciones = []
        edit_seg = None
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # Productos para el select
                    cursor.execute("SELECT * FROM productos WHERE activo=1 ORDER BY nombre")
                    productos = cursor.fetchall()
                    # Segmentaciones activas
                    cursor.execute("""
                        SELECT s.*, p.nombre, p.sku, p.stock_total
                        FROM segmentacion_inventario s
                        JOIN productos p ON s.producto_id = p.id
                        ORDER BY s.fecha_creacion DESC
                    """)
                    segmentaciones = cursor.fetchall()
                    # Segmentación específica
                    cursor.execute("""
                        SELECT s.*, p.nombre, p.sku, p.stock_total
                        FROM segmentacion_inventario s
                        JOIN productos p ON s.producto_id = p.id
                        WHERE s.id=%s
                    """, (seg_id,))
                    edit_seg = cursor.fetchone()
        return render_template('segmentacion.html',
                               active_page='productos',
                               alertas_count=contar_alertas(),
                               productos=productos,
                               segmentaciones=segmentaciones,
                               edit_seg=edit_seg)
    except Exception as e:
        return "<p>Excepción superior: " + repr(e) + "</p>"

@app.route('/guardar_segmentacion', methods=['POST'])
def api_crear_segmentacion():
    try:
        conn = obtenerconexion()
        producto_id      = int(request.form['producto_id'])
        stock_final      = int(request.form.get('stock_cliente_final', 0))
        stock_revendedor = int(request.form.get('stock_revendedor', 0))
        limite_final     = int(request.form.get('limite_compra_final', 0))
        limite_revend    = int(request.form.get('limite_compra_revendedor', 0))
        motivo           = request.form.get('motivo', '')

        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # Validación: no superar stock total
                    cursor.execute("SELECT stock_total FROM productos WHERE id=%s AND activo=1", (producto_id,))
                    prod = cursor.fetchone()
                    if not prod:
                        return "<p>Error: Producto no encontrado</p>"
                    if stock_final + stock_revendedor > prod['stock_total']:
                        return (f"<p>Error: Total asignado ({stock_final + stock_revendedor}) "
                                f"supera el stock disponible ({prod['stock_total']})</p>")

                    cursor.execute("""
                        INSERT INTO segmentacion_inventario
                            (producto_id, usuario_id, stock_cliente_final, stock_revendedor,
                             limite_compra_final, limite_compra_revendedor, motivo)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (producto_id, 1,
                          stock_final, stock_revendedor,
                          limite_final, limite_revend, motivo))
                    registrar_historial(conn, producto_id, 'CREATE', motivo=motivo)
                conn.commit()
            return render_template('exito.html', mensaje='Ajuste de segmentación registrado con éxito.', volver='/segmentacion')
        return "<p>Error al conectar con la base de datos.</p>"
    except Exception as e:
        return "<p>Excepción superior: " + repr(e) + "</p>"

@app.route('/actualizar_segmentacion', methods=['POST'])
def api_actualizar_segmentacion():
    try:
        seg_id           = int(request.form['seg_id'])
        stock_final      = int(request.form.get('stock_cliente_final', 0))
        stock_revendedor = int(request.form.get('stock_revendedor', 0))
        limite_final     = int(request.form.get('limite_compra_final', 0))
        limite_revend    = int(request.form.get('limite_compra_revendedor', 0))
        motivo           = request.form.get('motivo', '')

        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # Obtener datos anteriores para historial
                    cursor.execute("""
                        SELECT s.*, p.stock_total FROM segmentacion_inventario s
                        JOIN productos p ON s.producto_id = p.id WHERE s.id=%s
                    """, (seg_id,))
                    anterior = cursor.fetchone()
                    if not anterior:
                        return "<p>Error: Registro no encontrado</p>"

                    if stock_final + stock_revendedor > anterior['stock_total']:
                        return (f"<p>Error: Total ({stock_final + stock_revendedor}) "
                                f"supera stock ({anterior['stock_total']})</p>")

                    cursor.execute("""
                        UPDATE segmentacion_inventario
                        SET stock_cliente_final=%s, stock_revendedor=%s,
                            limite_compra_final=%s, limite_compra_revendedor=%s,
                            motivo=%s, usuario_id=%s, updated_at=NOW()
                        WHERE id=%s
                    """, (stock_final, stock_revendedor,
                          limite_final, limite_revend,
                          motivo, 1, seg_id))

                    registrar_historial(conn, anterior['producto_id'], 'UPDATE',
                                        'stock_cliente_final',
                                        anterior['stock_cliente_final'], stock_final, motivo)
                conn.commit()
            return render_template('exito.html', mensaje='Ajuste de segmentación actualizado correctamente.', volver='/segmentacion')
        return "<p>Error al conectar con la base de datos.</p>"
    except Exception as e:
        return "<p>Excepción superior: " + repr(e) + "</p>"

@app.route('/eliminar_segmentacion/<int:seg_id>')
def api_eliminar_segmentacion(seg_id):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT producto_id FROM segmentacion_inventario WHERE id=%s", (seg_id,))
                    row = cursor.fetchone()
                    if not row:
                        return "<p>Error: No encontrado</p>"
                    registrar_historial(conn, row['producto_id'], 'DELETE',
                                        motivo='Segmentación eliminada')
                    cursor.execute("DELETE FROM segmentacion_inventario WHERE id=%s", (seg_id,))
                conn.commit()
            return render_template('exito.html', mensaje='Ajuste de segmentación eliminado.', volver='/segmentacion')
        return "<p>Error al conectar con la base de datos.</p>"
    except Exception as e:
        return "<p>Excepción superior: " + repr(e) + "</p>"

@app.route('/toggle_segmentacion/<int:seg_id>')
def api_toggle_segmentacion(seg_id):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT producto_id, activo FROM segmentacion_inventario WHERE id=%s", (seg_id,))
                    row = cursor.fetchone()
                    if not row:
                        return "<p>Error: No encontrado</p>"
                    nuevo_estado = 0 if row['activo'] else 1
                    cursor.execute("UPDATE segmentacion_inventario SET activo=%s WHERE id=%s", (nuevo_estado, seg_id))
                    registrar_historial(conn, row['producto_id'], 'TOGGLE',
                                        'activo', row['activo'], nuevo_estado)
                conn.commit()
            return render_template('exito.html', mensaje='Estado de segmentación modificado con éxito.', volver='/segmentacion')
        return "<p>Error al conectar con la base de datos.</p>"
    except Exception as e:
        return "<p>Excepción superior: " + repr(e) + "</p>"

# ════════════════════════════════════════════════════════════
# API — ALERTAS
# ════════════════════════════════════════════════════════════
@app.route('/listar_alertas')
def api_get_alertas():
    try:
        conn = obtenerconexion()
        resultado = None
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM v_alertas_activas")
                    resultado = cursor.fetchall()
        return render_template('lista_alertas.html', datos=resultado)
    except Exception as e:
        return "<p>Excepción superior: " + repr(e) + "</p>"

@app.route('/eliminar_alerta/<int:alerta_id>')
def api_eliminar_alerta(alerta_id):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT producto_id FROM alertas_quiebre WHERE id=%s", (alerta_id,))
                    row = cursor.fetchone()
                    if not row:
                        return "<p>Error: No encontrado</p>"
                    cursor.execute("UPDATE alertas_quiebre SET activo=0 WHERE id=%s", (alerta_id,))
                    registrar_historial(conn, row['producto_id'], 'DELETE',
                                        motivo='Alerta descartada manualmente')
                conn.commit()
            return render_template('exito.html')
        return "<p>Error al eliminar alerta</p>"
    except Exception as e:
        return "<p>Excepción superior: " + repr(e) + "</p>"

# ════════════════════════════════════════════════════════════
# API — HISTORIAL
# ════════════════════════════════════════════════════════════
@app.route('/listar_historial')
def api_get_historial():
    try:
        conn = obtenerconexion()
        resultado = None
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM v_historial_completo LIMIT 200")
                    resultado = cursor.fetchall()
            # Convertir datetime a string
            if resultado:
                for row in resultado:
                    if isinstance(row.get('fecha'), datetime):
                        row['fecha'] = row['fecha'].strftime('%d/%m/%Y %H:%M')
        return render_template('lista_historial.html', datos=resultado)
    except Exception as e:
        return "<p>Excepción superior: " + repr(e) + "</p>"


# ════════════════════════════════════════════════════════════
# FASE 3 — Cambio de contraseña desde Perfil
# ════════════════════════════════════════════════════════════
@app.route('/cambiar_clave', methods=['POST'])
def api_cambiar_clave():
    try:
        clave_actual = request.form['clave_actual']
        clave_nueva  = request.form['clave_nueva']

        # Validaciones backend
        if not clave_actual or not clave_nueva:
            return "<p>Error: Ambas claves son requeridas</p>"
        if len(clave_nueva) < 8:
            return "<p>Error: La nueva clave debe tener al menos 8 caracteres</p>"
        if not any(c.isdigit() for c in clave_nueva):
            return "<p>Error: La nueva clave debe contener al menos un número</p>"
        if clave_actual == clave_nueva:
            return "<p>Error: La nueva clave debe ser diferente a la actual</p>"

        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT password_hash FROM usuarios WHERE id=%s AND activo=1", (1,))
                    usuario = cursor.fetchone()

                    if not usuario:
                        return "<p>Error: Usuario no encontrado</p>"

                    # Verificar clave actual
                    if not (usuario['password_hash'] == clave_actual):
                        return "<p>Error: La contraseña actual es incorrecta</p>"

                    # Guardar nueva clave
                    cursor.execute("UPDATE usuarios SET password_hash=%s WHERE id=%s",
                                   (clave_nueva, 1))
                conn.commit()
            return render_template('exito.html')
        return "<p>Error de conexión</p>"
    except Exception as e:
        return "<p>Excepción superior: " + repr(e) + "</p>"


# ════════════════════════════════════════════════════════════
# FASE 4 — Exportación CSV del historial
# ════════════════════════════════════════════════════════════
@app.route('/historial/exportar', methods=['GET'])
def exportar_historial_csv():
    try:
        conn = obtenerconexion()

        with conn:
            with conn.cursor() as cursor:
                accion = request.args.get('accion', '').strip().upper()
                if accion:
                    cursor.execute(
                        "SELECT * FROM v_historial_completo WHERE accion=%s ORDER BY fecha DESC LIMIT 1000",
                        (accion,)
                    )
                else:
                    cursor.execute("SELECT * FROM v_historial_completo ORDER BY fecha DESC LIMIT 1000")
                registros = cursor.fetchall()

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)

        writer.writerow([
            'Fecha', 'Producto', 'SKU', 'Empleado', 'Rol Empleado',
            'Accion', 'Campo Modificado', 'Valor Anterior', 'Valor Nuevo', 'Motivo'
        ])

        for r in registros:
            fecha = r['fecha'].strftime('%d/%m/%Y %H:%M') if isinstance(r.get('fecha'), datetime) else str(r.get('fecha', ''))
            writer.writerow([
                fecha,
                r.get('producto_nombre', ''),
                r.get('sku', ''),
                r.get('empleado_nombre', ''),
                r.get('empleado_rol', ''),
                r.get('accion', ''),
                r.get('campo_modificado', ''),
                r.get('valor_anterior', ''),
                r.get('valor_nuevo', ''),
                r.get('motivo', ''),
            ])

        nombre_archivo = f"historial_tottus_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

        return Response(
            output.getvalue(),
            mimetype='text/csv; charset=utf-8',
            headers={
                'Content-Disposition': f'attachment; filename="{nombre_archivo}"',
                'Content-Type': 'text/csv; charset=utf-8',
            }
        )
    except Exception as e:
        return "<p>Excepción: " + repr(e) + "</p>", 500


# ════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(debug=True, port=5000)