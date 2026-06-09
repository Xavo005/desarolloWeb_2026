import csv
import io
import json
from datetime import datetime
from bd import obtenerconexion

from flask import (
    Flask, render_template, request, Response, jsonify,
    session, redirect, url_for, stream_with_context
)

from productosAD import (
    leer_historial, registrar_historial,
    autenticar_usuario,
    clsProducto, leer_productos, leer_producto_por_id,
    insertar_producto, actualizar_producto, eliminar_producto,
    buscar_sku,
    clsConteo, leer_conteos, insertar_conteo,
    insertar_conteo_manual,
    verificar_dependencias_producto, verificar_dependencias_trabajador
)
from historialAD import leer_historial

# Si tu archivo se llama conteoAD.py, entonces debe ser:
from Conteo_NuevoAD import registrar_conteo, listar_conteos_reales

from alertaAD import (
    clsAlerta, obtener_alertas_activas, obtener_totales_alertas,
    eliminar_alerta, actualizar_alerta_sincronizada,
    obtener_alertas_dinamicas, contar_alertas
)
from segmentacionAD import (
    clsSegmentacion, obtener_segmentaciones, obtener_segmentacion_xID,
    insertar_segmentacion, actualizar_segmentacion, eliminar_segmentacion,
    toggle_segmentacion, validar_stock_disponible
)
from dashboardAD import (
    obtener_stats_dashboard, obtener_alertas_recientes,
    obtener_datos_graficos_dashboard, leer_productos_basico
)

from usuarioAD import (
clsTrabajador, leer_trabajadores, leer_trabajador_por_id,
    insertar_trabajador, actualizar_trabajador, eliminar_trabajador,
    cambiar_contrasena, restablecer_contrasena
)

app = Flask(__name__)
app.secret_key = 'tottus_sgi_secret_2026'

# ==============================================================================
# FUNCIONES AUXILIARES CENTRALIZADAS
# ==============================================================================
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


# ==============================================================================
# INTEGRIDAD REFERENCIAL - VALIDACIONES DE DEPENDENCIA
# ==============================================================================
def _verificar_dependencias_producto(prod_id):
    """Capa de controlador: delega validacion a tottusAD."""
    return verificar_dependencias_producto(prod_id)


def _verificar_dependencias_trabajador(usuario_id):
    """Capa de controlador: delega validacion a tottusAD."""
    return verificar_dependencias_trabajador(usuario_id)


# ==============================================================================
# RUTAS PUBLICAS - Login / Logout
# ==============================================================================
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
                # Guardar datos del usuario en la session nativa de Flask
                # autenticar_usuario retorna dict con: id, codigo_empleado, nombre, rol, password_hash
                session['id']              = usuario.get('id')
                session['nombre']          = usuario.get('nombre', 'Usuario')
                session['rol']             = usuario.get('rol', 'operario')
                session['codigo_empleado'] = usuario.get('codigo_empleado', '')
                session['sede']            = usuario.get('sede', '')
                return redirect(url_for('dashboard'))
            else:
                error = 'Codigo o contrasena incorrectos.'
        return render_template('login.html', error=error)
    except Exception as e:
        print("Error en /login:", repr(e))
        return mostrar_error("Error interno al intentar iniciar sesion.", 500)


@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html', error=None)


# ==============================================================================
# RUTAS - VISTAS PRINCIPALES
# ==============================================================================
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

@app.route('/api/dashboard/graficos')
def api_dashboard_graficos():
    try:
        datos = obtener_datos_graficos_dashboard()
        return jsonify({
            'success': True,
            'stock_por_categoria': datos['stock_por_categoria'],
            'tendencia_ajustes':   datos['tendencia_ajustes'],
            'alertas_por_nivel':   datos['alertas_por_nivel']
        })
    except Exception as e:
        print("Error en /api/dashboard/graficos:", repr(e))
        return jsonify({'success': False, 'message': str(e)}), 500


# ==============================================================================
# UC4 - ALERTAS DE QUIEBRE (Gianella Torres)
# ==============================================================================
# contar_alertas() fue movida a tottusAD.py - se importa desde alli

