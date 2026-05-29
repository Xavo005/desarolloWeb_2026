"""
app.py — Tottus SGI · Controlador (Capa de Presentacion)
Solo rutas Flask + validacion de formularios + render_template.
Toda la logica de datos vive en tottusAD.py.
"""
import csv
import io
import json
from datetime import datetime
from flask import Flask, render_template, request, Response
from markupsafe import escape
from bd import obtenerconexion

from tottusAD import (
    obtener_stats_dashboard, obtener_alertas_recientes,
    leer_historial, registrar_historial,
    autenticar_usuario,
    clsProducto, leer_productos, leer_producto_por_id,
    insertar_producto, actualizar_producto, eliminar_producto,
    buscar_sku,
    clsSegmentacion, obtener_segmentaciones, obtener_segmentacion_xID, insertar_segmentacion, actualizar_segmentacion, eliminar_segmentacion, toggle_segmentacion,
    clsAlerta, obtener_alertas_activas, obtener_totales_alertas, eliminar_alerta, actualizar_alerta,
    clsTrabajador, leer_trabajadores, leer_trabajador_por_id,
    insertar_trabajador  as ad_insertar_trabajador,
    actualizar_trabajador as ad_actualizar_trabajador,
    eliminar_trabajador  as ad_eliminar_trabajador,
)

app = Flask(__name__)


# ════════════════════════════════════════════════════════════
# CONTEXT PROCESSOR — Variables globales para templates
# ════════════════════════════════════════════════════════════
@app.context_processor
def inject_session():
    return dict(session={
        'nombre': 'Administrador Sistema',
        'rol': 'gerente',
        'codigo_empleado': 'ADMIN-001'
    })


# ════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES CENTRALIZADAS
# ════════════════════════════════════════════════════════════
def mostrar_exito(mensaje, volver='/dashboard', primary_label='Volver a la seccion'):
    """Renderiza la plantilla de exito con mensaje y boton de retorno."""
    return render_template('exito.html',
                           mensaje=mensaje,
                           volver=volver,
                           primary_label=primary_label)


def mostrar_error(mensaje, status=400):
    """Renderiza la plantilla de error con mensaje y codigo HTTP."""
    return render_template('error400.html',
                           mensaje=mensaje,
                           status=status), status


# ════════════════════════════════════════════════════════════
# RUTAS PUBLICAS — Login / Logout
# ════════════════════════════════════════════════════════════
@app.route('/')
def index():
    return render_template('login.html', error=None)


@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        error = None
        if request.method == 'POST':
            codigo = request.form.get('codigo_empleado', '').strip()
            clave  = request.form.get('password', '')

            usuario = autenticar_usuario(codigo, clave)

            if usuario:
                return render_template('dashboard.html',
                                       active_page='dashboard',
                                       alertas_count=contar_alertas(),
                                       stats=obtener_stats_dashboard(),
                                       alertas_recientes=obtener_alertas_recientes())
            else:
                error = 'Codigo o contrasena incorrectos.'
        return render_template('login.html', error=error)
    except Exception as e:
        print("Error en /login:", repr(e))
        return mostrar_error("Error interno al intentar iniciar sesion.", 500)


@app.route('/logout')
def logout():
    return render_template('login.html', error=None)


# ════════════════════════════════════════════════════════════
# RUTAS — VISTAS PRINCIPALES
# ════════════════════════════════════════════════════════════
@app.route('/dashboard')
def dashboard():
    try:
        stats = obtener_stats_dashboard()
        alertas_recientes = obtener_alertas_recientes()
        totales = obtener_totales_alertas()
        alertas_count = totales.get('critico', 0) + totales.get('urgente', 0)
        
        return render_template('dashboard.html',
                               active_page='dashboard',
                               nombre="Administrador Sistema",
                               sede="Chiclayo - Open Plaza",
                               alertas_count=alertas_count,
                               stats=stats,
                               alertas_recientes=alertas_recientes)
    except Exception as e:
        return render_template('error_500.html'), 500
# ==============================================================================
# UC4 - ALERTAS DE QUIEBRE (Gianella)
# ==============================================================================
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
    
