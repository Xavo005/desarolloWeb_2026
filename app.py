"""
app.py — Tottus SGI · Controlador (Capa de Presentacion)
Solo rutas Flask + validacion de formularios + render_template.
Toda la logica de datos vive en tottusAD.py.
"""
import csv
import io
import json
from datetime import datetime
from flask import Flask, render_template, request, Response, jsonify  # type: ignore[import]
from bd import obtenerconexion
from tottusAD import (
    autenticar_usuario,
    clsProducto, leer_productos, leer_producto_por_id,
    insertar_producto, actualizar_producto, eliminar_producto,
    buscar_sku,
    clsSegmentacion, leer_segmentaciones, leer_segmentacion_por_id,
    insertar_segmentacion, actualizar_segmentacion,
    eliminar_segmentacion, toggle_segmentacion,
    contar_alertas, leer_alertas, eliminar_alerta,
    leer_historial, registrar_historial,
    cambiar_clave,
    clsTrabajador, leer_trabajadores, leer_trabajador_por_id,
    insertar_trabajador  as ad_insertar_trabajador,
    actualizar_trabajador as ad_actualizar_trabajador,
    eliminar_trabajador  as ad_eliminar_trabajador,
)

from flask import Flask
try:
    from routes.api_inventario import api_bp
except ImportError as e:
    print(f"Error específico de importación: {e}")



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
                                       stats={'alertas_criticas': 0, 'total_productos': 0},
                                       alertas_recientes=[])
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
# ==============================================================================
@app.route('/alertas')
def alertas():
    lista_alertas = []
    totales_por_nivel = {'critico': 0, 'urgente': 0, 'ok': 0}
    try:
        resultado = leer_alertas()
        if resultado:
            lista_alertas = resultado
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
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
    try:
        sku    = request.form.get('sku', '').strip().upper()
        nombre = request.form.get('nombre', '').strip()
        categoria = request.form.get('categoria', '').strip()
        ubicacion = request.form.get('ubicacion_gondola', '').strip()
        
        if not sku or not nombre:
            return mostrar_error("SKU y nombre son obligatorios.")

        try:
            stock  = int(request.form.get('stock_total', 0))
            precio = float(request.form.get('precio_unitario', 0))
            venta  = float(request.form.get('venta_dia', 0))
        except (ValueError, TypeError):
            return mostrar_error("Valores numéricos inválidos.")

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
                'Producto registrado correctamente en el catálogo.',
                '/productos', 'Ver catálogo')
        
        return mostrar_error("No se pudo registrar. Es probable que el SKU ya exista.")
        
    except Exception as e:
        print(f"--- ERROR CRÍTICO EN /guardar_producto ---")
        print(repr(e)) 
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
# API — PRODUCTOS - Xavier Ruiz Guevara
# ════════════════════════════════════════════════════════════
@app.route("/api_listar_productos")
def api_listar_productos():
    try:
        resultado = leer_productos()
        return jsonify(resultado)
    except:
        return {}
    
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
# API — HISTORIAL CSV  (EDIEGO CALDERON)
# ════════════════════════════════════════════════════════════
print("--- CARGANDO RUTA EXPORTAR ---")
@app.route('/api/historial/exportar', methods=['GET'])
def api_exportar_historial():
    try:
        conn = obtenerconexion()
        with conn.cursor() as cursor:
            # CORRECCIÓN: Usamos 'fecha' que es el nombre real de tu columna
            cursor.execute("SELECT * FROM historial_ajustes ORDER BY fecha DESC")
            registros = cursor.fetchall()
        conn.close()

        si = io.StringIO()
        cw = csv.writer(si)
        
        # Encabezados
        cw.writerow(['ID', 'Producto ID', 'Accion', 'Campo', 'Anterior', 'Nuevo', 'Motivo', 'Fecha'])

        # CORRECCIÓN: Nombres de columnas actualizados según tu tabla
        for reg in registros:
            cw.writerow([
                reg['id'], 
                reg['producto_id'], 
                reg['accion'],           # Antes era 'tipo'
                reg['campo_modificado'], # Antes era 'campo'
                reg['valor_anterior'], 
                reg['valor_nuevo'], 
                reg['motivo'], 
                reg['fecha']             # Antes era 'fecha_hora'
            ])

        output = si.getvalue()
        return Response(
            output,
            mimetype='text/csv',
            headers={"Content-Disposition": "attachment;filename=historial_inventario.csv"}
        )

    except Exception as e:
        print("Error en /api/historial/exportar:", repr(e))
        return Response(
            json.dumps({'success': False, 'message': str(e)}),
            mimetype='application/json', status=500
        )




