def _obtener_datos_alertas(modo='estatico'):
    if modo == 'dinamico':
        lista_alertas, totales = obtener_alertas_dinamicas()
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
        alerta_id     = int(request.form['id'])
        unidades      = int(request.form['unidades'])
        venta_dia     = float(request.form.get('venta_dia', 0) or 0)
        estado_transf = request.form['estado_transf'].strip()
        modo          = request.form.get('modo', 'estatico')
        stock_minimo  = request.form.get('stock_minimo')
        if stock_minimo is not None:
            try:
                stock_minimo = int(stock_minimo)
            except (ValueError, TypeError):
                stock_minimo = None

        obj_alerta = clsAlerta(
            id=alerta_id,
            unidades=unidades,
            venta_dia=venta_dia,
            estado_transf=estado_transf,
            stock_minimo=stock_minimo
        )

        exito = actualizar_alerta_sincronizada(obj_alerta)

        if not exito:
            return render_template('error_500.html'), 500

        # Patrón PRG: Redirigimos pasando el modo como parámetro en la URL (?modo=...)
    
        return redirect(url_for('alertas', modo=modo))

    except Exception as e:
        print("Error en /alertas/actualizar:", repr(e))
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
# API - ALERTAS - Gianella Torres
# ==============================================================================
@app.route("/api_listar_alertas")
def api_listar_alertas():
    try:
        # Capturamos el modo desde la URL (ej: /api_listar_alertas?modo=dinamico)
        modo = request.args.get('modo', 'estatico')
        
        # Llamamos a tu función interna que ya calcula todo
        datos = _obtener_datos_alertas(modo)
        
        # Retornamos solo el diccionario de alertas y totales en formato JSON
        return jsonify({
            "code": 1,
            "data": {
                "alertas": datos['alertas'],
                "totales": datos['totales'],
                "modo": datos['modo']
            }
        })
    except Exception as e:
        return jsonify({"code": -1, "data": {}, "message": repr(e)})

# ==============================================================================
# HISTORIAL-DIEGO CALDERON
# ==============================================================================
@app.context_processor
def inject_alertas():
    return dict(alertas_count=contar_alertas())

@app.route('/historial')
def historial():
    # Simplificamos al máximo: si la función falla, devolvemos lista vacía directamente
    # Esto elimina el try/except innecesario dentro de la ruta--CAMBIO -1.1
    registros = leer_historial(p_limite=100) or []
    
    return render_template('historial.html', 
                           active_page='dashboard', 
                           registros=registros)


@app.route('/perfil')
def perfil():
    # Obtener el usuario logueado usando el id guardado en session
    usuario_id = session.get('id')
    usuario = None
    if usuario_id:
        try:
            usuario = leer_trabajador_por_id(usuario_id)
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


# ==============================================================================
# CRUD - PRODUCTOS - Xavier Ruiz Guevara
# ==============================================================================
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
    try:
        sku       = request.form.get('sku', '').strip().upper()
        nombre    = request.form.get('nombre', '').strip()
        categoria = request.form.get('categoria', '').strip()
        ubicacion = request.form.get('ubicacion_gondola', '').strip()

        if not sku or not nombre:
            return mostrar_error("SKU y nombre son obligatorios.")

        try:
            stock  = int(request.form.get('stock_total', 0))
            precio = float(request.form.get('precio_unitario', 0))
            venta  = float(request.form.get('venta_dia', 0))
        except (ValueError, TypeError):
            return mostrar_error("Valores numericos invalidos.")

        if stock < 0 or precio < 0 or venta < 0:
            return mostrar_error("El stock, precio y venta diaria no pueden ser negativos.")

        obj = clsProducto(
            p_id=None,
            p_sku=sku,
            p_nombre=nombre,
            p_categoria=categoria,
            p_stock_total=stock,
            p_precio_unitario=precio,
            p_venta_dia=venta,
            p_ubicacion_gondola=ubicacion
        )

        if insertar_producto(obj):
            return mostrar_exito(
                'Producto registrado correctamente en el catalogo.',
                '/productos', 'Ver catalogo')

        return mostrar_error("No se pudo registrar. Es probable que el SKU ya exista.")

    except Exception as e:
        print(f"ERROR en /guardar_producto: {repr(e)}")
        return mostrar_error("Error interno al registrar el producto.", 500)


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
    """
    Antes de desactivar el producto, verifica que no tenga dependencias
    activas en segmentacion_inventario, alertas_quiebre o conteos_manuales.
    """
    try:
        bloqueo = _verificar_dependencias_producto(prod_id)
        if bloqueo:
            return mostrar_error(f"No se puede eliminar: {bloqueo}")

        if eliminar_producto(prod_id):
            return mostrar_exito(
                'Producto desactivado del catalogo correctamente.',
                '/productos', 'Ver catalogo')
        return mostrar_error("Producto no encontrado o no se pudo desactivar.")
    except Exception as e:
        print("Error en /eliminar_producto:", repr(e))
        return mostrar_error("Error interno al desactivar el producto.", 500)