def _obtener_datos_alertas(modo='estatico'):
    if modo == 'dinamico':
        conn = obtenerconexion()
        # Traer alertas activas con stock_total y venta_dia estático
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT a.id, a.producto_id, a.producto, a.sku, a.categoria, 
                           p.stock_total AS unidades, p.venta_dia, a.estado_transf
                    FROM alertas_quiebre a
                    JOIN productos p ON a.producto_id = p.id
                    WHERE a.activo = 1
                """)
                alertas_raw = cursor.fetchall()
                
                lista_alertas = []
                total_critico = 0
                total_urgente = 0
                total_ok = 0
                
                for a in alertas_raw:
                    pred = calcular_prediccion_dinamica(
                        conn, 
                        a['producto_id'], 
                        a['unidades'], 
                        a['venta_dia']
                    )
                    
                    item = {
                        'id': a['id'],
                        'producto_id': a['producto_id'],
                        'producto': a['producto'],
                        'sku': a['sku'],
                        'categoria': a['categoria'],
                        'unidades': a['unidades'],
                        'venta_dia': pred['venta_dia_real'],
                        'horas_restantes': pred['horas_restantes_real'],
                        'nivel': pred['nivel_real'],
                        'estado_transf': a['estado_transf']
                    }
                    
                    if item['nivel'] == 'critico': total_critico += 1
                    elif item['nivel'] == 'urgente': total_urgente += 1
                    else: total_ok += 1
                    
                    lista_alertas.append(item)
                
                # Ordenar por horas restantes
                lista_alertas.sort(key=lambda x: x['horas_restantes'])
                
                totales = {
                    'critico': total_critico,
                    'urgente': total_urgente,
                    'ok': total_ok
                }
    else:
        lista_alertas = obtener_alertas_activas()
        totales = obtener_totales_alertas()

    alertas_count = totales.get('critico', 0) + totales.get('urgente', 0)
    
    return {
        'alertas': lista_alertas,
        'totales': totales,
        'alertas_count': alertas_count,
        'modo': modo,
        'active_page': 'alertas'
    }

@app.route('/alertas')
def alertas():
    try:
        modo = request.args.get('modo', 'estatico')
        datos = _obtener_datos_alertas(modo)
        return render_template('alertas.html', **datos)
    except Exception as e:
        return render_template('error_500.html'), 500

@app.route('/alertas/actualizar', methods=['POST'])
def actualizar_alerta_tradicional():
    try:
        alerta_id = int(request.form['id'])
        unidades = int(request.form['unidades'])
        venta_dia = float(request.form['venta_dia'])
        estado_transf = request.form['estado_transf'].strip()
        
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    # Actualizar la alerta
                    cursor.execute("""
                        UPDATE alertas_quiebre 
                        SET unidades=%s, venta_dia=%s, estado_transf=%s, updated_at=NOW()
                        WHERE id=%s
                    """, (unidades, venta_dia, estado_transf, alerta_id))
                    
                    # Opcionalmente registrar en historial (según lógica previa)
                    cursor.execute("SELECT producto_id FROM alertas_quiebre WHERE id=%s", (alerta_id,))
                    row = cursor.fetchone()
                    if row and row['producto_id']:
                        registrar_historial(row['producto_id'], 'UPDATE', 'alert_edit', 
                                            None, None, f'Edición tradicional de alerta {alerta_id}')
                conn.commit()
        
        # Volver a renderizar la página de alertas (sin redirect)
        datos = _obtener_datos_alertas()
        return render_template('alertas.html', **datos)
    except Exception as e:
        return render_template('error_500.html'), 500

@app.route('/eliminar_alerta/<int:alerta_id>')
def eliminar_alerta_ruta(alerta_id):
    try:
        if eliminar_alerta(alerta_id):
            datos = _obtener_datos_alertas()
            return render_template('alertas.html', **datos)
        else:
            return render_template('error_500.html'), 500
    except Exception as e:
        return render_template('error_500.html'), 500

# ==============================================================================
# HISTORIAL
# ==============================================================================
@app.route('/historial')
def historial():
    registros = []
    try:
        resultado = leer_historial(p_limite=100)
        if resultado:
            registros = resultado
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


# ════════════════════════════════════════════════════════════
# CRUD — PRODUCTOS - Xavier Ruiz Guevara
# ════════════════════════════════════════════════════════════
@app.route('/productos')
def productos():
    try:
        q = request.args.get('q', '').strip()
        resultado = leer_productos(p_busqueda=q if q else None)
        return render_template('productos.html',
                               active_page='productos',
                               alertas_count=contar_alertas(),
                               productos=resultado or [],
                               edit_prod=None,
                               q_search=q)
    except Exception as e:
        print("Error en /productos:", repr(e))
        return mostrar_error("Error al cargar el catalogo de productos.", 500)


@app.route('/productos/editar/<int:prod_id>')
def editar_producto_vista(prod_id):
    try:
        productos_lista = leer_productos() or []
        edit_prod = leer_producto_por_id(prod_id)
        return render_template('productos.html',
                               active_page='productos',
                               alertas_count=contar_alertas(),
                               productos=productos_lista,
                               edit_prod=edit_prod)
    except Exception as e:
        print("Error en /productos/editar:", repr(e))
        return mostrar_error("Error al cargar el producto para edicion.", 500)


@app.route('/guardar_producto', methods=['POST'])
def guardar_producto():
    sku    = request.form.get('sku', '').strip().upper()
    nombre = request.form.get('nombre', '').strip()
    
    if not sku or not nombre:
        return "<h1>Error</h1><p>El SKU y el nombre son obligatorios.</p><a href='/productos'>Volver</a>"

    try:
        stock  = int(request.form.get('stock_total', 0))
        precio = float(request.form.get('precio_unitario', 0))
        venta  = float(request.form.get('venta_dia', 0))
    except ValueError:
        return "<h1>Error</h1><p>Los valores numéricos no son válidos.</p><a href='/productos'>Volver</a>"

    obj = clsProducto(
        p_id=None,
        p_sku=sku,
        p_nombre=nombre,
        p_categoria=request.form.get('categoria', ''),
        p_stock_total=stock,
        p_precio_unitario=precio,
        p_venta_dia=venta,
        p_ubicacion_gondola=request.form.get('ubicacion_gondola', '')
    )

    if insertar_producto(obj):
        return redirect(url_for('listar_productos'))
    else:
        return "<h1>Error</h1><p>No se pudo guardar el producto. Verifique el SKU.</p><a href='/productos'>Volver</a>"


@app.route('/actualizar_producto', methods=['POST'])
def actualizar_producto_ruta():
    try:
        prod_id = int(request.form.get('prod_id', 0))
        nombre  = request.form.get('nombre', '').strip()
        if not nombre:
            return mostrar_error("El nombre del producto es obligatorio.")

        try:
            stock  = int(request.form.get('stock_total', 0))
            precio = float(request.form.get('precio_unitario', 0))
            venta  = float(request.form.get('venta_dia', 0))
        except ValueError:
            return mostrar_error("Valores numericos invalidos.")

        if stock < 0 or precio < 0 or venta < 0:
            return mostrar_error("El stock, precio y venta diaria no pueden ser negativos.")

        obj = clsProducto(
            p_id=prod_id,
            p_sku=request.form.get('sku', '').strip().upper(),
            p_nombre=nombre,
            p_categoria=request.form.get('categoria', ''),
            p_stock_total=stock,
            p_precio_unitario=precio,
            p_venta_dia=venta,
            p_ubicacion_gondola=request.form.get('ubicacion_gondola', '')
        )

        if actualizar_producto(obj):
            return mostrar_exito(
                'Producto actualizado correctamente.',
                '/productos', 'Ver catalogo')
        return mostrar_error("No se pudo actualizar. Verifique que el SKU no este duplicado.")
    except Exception as e:
        print("Error en /actualizar_producto:", repr(e))
        return mostrar_error("Error interno al actualizar el producto.", 500)


@app.route('/eliminar_producto/<int:prod_id>', methods=['POST'])
def eliminar_producto_ruta(prod_id):
    try:
        if eliminar_producto(prod_id):
            return mostrar_exito(
                'Producto desactivado del catalogo correctamente.',
                '/productos', 'Ver catalogo')
        return mostrar_error("Producto no encontrado o no se pudo desactivar.")
    except Exception as e:
        print("Error en /eliminar_producto:", repr(e))
        return mostrar_error("Error interno al desactivar el producto.", 500)


# ════════════════════════════════════════════════════════════
# API — ESCANER  (Excepcion aprobada: respuestas JSON)
# ════════════════════════════════════════════════════════════
@app.route('/api/productos/buscar-sku/<sku>', methods=['GET'])
def api_buscar_sku(sku):
    try:
        prod = buscar_sku(sku)
        if not prod:
            return Response(
                json.dumps({'success': False, 'message': 'SKU no encontrado'}),
                mimetype='application/json', status=404)
        return Response(
            json.dumps({'success': True, 'data': prod}, default=str),
            mimetype='application/json')
    except Exception as e:
        print("Error en /api/buscar-sku:", repr(e))
        return Response(
            json.dumps({'success': False, 'message': repr(e)}),
            mimetype='application/json', status=500)


# ════════════════════════════════════════════════════════════
# API — CONTEOS MANUALES  (Excepcion aprobada: escaner)
# ════════════════════════════════════════════════════════════
@app.route('/api/conteos', methods=['POST'])
def api_crear_conteo():
    try:
        data    = request.get_json() or {}
        prod_id = data.get('producto_id')
        contado = data.get('stock_contado')
        motivo  = data.get('motivo', '')

        if prod_id is None or contado is None:
            return Response(
                json.dumps({'success': False, 'message': 'producto_id y stock_contado son requeridos'}),
                mimetype='application/json', status=400)

        conn = obtenerconexion()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT stock_total FROM productos WHERE id=%s AND activo=1", (prod_id,))
                prod = cursor.fetchone()
                if not prod:
                    return Response(
                        json.dumps({'success': False, 'message': 'Producto no encontrado'}),
                        mimetype='application/json', status=404)

                stock_sistema = prod['stock_total']
                cursor.execute("""
                    INSERT INTO conteos_manuales
                        (producto_id, usuario_id, stock_sistema, stock_contado, motivo, estado)
                    VALUES (%s, %s, %s, %s, %s, 'aplicado')
                """, (prod_id, 1, stock_sistema, int(contado), motivo))

                cursor.execute("UPDATE productos SET stock_total=%s WHERE id=%s",
                               (int(contado), prod_id))

                registrar_historial(prod_id, 'CONTEO',
                                    p_campo='stock_total',
                                    p_anterior=stock_sistema,
                                    p_nuevo=contado,
                                    p_motivo=motivo or 'Conteo manual desde escaner')
            conn.commit()
        return Response(
            json.dumps({'success': True, 'message': 'Conteo registrado'}),
            mimetype='application/json')
    except Exception as e:
        print("Error en /api/conteos:", repr(e))
        return Response(
            json.dumps({'success': False, 'message': repr(e)}),
            mimetype='application/json', status=500)


# ════════════════════════════════════════════════════════════
# CRUD — SEGMENTACIONES
# ════════════════════════════════════════════════════════════
def _obtener_datos_segmentacion():
    segmentaciones = obtener_segmentaciones()
    conn = obtenerconexion()
    productos = []
    if conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM productos WHERE activo=1 ORDER BY nombre")
                productos = cursor.fetchall()
    totales = obtener_totales_alertas()
    alertas_count = totales.get('critico', 0) + totales.get('urgente', 0)
    return {
        'segmentaciones': segmentaciones,
        'productos': productos,
        'alertas_count': alertas_count,
        'active_page': 'productos'
    }

@app.route('/segmentacion')
def segmentacion():
    try:
        datos = _obtener_datos_segmentacion()
        return render_template('segmentacion.html', edit_seg=None, **datos)
    except Exception as e:
        return render_template('error_500.html'), 500

@app.route('/segmentacion/editar/<int:seg_id>')
def editar_segmentacion_vista(seg_id):
    try:
        edit_seg = obtener_segmentacion_xID(seg_id)
        datos = _obtener_datos_segmentacion()
        return render_template('segmentacion.html', edit_seg=edit_seg, **datos)
    except Exception as e:
        return render_template('error_500.html'), 500

@app.route('/guardar_segmentacion', methods=['POST'])
def guardar_segmentacion_ruta():
    try:
        producto_id      = int(request.form['producto_id'])
        stock_final      = int(request.form.get('stock_cliente_final', 0))
        stock_revendedor = int(request.form.get('stock_revendedor', 0))
        motivo           = request.form.get('motivo', '')

        # Validación de stock
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT stock_total FROM productos WHERE id=%s AND activo=1", (producto_id,))
                    prod = cursor.fetchone()
                    if not prod:
                        return mostrar_error("Producto no encontrado o inactivo.")
                    
                    if (stock_final + stock_revendedor > prod['stock_total']):
                        return mostrar_error(f"Stock insuficiente. Disponible: {prod['stock_total']}, Solicitado: {stock_final + stock_revendedor}")

        # Insertar segmentación
        objSegmentacion = clsSegmentacion(
            producto_id=producto_id,
            stock_cliente_final=stock_final,
            stock_revendedor=stock_revendedor,
            limite_compra_final=int(request.form.get('limite_compra_final', 0)),
            limite_compra_revendedor=int(request.form.get('limite_compra_revendedor', 0)),
            motivo=motivo
        )

        if insertar_segmentacion(objSegmentacion):
            # El historial se registra con su propia conexión interna
            registrar_historial(producto_id, 'CREATE', p_motivo=motivo)
            return mostrar_exito('Segmentación creada correctamente.', '/segmentacion')
        else:
            return mostrar_error("No se pudo guardar la segmentación.")
    except Exception as e:
        print(f"Error en guardar_segmentacion: {e}")
        return mostrar_error("Error interno al procesar la segmentación.", 500)

@app.route('/actualizar_segmentacion', methods=['POST'])
def actualizar_segmentacion_ruta():
    try:
        seg_id           = int(request.form['seg_id'])
        stock_final      = int(request.form.get('stock_cliente_final', 0))
        stock_revendedor = int(request.form.get('stock_revendedor', 0))
        motivo           = request.form.get('motivo', '')

        anterior = None
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
                        return mostrar_error("Segmentación no encontrada.")
                    
                    if (stock_final + stock_revendedor > anterior['stock_total']):
                        return mostrar_error(f"Stock insuficiente. Disponible: {anterior['stock_total']}, Solicitado: {stock_final + stock_revendedor}")

        objSegmentacion = clsSegmentacion(
            id=seg_id,
            stock_cliente_final=stock_final,
            stock_revendedor=stock_revendedor,
            limite_compra_final=int(request.form.get('limite_compra_final', 0)),
            limite_compra_revendedor=int(request.form.get('limite_compra_revendedor', 0)),
            motivo=motivo
        )

        if actualizar_segmentacion(objSegmentacion):
            if anterior:
                # Registrar cambio en el historial
                registrar_historial(
                    p_producto_id=anterior['producto_id'], 
                    p_accion='UPDATE',
                    p_campo='segmentacion_stock',
                    p_anterior=f"F:{anterior['stock_cliente_final']} R:{anterior['stock_revendedor']}",
                    p_nuevo=f"F:{stock_final} R:{stock_revendedor}",
                    p_motivo=motivo
                )
            return mostrar_exito('Segmentación actualizada correctamente.', '/segmentacion')
        else:
            return mostrar_error("No se pudo actualizar la segmentación.")
    except Exception as e:
        print(f"Error en actualizar_segmentacion: {e}")
        return mostrar_error("Error interno al actualizar la segmentación.", 500)
    
@app.route('/eliminar_segmentacion/<int:seg_id>')
def eliminar_segmentacion_ruta(seg_id):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT producto_id FROM segmentacion_inventario WHERE id=%s", (seg_id,))
                    row = cursor.fetchone()
                    if row:
                        registrar_historial(row['producto_id'], 'DELETE', p_motivo='Segmentación eliminada')
                conn.commit()

        if eliminar_segmentacion(seg_id):
            return render_template('exito.html', mensaje='Segmentación eliminada correctamente.', volver='/segmentacion')
        else:
            return render_template('error_500.html'), 500
    except Exception as e:
        return render_template('error_500.html'), 500

@app.route('/toggle_segmentacion/<int:seg_id>')
def toggle_segmentacion_ruta(seg_id):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT producto_id, activo FROM segmentacion_inventario WHERE id=%s", (seg_id,))
                    row = cursor.fetchone()
                    if row:
                        registrar_historial(row['producto_id'], 'TOGGLE',
                                            p_campo='activo',
                                            p_anterior=row['activo'],
                                            p_nuevo=1 - row['activo'])
                conn.commit()

        if toggle_segmentacion(seg_id):
            datos = _obtener_datos_segmentacion()
            return render_template('segmentacion.html', edit_seg=None, **datos)
        else:
            return render_template('error_500.html'), 500
    except Exception as e:
        return render_template('error_500.html'), 500

# ════════════════════════════════════════════════════════════
# ALERTAS
# ════════════════════════════════════════════════════════════
def calcular_prediccion_dinamica(conn, producto_id, stock_actual, static_venta_dia):
    try:
        with conn.cursor() as cursor:
            # Consultar historial de ajustes del stock_total de los últimos 14 días
            sql = """
                SELECT valor_anterior, valor_nuevo, fecha
                FROM historial_ajustes
                WHERE producto_id = %s 
                  AND (campo_modificado = 'stock_total' OR accion = 'CONTEO')
                  AND fecha >= NOW() - INTERVAL 14 DAY
                ORDER BY fecha ASC
            """
            cursor.execute(sql, (producto_id,))
            rows = cursor.fetchall()
            
            reducciones = 0
            oldest_fecha = None
            
            for row in rows:
                try:
                    val_ant = int(row['valor_anterior']) if row['valor_anterior'] is not None else 0
                    val_nue = int(row['valor_nuevo']) if row['valor_nuevo'] is not None else 0
                    if val_ant > val_nue:
                        reducciones += (val_ant - val_nue)
                        if oldest_fecha is None:
                            oldest_fecha = row['fecha']
                except (ValueError, TypeError):
                    continue
            
            if oldest_fecha and reducciones > 0:
                delta = datetime.now() - oldest_fecha
                days = delta.total_seconds() / 86400.0
                days = max(days, 1.0) # Al menos 1 día para evitar valores atípicos
                venta_dia_real = reducciones / days
            else:
                venta_dia_real = float(static_venta_dia or 0)
                
            if venta_dia_real > 0:
                horas_restantes = (stock_actual / venta_dia_real) * 24.0
            else:
                horas_restantes = 9999.0
                
            # Calcular nivel
            if venta_dia_real <= 0:
                nivel = 'ok'
            elif horas_restantes <= 24:
                nivel = 'critico'
            elif horas_restantes <= 72:
                nivel = 'urgente'
            elif horas_restantes <= 120:
                nivel = 'advertencia'
            else:
                nivel = 'ok'
                
            return {
                'venta_dia_real': round(venta_dia_real, 2),
                'horas_restantes_real': round(horas_restantes, 1),
                'nivel_real': nivel,
                'usando_historial': oldest_fecha is not None and reducciones > 0
            }
    except Exception:
        # Fallback si ocurre algún error
        venta_dia_real = float(static_venta_dia or 0)
        horas = (stock_actual / venta_dia_real * 24) if venta_dia_real > 0 else 9999.0
        nivel = 'ok'
        if venta_dia_real > 0:
            if horas <= 24: nivel = 'critico'
            elif horas <= 72: nivel = 'urgente'
            elif horas <= 120: nivel = 'advertencia'
        return {
            'venta_dia_real': round(venta_dia_real, 2),
            'horas_restantes_real': round(horas, 1),
            'nivel_real': nivel,
            'usando_historial': False
        }

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

# ════════════════════════════════════════════════════════════
# HISTORIAL
# ════════════════════════════════════════════════════════════
@app.route('/listar_historial')
def listar_historial():
    try:
        resultado = leer_historial(p_limite=200)
        if resultado:
            for row in resultado:
                if isinstance(row.get('fecha'), datetime):
                    row['fecha'] = row['fecha'].strftime('%d/%m/%Y %H:%M')
        return render_template('lista_historial.html', datos=resultado)
    except Exception as e:
        print("Error en /listar_historial:", repr(e))
        return mostrar_error("Error al cargar el historial.", 500)


# ════════════════════════════════════════════════════════════
# CAMBIO DE CONTRASENA
# ════════════════════════════════════════════════════════════
@app.route('/cambiar_clave', methods=['POST'])
def cambiar_clave_ruta():
    try:
        clave_actual = request.form.get('clave_actual', '')
        clave_nueva  = request.form.get('clave_nueva', '')

        # Validaciones backend
        if not clave_actual or not clave_nueva:
            return mostrar_error("Ambas claves son requeridas.")
        if len(clave_nueva) < 8:
            return mostrar_error("La nueva clave debe tener al menos 8 caracteres.")
        if not any(c.isdigit() for c in clave_nueva):
            return mostrar_error("La nueva clave debe contener al menos un numero.")
        if clave_actual == clave_nueva:
            return mostrar_error("La nueva clave debe ser diferente a la actual.")

        if cambiar_clave(1, clave_actual, clave_nueva):
            return mostrar_exito(
                'Contrasena actualizada correctamente.',
                '/perfil', 'Volver al perfil')
        return mostrar_error("La contrasena actual es incorrecta.")
    except Exception as e:
        print("Error en /cambiar_clave:", repr(e))
        return mostrar_error("Error interno al cambiar la contrasena.", 500)


# ════════════════════════════════════════════════════════════
# EXPORTACION CSV DEL HISTORIAL
# ════════════════════════════════════════════════════════════
@app.route('/historial/exportar', methods=['GET'])
def exportar_historial_csv():
    try:
        accion = request.args.get('accion', '').strip().upper()
        registros = leer_historial(
            p_accion=accion if accion else None,
            p_limite=1000
        ) or []

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
        print("Error en /historial/exportar:", repr(e))
        return mostrar_error("Error al exportar el historial.", 500)


# ════════════════════════════════════════════════════════════
# CRUD — PERSONAL / TRABAJADORES
# ════════════════════════════════════════════════════════════
@app.route('/trabajadores')
def listar_trabajadores():
    try:
        lista = leer_trabajadores() or []
        return render_template('lista_trabajadores.html',
                               active_page='trabajadores',
                               alertas_count=contar_alertas(),
                               trabajadores=lista)
    except Exception as e:
        print("Error en /trabajadores:", repr(e))
        return mostrar_error("Error al cargar el listado de personal.", 500)


@app.route('/trabajadores/nuevo')
def vista_agregar_trabajador():
    return render_template('trabajador.html',
                           active_page='trabajadores',
                           alertas_count=contar_alertas())


@app.route('/insertar_trabajador', methods=['POST'])
def insertar_trabajador():
    try:
        nombre           = request.form.get('nombre', '').strip()
        codigo_empleado  = request.form.get('codigo_empleado', '').strip().upper()
        email            = request.form.get('email', '').strip()
        sede             = request.form.get('sede', '').strip()
        rol              = request.form.get('rol', 'operario').strip()
        palabra_clave    = request.form.get('palabra_clave', '').strip()

        if not nombre or not codigo_empleado or not sede:
            return mostrar_error("Nombre, codigo de empleado y sede son obligatorios.")

        obj = clsTrabajador(
            p_nombre=nombre,
            p_codigo_empleado=codigo_empleado,
            p_email=email,
            p_sede=sede,
            p_rol=rol,
            p_palabra_clave=palabra_clave,
            p_password_hash='Tottus2026'
        )

        if ad_insertar_trabajador(obj):
            return mostrar_exito(
                'Trabajador registrado correctamente. Clave inicial: Tottus2026',
                '/trabajadores', 'Ver personal')
        return mostrar_error("No se pudo registrar. El codigo de empleado ya existe.")
    except Exception as e:
        print("Error en /insertar_trabajador:", repr(e))
        return mostrar_error("Error interno al registrar el trabajador.", 500)


@app.route('/trabajadores/editar/<int:id>')
def vista_editar_trabajador(id):
    try:
        trabajador = leer_trabajador_por_id(id)
        if not trabajador:
            return mostrar_error("Trabajador no encontrado.", 404)
        return render_template('trabajador_edit.html',
                               active_page='trabajadores',
                               alertas_count=contar_alertas(),
                               trabajador=trabajador)
    except Exception as e:
        print("Error en /trabajadores/editar:", repr(e))
        return mostrar_error("Error al cargar el trabajador para edicion.", 500)


@app.route('/actualizar_trabajador', methods=['POST'])
def actualizar_trabajador():
    try:
        trab_id         = int(request.form.get('id', 0))
        nombre          = request.form.get('nombre', '').strip()
        codigo_empleado = request.form.get('codigo_empleado', '').strip().upper()
        email           = request.form.get('email', '').strip()
        sede            = request.form.get('sede', '').strip()
        rol             = request.form.get('rol', 'operario').strip()
        palabra_clave   = request.form.get('palabra_clave', '').strip()
        nueva_password  = request.form.get('nueva_password', '').strip()

        if not nombre or not codigo_empleado or not sede:
            return mostrar_error("Nombre, codigo de empleado y sede son obligatorios.")

        obj = clsTrabajador(
            p_id=trab_id,
            p_nombre=nombre,
            p_codigo_empleado=codigo_empleado,
            p_email=email,
            p_sede=sede,
            p_rol=rol,
            p_palabra_clave=palabra_clave,
            p_password_hash=nueva_password if nueva_password else None
        )

        if ad_actualizar_trabajador(obj):
            return mostrar_exito(
                'Datos del trabajador actualizados correctamente.',
                '/trabajadores', 'Ver personal')
        return mostrar_error("No se pudo actualizar. Verifique que el codigo no este duplicado.")
    except Exception as e:
        print("Error en /actualizar_trabajador:", repr(e))
        return mostrar_error("Error interno al actualizar el trabajador.", 500)


@app.route('/eliminar_trabajador/<int:id>')
def eliminar_trabajador(id):
    """
    El template lista_trabajadores.html usa GET con onclick=confirm().
    Se mantiene GET para compatibilidad con el template existente.
    """
    try:
        if ad_eliminar_trabajador(id):
            return mostrar_exito(
                'Trabajador desactivado del sistema correctamente.',
                '/trabajadores', 'Ver personal')
        return mostrar_error("Trabajador no encontrado o no se pudo desactivar.")
    except Exception as e:
        print("Error en /eliminar_trabajador:", repr(e))
        return mostrar_error("Error interno al desactivar el trabajador.", 500)


# ════════════════════════════════════════════════════════════
# RUTA — RESTABLECER CONTRASEÑA
# ════════════════════════════════════════════════════════════
@app.route('/restablecer', methods=['GET', 'POST'])
def restablecer():
    """
    GET  -> muestra el formulario de recuperacion de acceso.
    POST -> valida codigo de empleado y cambia la clave en texto plano.
    El template usa: codigo_empleado, clave_nueva.
    La palabra_clave del form se usa como clave_actual (mecanismo simple).
    """
    if request.method == 'POST':
        try:
            codigo    = request.form.get('codigo_empleado', '').strip()
            clave_sec = request.form.get('palabra_clave', '').strip()
            clave_nva = request.form.get('clave_nueva', '').strip()

            if not codigo or not clave_nva:
                return render_template('restablecer.html',
                                       error='El codigo de empleado y la nueva contraseña son obligatorios.')

            # Buscar el usuario por codigo_empleado para obtener su ID
            conn = obtenerconexion()
            usuario_id = None
            if conn:
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "SELECT id FROM usuarios WHERE codigo_empleado=%s AND activo=1",
                            (codigo,)
                        )
                        row = cursor.fetchone()
                        if row:
                            usuario_id = row['id']

            if not usuario_id:
                return render_template('restablecer.html',
                                       error='Codigo de empleado no encontrado.')

            # Cambiar clave: se usa clave_sec como verificacion de identidad
            # (si el campo esta vacio se omite la verificacion en text plain)
            if cambiar_clave(usuario_id, clave_sec, clave_nva):
                return mostrar_exito(
                    'Contraseña restablecida correctamente.',
                    '/', 'Ir al Login')
            else:
                return render_template('restablecer.html',
                                       error='No se pudo restablecer. Verifique su palabra clave de seguridad.')
        except Exception as e:
            print("Error en /restablecer:", repr(e))
            return render_template('restablecer.html',
                                   error='Error interno. Intente de nuevo.')

    return render_template('restablecer.html', error=None)

# ════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(debug=True, port=5000)