# ════════════════════════════════════════════════════════════
# CRUD — SEGMENTACIONES
# ════════════════════════════════════════════════════════════
@app.route('/segmentacion')
def segmentacion():
    try:
        productos_lista = leer_productos() or []
        segmentaciones  = leer_segmentaciones() or []
        return render_template('segmentacion.html',
                               active_page='productos',
                               alertas_count=contar_alertas(),
                               productos=productos_lista,
                               segmentaciones=segmentaciones,
                               edit_seg=None)
    except Exception as e:
        print("Error en /segmentacion:", repr(e))
        return mostrar_error("Error al cargar la segmentacion de inventario.", 500)

@app.route('/guardar_segmentacion', methods=['POST'])
def guardar_segmentacion():
    try:
        producto_id      = int(request.form.get('producto_id', 0))
        stock_final      = int(request.form.get('stock_cliente_final', 0))
        stock_revendedor = int(request.form.get('stock_revendedor', 0))
        limite_final     = int(request.form.get('limite_compra_final', 0))
        limite_revend    = int(request.form.get('limite_compra_revendedor', 0))
        motivo           = request.form.get('motivo', '')

        obj = clsSegmentacion(
            p_producto_id=producto_id,
            p_usuario_id=1,
            p_stock_cliente_final=stock_final,
            p_stock_revendedor=stock_revendedor,
            p_limite_compra_final=limite_final,
            p_limite_compra_revendedor=limite_revend,
            p_motivo=motivo
        )

        if insertar_segmentacion(obj):
            return mostrar_exito(
                'Ajuste de segmentacion registrado con exito.',
                '/segmentacion', 'Ver segmentaciones')
        return mostrar_error("No se pudo registrar. El total asignado puede superar el stock disponible.")
    except Exception as e:
        print("Error en /guardar_segmentacion:", repr(e))
        return mostrar_error("Error interno al registrar la segmentacion.", 500)



@app.route('/segmentacion/editar/<int:seg_id>')
def editar_segmentacion_vista(seg_id):
    try:
        productos_lista = leer_productos() or []
        segmentaciones  = leer_segmentaciones() or []
        edit_seg        = leer_segmentacion_por_id(seg_id)
        return render_template('segmentacion.html',
                               active_page='productos',
                               alertas_count=contar_alertas(),
                               productos=productos_lista,
                               segmentaciones=segmentaciones,
                               edit_seg=edit_seg)
    except Exception as e:
        print("Error en /segmentacion/editar:", repr(e))
        return mostrar_error("Error al cargar la segmentacion para edicion.", 500)