# ==============================================================================
# API - PRODUCTOS - Xavier Ruiz Guevara
# ==============================================================================
@app.route("/api_listar_productos")
def api_listar_productos():
    try:
        resultado = leer_productos()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"code": -1, "data": {}, "message": repr(e)})


@app.route("/api_guardar_producto", methods=['POST'])
def api_guardar_producto():
    try:
        objProducto = clsProducto(
            None,
            request.json['sku'],
            request.json['nombre'],
            request.json['categoria'],
            request.json['stock_total'],
            request.json['precio_unitario'],
            request.json['venta_dia'],
            request.json['ubicacion_gondola']
        )
        if insertar_producto(objProducto):
            return jsonify({"code": 1, "message": "Producto insertado correctamente"})
        return jsonify({"code": 0, "data": {}, "message": "Error al insertar producto"})
    except Exception as e:
        return jsonify({"code": -1, "data": {}, "message": repr(e)})


# ==============================================================================
# API - ESCANER 
# ==============================================================================
@app.route("/api_buscar_sku", methods=["POST"])
def api_buscar_sku():
    try:
        sku_capturado = request.json['sku']
        resultado = buscar_sku(sku_capturado)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"code": -1, "message": repr(e)})


# ==============================================================================
# API — HISTORIAL CSV (MODIFICADO PARA POST)
# ==============================================================================
@app.route('/api/historial/exportar', methods=['POST']) # <--- Cambiado a POST
def api_exportar_historial():
    def generate():
        data = io.StringIO()
        writer = csv.writer(data)
        
        # Cabeceras
        writer.writerow(['ID', 'Producto ID', 'Accion', 'Campo', 'Anterior', 'Nuevo', 'Motivo', 'Fecha'])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        conn = obtenerconexion()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, producto_id, accion, campo_modificado, 
                           valor_anterior, valor_nuevo, motivo, fecha 
                    FROM historial_ajustes ORDER BY fecha DESC
                """)
                
                for reg in cursor:
                    writer.writerow([
                        reg.get('id'), 
                        reg.get('producto_id'), 
                        reg.get('accion'), 
                        reg.get('campo_modificado') or 'N/A', 
                        reg.get('valor_anterior') or '-', 
                        reg.get('valor_nuevo') or '-', 
                        reg.get('motivo'), 
                        reg.get('fecha')
                    ])
                    yield data.getvalue()
                    data.seek(0)
                    data.truncate(0)
        finally:
            conn.close()

    return Response(
        stream_with_context(generate()),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=historial_inventario.csv"}
    )






# ==============================================================================
# CRUD - SEGMENTACIONES - Gianella Torres
# ==============================================================================
def _obtener_datos_segmentacion():
    """Helper: reune datos para la vista de segmentacion. Sin SQL directo."""
    segmentaciones = obtener_segmentaciones()
    productos_lista = leer_productos_basico()
    totales = obtener_totales_alertas()
    alertas_count = totales.get('critico', 0) + totales.get('urgente', 0)
    return {
        'segmentaciones': segmentaciones,
        'productos': productos_lista,
        'alertas_count': alertas_count,
        'active_page': 'segmentacion'
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
        if not edit_seg:
            return mostrar_error('Segmentacion no encontrada.', 404)
        datos = _obtener_datos_segmentacion()
        return render_template('segmentacion.html', edit_seg=edit_seg, **datos)
    except Exception as e:
        print(f'Error en /segmentacion/editar: {repr(e)}')
        return render_template('error_500.html'), 500


@app.route('/guardar_segmentacion', methods=['POST'])
def guardar_segmentacion_ruta():
    try:
        producto_id      = int(request.form['producto_id'])
        stock_final      = int(request.form.get('stock_cliente_final', 0))
        stock_revendedor = int(request.form.get('stock_revendedor', 0))
        motivo           = request.form.get('motivo', '')

        # Validacion de stock disponible
        error = validar_stock_disponible(producto_id, stock_final + stock_revendedor)
        if error:
            return mostrar_error(error)

        # Insertar segmentacion
        objSegmentacion = clsSegmentacion(
            producto_id=producto_id,
            stock_cliente_final=stock_final,
            stock_revendedor=stock_revendedor,
            limite_compra_final=int(request.form.get('limite_compra_final', 0)),
            limite_compra_revendedor=int(request.form.get('limite_compra_revendedor', 0)),
            motivo=motivo
        )

        if insertar_segmentacion(objSegmentacion):
            registrar_historial(producto_id, 'CREATE', p_motivo=motivo)
            return mostrar_exito('Segmentacion creada correctamente.', '/segmentacion')
        else:
            return mostrar_error("No se pudo guardar la segmentacion.")
    except Exception as e:
        print(f"Error en guardar_segmentacion: {e}")
        return mostrar_error("Error interno al procesar la segmentacion.", 500)


@app.route('/actualizar_segmentacion', methods=['POST'])
def actualizar_segmentacion_ruta():
    try:
        seg_id           = int(request.form['seg_id'])
        stock_final      = int(request.form.get('stock_cliente_final', 0))
        stock_revendedor = int(request.form.get('stock_revendedor', 0))
        motivo           = request.form.get('motivo', '')

        anterior = obtener_segmentacion_xID(seg_id)
        if not anterior:
            return mostrar_error("Segmentacion no encontrada.")

        producto_id = anterior['producto_id']

        # Validacion de stock disponible
        error = validar_stock_disponible(producto_id, stock_final + stock_revendedor)
        if error:
            return mostrar_error(error)

        objSegmentacion = clsSegmentacion(
            id=seg_id,
            stock_cliente_final=stock_final,
            stock_revendedor=stock_revendedor,
            limite_compra_final=int(request.form.get('limite_compra_final', 0)),
            limite_compra_revendedor=int(request.form.get('limite_compra_revendedor', 0)),
            motivo=motivo
        )

        if actualizar_segmentacion(objSegmentacion):
            registrar_historial(
                p_producto_id=producto_id,
                p_accion='UPDATE',
                p_campo='segmentacion_stock',
                p_anterior=f"F:{anterior['stock_cliente_final']} R:{anterior['stock_revendedor']}",
                p_nuevo=f"F:{stock_final} R:{stock_revendedor}",
                p_motivo=motivo
            )
            return mostrar_exito('Segmentacion actualizada correctamente.', '/segmentacion')
        else:
            return mostrar_error("No se pudo actualizar la segmentacion.")
    except Exception as e:
        print(f"Error en actualizar_segmentacion: {e}")
        return mostrar_error("Error interno al actualizar la segmentacion.", 500)


@app.route('/eliminar_segmentacion/<int:seg_id>')
def eliminar_segmentacion_ruta(seg_id):
    """
    Elimina una segmentacion. La segmentacion en si no tiene dependencias
    adicionales que bloqueen su eliminacion - se permite directo.
    """
    try:
        row = obtener_segmentacion_xID(seg_id)
        if row:
            registrar_historial(row['producto_id'], 'DELETE', p_motivo='Segmentacion eliminada')

        if eliminar_segmentacion(seg_id):
            return mostrar_exito('Segmentacion eliminada correctamente.', '/segmentacion')
        else:
            return mostrar_error("No se pudo eliminar la segmentacion.")
    except Exception as e:
        return mostrar_error("Error interno al eliminar la segmentacion.", 500)


@app.route('/toggle_segmentacion/<int:seg_id>')
def toggle_segmentacion_ruta(seg_id):
    try:
        row = obtener_segmentacion_xID(seg_id)
        if row:
            registrar_historial(row['producto_id'], 'TOGGLE',
                                p_campo='activo',
                                p_anterior=row['activo'],
                                p_nuevo=1 - row['activo'])

        if toggle_segmentacion(seg_id):
            datos = _obtener_datos_segmentacion()
            return render_template('segmentacion.html', edit_seg=None, **datos)
        else:
            return render_template('error_500.html'), 500
    except Exception as e:
        return render_template('error_500.html'), 500


# ==============================================================================
# APIS - SEGMENTACIONES - Xavier Ruiz Guevara
# ==============================================================================
@app.route("/api_listar_segmentaciones")
def api_listar_segmentaciones():
    try:
        resultado = obtener_segmentaciones()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"code": -1, "message": repr(e)})


@app.route("/api_guardar_segmentacion", methods=['POST'])
def api_guardar_segmentacion():
    try:
        obj = clsSegmentacion(
            producto_id=request.json['producto_id'],
            stock_cliente_final=request.json['stock_cliente_final'],
            stock_revendedor=request.json['stock_revendedor'],
            limite_compra_final=request.json['limite_compra_final'],
            limite_compra_revendedor=request.json['limite_compra_revendedor'],
            motivo=request.json['motivo']
        )

        if insertar_segmentacion(obj):
            return jsonify({"code": 1, "message": "Segmentacion registrada correctamente"})

        return jsonify({"code": 0, "message": "No se pudo registrar. Verifique el stock disponible."})

    except Exception as e:
        return jsonify({"code": -1, "message": repr(e)})


# ==============================================================================
# APIS - USUARIOS / TRABAJADORES
# ==============================================================================
@app.route("/api_listar_usuarios")
def api_listar_usuarios():
    try:
        datos = leer_trabajadores()
        return jsonify(datos)
    except Exception as e:
        return jsonify({"code": -1, "message": f"Error: {repr(e)}"})


@app.route("/api_guardar_usuario", methods=['POST'])
def api_guardar_usuario():
    try:
        d = request.json
        pwd = d.get('password_hash')
        if not pwd:
            pwd = '123'
        obj = clsTrabajador(
            None,
            d.get('nombre', ''),
            d.get('codigo_empleado', ''),
            d.get('email', ''),
            d.get('sede', ''),
            d.get('rol', 'operario'),
            pwd, 
            1
        )
        
        if insertar_trabajador(obj):
            return jsonify({"code": 1, "message": "Trabajador registrado correctamente"})
        else:
            return jsonify({"code": 0, "message": "No se pudo registrar (codigo duplicado o error)"})
    except Exception as e:
        return jsonify({"code": -1, "message": str(e)})
    


#==============================================================================
# APIS - CONTEOS MANUALES - Diego Calderon
#=============================================================================

    
# --- LISTAR ---
@app.route("/api/conteos/listar", methods=['POST'])
def api_listar_conteos():
    try:
        resultado = listar_conteos_reales()
        # Imprime esto en la consola para ver qué está pasando antes de enviar
        print(f"DEBUG: Datos obtenidos de BD: {resultado}")
        
        if not resultado:
            return jsonify({"code": 0, "message": "No se encontraron registros o hubo un error"})
            
        return jsonify({"code": 1, "data": resultado})
    except Exception as e:
        print(f"ERROR EN API LISTAR: {e}")
        return jsonify({"code": -1, "message": str(e)})

# --- GUARDAR ---
@app.route("/api/conteos/guardar", methods=['POST'])
def api_guardar_conteo():
    try:
        data = request.json
        # 1. Extraemos los 6 datos del JSON
        producto_id = data['producto_id']
        usuario_id = data['usuario_id']
        stock_sistema = data['stock_sistema']
        stock_contado = data['stock_contado']
        motivo = data['motivo']
        estado = data['estado'] # ¡Esto es lo que faltaba extraer!
        
        # 2. Llamamos pasando los 6 argumentos
        if registrar_conteo(producto_id, usuario_id, stock_sistema, stock_contado, motivo, estado):
            return jsonify({"code": 1, "message": "Conteo registrado con éxito"})
        else:
            return jsonify({"code": 0, "message": "Error al registrar en la BD"})
    except Exception as e:
        # Si aquí sale el error, es que algo en el JSON de arriba falló (ej: falta un campo)
        return jsonify({"code": -1, "message": str(e)})


@app.route('/listar_alertas')
def api_get_alertas():
    """
    Muestra la lista de alertas activas.
    Delega a obtener_alertas_activas() de tottusAD (Regla 3 capas).
    Sin SELECT * ni acceso directo a BD desde el controlador.
    """
    try:
        resultado = obtener_alertas_activas()
        return render_template('lista_alertas.html', datos=resultado)
    except Exception as e:
        return mostrar_error("Error al cargar la lista de alertas.", 500)



# ==============================================================================
# HISTORIAL
# ==============================================================================
@app.route('/api/historial/listar', methods=['POST'])
def api_listar_historial():
    try:
        # Llamamos a tu función de la capa de datos
        resultado = leer_historial(p_limite=200)
        
        # Formateo de fechas para que el JSON no explote con objetos datetime
        if resultado:
            for row in resultado:
                if isinstance(row.get('fecha'), datetime):
                    row['fecha'] = row['fecha'].strftime('%d/%m/%Y %H:%M')
                    
        return jsonify({"code": 1, "data": resultado})
    except Exception as e:
        print("Error en /api/historial/listar:", repr(e))
        return jsonify({"code": 0, "message": "Error al cargar historial"})





# ==============================================================================
# CRUD - TRABAJADORES - SECLEN
# ==============================================================================

# ==============================================================================
# RUTA - LISTAR
# ==============================================================================  
@app.route('/trabajadores')
def listar_trabajadores():
    try:
        lista = leer_trabajadores() or []
        return render_template('lista_trabajadores.html',
                               active_page='trabajadores',
                               alertas_count=contar_alertas(), # Dejamos el 3 fijo de tu campana
                               trabajadores=lista)
    except Exception as e:
        print("Error en /trabajadores:", repr(e))
        return mostrar_error("Error al cargar el listado de personal.", 500)

# ==============================================================================
# RUTA - INSERTAR
# ==============================================================================  
@app.route('/trabajadores/nuevo')
def vista_agregar_trabajador():
    return render_template('trabajador.html',
                           active_page='trabajadores',
                           alertas_count=contar_alertas())

@app.route('/insertar_trabajador', methods=['POST'])
def insertar_trabajador_ruta():
    try:
        nombre          = request.form.get('nombre', '').strip()
        codigo_empleado = request.form.get('codigo_empleado', '').strip().upper()
        email           = request.form.get('email', '').strip()
        sede            = request.form.get('sede', '').strip().lower()
        rol             = request.form.get('rol', 'operario').strip().lower()
        palabra_clave   = request.form.get('palabra_clave', '').strip()

        if not nombre or not codigo_empleado or not sede:
            return mostrar_error("Nombre, codigo de empleado y sede son obligatorios.")

        obj = clsTrabajador()
        obj.nombre = nombre
        obj.codigo_empleado = codigo_empleado
        obj.email = email
        obj.sede = sede
        obj.rol = rol
        obj.palabra_clave = palabra_clave
        obj.password = 'Tottus2026'

        if insertar_trabajador(obj): 
            return mostrar_exito(
                'Trabajador registrado correctamente. Clave inicial: Tottus2026',
                '/trabajadores', 'Ver personal')
            
        return mostrar_error("No se pudo registrar. El codigo de empleado ya existe.")
    except Exception as e:
        print("Error en /insertar_trabajador:", repr(e))
        return mostrar_error("Error interno al registrar el trabajador.", 500)
    
# ==============================================================================
# RUTA - ACTUALIZAR
# ==============================================================================      
@app.route('/trabajadores/editar/<int:id>')
def vista_editar_trabajador(id):
    try:
        trabajador_obj = leer_trabajador_por_id(id)
        if not trabajador_obj:
            return "Trabajador no encontrado.", 404
        
        return render_template('trabajador_edit.html',
                               active_page='trabajadores',
                               alertas_count=contar_alertas(),
                               trabajador=trabajador_obj)   
                               
    except Exception as e:
        print(f"Error en vista_editar_trabajador: {repr(e)}")
        return "Error interno al cargar el formulario de edicion.", 500

@app.route('/actualizar_trabajador', methods=['POST'])
def actualizar_trabajador_ruta():
    try:
        trab_id         = int(request.form.get('id', 0))
        nombre          = request.form.get('nombre', '').strip()
        codigo_empleado = request.form.get('codigo_empleado', '').strip().upper()
        email           = request.form.get('email', '').strip()
        sede            = request.form.get('sede', '').strip().lower()
        rol             = request.form.get('rol', 'operario').strip().lower()
        palabra_clave   = request.form.get('palabra_clave', '').strip()
        nueva_password  = request.form.get('nueva_password', '').strip()

        if not nueva_password:
            trab_actual = leer_trabajador_por_id(trab_id)
            if trab_actual and isinstance(trab_actual, dict):
                nueva_password = trab_actual.get('password')

        obj = clsTrabajador()
        obj.id = trab_id
        obj.nombre = nombre
        obj.codigo_empleado = codigo_empleado
        obj.email = email
        obj.sede = sede
        obj.rol = rol
        obj.palabra_clave = palabra_clave
        obj.password = nueva_password

        if actualizar_trabajador(obj): 
            return redirect(url_for('listar_trabajadores'))
            
        return "Error: Codigo de empleado ya registrado o datos invalidos.", 400
        
    except Exception as e:
        print(f"Error en actualizar_trabajador_ruta: {repr(e)}")
        return "Error interno al actualizar el registro.", 500
    
# ==============================================================================
# RUTA -ELIMINAR
# ==============================================================================            
@app.route('/eliminar_trabajador/<int:id>', methods=['POST', 'GET'])
def eliminar_trabajador_ruta(id):
    try:
        # CORREGIDO: Se quitó el 'ad_' para llamar a la función real de tottusAD
        if eliminar_trabajador(id): 
            return mostrar_exito(
                'Trabajador desactivado del sistema correctamente.',
                '/trabajadores', 'Ver personal')
            
        return mostrar_error("Trabajador no encontrado o no se pudo desactivar.")
    except Exception as e:
        print("Error en /eliminar_trabajador:", repr(e))
        return mostrar_error("Error interno al desactivar el trabajador.", 500)

# ==============================================================================
# RUTA - CAMBIO DE CONTRASENA (Desde cambiar_clave.html)
# ==============================================================================
@app.route('/cambiar_clave', methods=['GET', 'POST'])
def cambiar_clave_ruta():
    if request.method == 'GET':
        return render_template('cambiar_clave.html')

    try:
        clave_actual    = request.form.get('clave_actual', '').strip()
        clave_nueva     = request.form.get('clave_nueva', '').strip()
        clave_confirmar = request.form.get('clave_confirmar', '').strip()

        if not clave_actual or not clave_nueva:
            return mostrar_error("Ambas claves son requeridas.", 400)
            
        if clave_nueva != clave_confirmar:
            return mostrar_error("La nueva contrasena y su confirmacion no coinciden.", 400)
            
        if len(clave_nueva) < 8 or not any(c.isdigit() for c in clave_nueva):
            return mostrar_error("La nueva clave debe tener al menos 8 caracteres y contener un numero.", 400)
            
        if clave_actual == clave_nueva:
            return mostrar_error("La nueva clave debe ser diferente a la actual.", 400)

        trabajador_id = session.get('id')
        if not trabajador_id:
            return mostrar_error("Sesion no valida o expirada. Por favor, vuelve a loguearte.", 401)

        if cambiar_contrasena(trabajador_id, clave_actual, clave_nueva):
            return redirect(url_for('listar_trabajadores'))
            
        return mostrar_error("La contrasena actual es incorrecta.", 400)

    except Exception as e:
        print(f"Error en cambiar_clave_ruta: {repr(e)}")
        return mostrar_error("Error interno del servidor.", 500)

# ==============================================================================
# RUTA - RESTABLECER CONTRASEÑA
# ==============================================================================
@app.route('/restablecer', methods=['GET', 'POST'])
def restablecer():
    if request.method == 'POST':
        try:
            codigo    = request.form.get('codigo_empleado', '').strip()
            clave_sec = request.form.get('palabra_clave', '').strip()
            clave_nva = request.form.get('clave_nueva', '').strip()

            if not codigo or not clave_nva:
                return render_template('restablecer.html',
                                       error='El codigo de empleado y la nueva contrasena son obligatorios.')

            if restablecer_contrasena(codigo, clave_sec, clave_nva):
                return mostrar_exito(
                    'Contrasena restablecida correctamente.',
                    '/', 'Ir al Login')
            else:
                return render_template('restablecer.html',
                                       error='Datos incorrectos. Verifique su codigo o palabra clave.')
        except Exception as e:
            print("Error en /restablecer:", repr(e))
            return render_template('restablecer.html',
                                   error='Error interno. Intente de nuevo.')

    return render_template('restablecer.html', error=None)

# ==============================================================================
if __name__ == '__main__':
    app.run(debug=True, port=5000)