@app.route('/actualizar_segmentacion', methods=['POST'])
def actualizar_segmentacion_ruta():
    try:
        seg_id           = int(request.form.get('seg_id', 0))
        stock_final      = int(request.form.get('stock_cliente_final', 0))
        stock_revendedor = int(request.form.get('stock_revendedor', 0))
        limite_final     = int(request.form.get('limite_compra_final', 0))
        limite_revend    = int(request.form.get('limite_compra_revendedor', 0))
        motivo           = request.form.get('motivo', '')

        obj = clsSegmentacion(
            p_id=seg_id,
            p_usuario_id=1,
            p_stock_cliente_final=stock_final,
            p_stock_revendedor=stock_revendedor,
            p_limite_compra_final=limite_final,
            p_limite_compra_revendedor=limite_revend,
            p_motivo=motivo
        )

        if actualizar_segmentacion(obj):
            return mostrar_exito(
                'Ajuste de segmentacion actualizado correctamente.',
                '/segmentacion', 'Ver segmentaciones')
        return mostrar_error("No se pudo actualizar. Verifique los datos e intente de nuevo.")
    except Exception as e:
        print("Error en /actualizar_segmentacion:", repr(e))
        return mostrar_error("Error interno al actualizar la segmentacion.", 500)


@app.route('/eliminar_segmentacion/<int:seg_id>', methods=['POST'])
def eliminar_segmentacion_ruta(seg_id):
    try:
        if eliminar_segmentacion(seg_id):
            return mostrar_exito(
                'Ajuste de segmentacion eliminado.',
                '/segmentacion', 'Ver segmentaciones')
        return mostrar_error("Registro de segmentacion no encontrado.")
    except Exception as e:
        print("Error en /eliminar_segmentacion:", repr(e))
        return mostrar_error("Error interno al eliminar la segmentacion.", 500)


@app.route('/toggle_segmentacion/<int:seg_id>', methods=['POST'])
def toggle_segmentacion_ruta(seg_id):
    try:
        if toggle_segmentacion(seg_id):
            return mostrar_exito(
                'Estado de segmentacion modificado con exito.',
                '/segmentacion', 'Ver segmentaciones')
        return mostrar_error("Registro de segmentacion no encontrado.")
    except Exception as e:
        print("Error en /toggle_segmentacion:", repr(e))
        return mostrar_error("Error interno al cambiar el estado.", 500)

# ════════════════════════════════════════════════════════════
# AP IS — SEGMENTACIONES Xavier Ruiz Guevara
# ════════════════════════════════════════════════════════════
@app.route("/api_listar_segmentaciones")
def api_listar_segmentaciones():
    try:
        resultado = leer_segmentaciones()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"code": -1, "message": repr(e)})

@app.route("/api_guardar_segmentacion", methods=['POST'])
def api_guardar_segmentacion():
    try:
        obj = clsSegmentacion(
            p_producto_id=request.json['producto_id'],
            p_usuario_id=1, # Manteniendo tu lógica fija de usuario
            p_stock_cliente_final=request.json['stock_cliente_final'],
            p_stock_revendedor=request.json['stock_revendedor'],
            p_limite_compra_final=request.json['limite_compra_final'],
            p_limite_compra_revendedor=request.json['limite_compra_revendedor'],
            p_motivo=request.json['motivo']
        )
        
        if insertar_segmentacion(obj):
            return jsonify({"code": 1, "message": "Segmentación registrada correctamente"})
        
        return jsonify({"code": 0, "message": "No se pudo registrar. Verifique el stock disponible."})
        
    except Exception as e:
        return jsonify({"code": -1, "message": repr(e)}) 

# ════════════════════════════════════════════════════════════
# ALERTAS
# ════════════════════════════════════════════════════════════
@app.route('/listar_alertas')
def listar_alertas():
    try:
        resultado = leer_alertas()
        return render_template('lista_alertas.html', datos=resultado)
    except Exception as e:
        print("Error en /listar_alertas:", repr(e))
        return mostrar_error("Error al cargar las alertas.", 500)


@app.route('/eliminar_alerta/<int:alerta_id>', methods=['POST'])
def eliminar_alerta_ruta(alerta_id):
    try:
        if eliminar_alerta(alerta_id):
            return mostrar_exito(
                'Alerta descartada correctamente.',
                '/alertas', 'Ver alertas')
        return mostrar_error("Alerta no encontrada.")
    except Exception as e:
        print("Error en /eliminar_alerta:", repr(e))
        return mostrar_error("Error interno al descartar la alerta.", 500)


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