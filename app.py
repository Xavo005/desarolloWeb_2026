"""
app.py — Tottus SGI · Backend Unificado
Reemplaza: app.py + main.py + alertasAD.py
"""
import os
from functools import wraps
from datetime import datetime
from flask import (Flask, render_template, request, jsonify,
                   session, redirect, url_for, flash)
import mysql.connector
from mysql.connector import Error
from werkzeug.security import check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev_secret_change_me')

# ── Configuración BD ─────────────────────────────────────────
DB_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'tottus_sgi'),
    'user':     os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
}

def get_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"[ERROR BD] {e}")
        return None

# ── Decoradores ──────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def requiere_rol(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'usuario_id' not in session:
                return jsonify({'error': 'No autenticado'}), 401
            if session.get('rol') not in roles:
                return jsonify({'error': 'Sin permisos para esta acción'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


def contar_alertas():
    conn = get_db()
    if not conn:
        return 0
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM alertas_quiebre WHERE activo=1 AND nivel IN ('critico','urgente')")
        return cur.fetchone()[0]
    finally:
        conn.close()

def registrar_historial(conn, producto_id, accion,
                        campo=None, anterior=None, nuevo=None, motivo=None):
    if 'usuario_id' not in session:
        return
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO historial_ajustes
            (producto_id, usuario_id, empleado_nombre, accion,
             campo_modificado, valor_anterior, valor_nuevo, motivo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (producto_id, session['usuario_id'], session.get('nombre', ''),
          accion, campo, str(anterior) if anterior is not None else None,
          str(nuevo) if nuevo is not None else None, motivo))

# ════════════════════════════════════════════════════════════
# RUTAS PÚBLICAS
# ════════════════════════════════════════════════════════════
@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))

    error = None
    if request.method == 'POST':
        codigo = request.form.get('codigo_empleado', '').strip()
        clave  = request.form.get('password', '')

        conn = get_db()
        if conn:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT * FROM usuarios WHERE codigo_empleado=%s AND activo=1",
                (codigo,)
            )
            usuario = cur.fetchone()
            conn.close()

            if usuario and check_password_hash(usuario['password_hash'], clave):
                session.clear()
                session['usuario_id'] = usuario['id']
                session['nombre']     = usuario['nombre']
                session['rol']        = usuario['rol']
                session['sede']       = usuario['sede']
                session['codigo']     = usuario['codigo_empleado']

                # Actualizar último login
                c2 = get_db()
                if c2:
                    cur2 = c2.cursor()
                    cur2.execute("UPDATE usuarios SET ultimo_login=NOW() WHERE id=%s",
                                 (usuario['id'],))
                    c2.commit()
                    c2.close()

                return redirect(url_for('dashboard'))
            else:
                error = 'Código o contraseña incorrectos.'
        else:
            error = 'Error de conexión con la base de datos.'

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ════════════════════════════════════════════════════════════
# RUTAS AUTENTICADAS — VISTAS
# ════════════════════════════════════════════════════════════
@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    stats = {'alertas_criticas': 0, 'productos_ok': 0, 'total_productos': 0}
    alertas_recientes = []
    if conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) AS n FROM alertas_quiebre WHERE activo=1 AND nivel='critico'")
        stats['alertas_criticas'] = cur.fetchone()['n']
        cur.execute("SELECT COUNT(*) AS n FROM productos WHERE activo=1")
        stats['total_productos'] = cur.fetchone()['n']
        cur.execute("""
            SELECT sku, producto, nivel, horas_restantes
            FROM alertas_quiebre WHERE activo=1 ORDER BY horas_restantes ASC LIMIT 3
        """)
        alertas_recientes = cur.fetchall()
        conn.close()

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
@login_required
def alertas():
    conexion = get_db()
    lista_alertas = []
    totales_por_nivel = {'critico': 0, 'urgente': 0, 'ok': 0}
    
    if conexion:
        cursor = conexion.cursor(dictionary=True)
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
        conexion.close()

    return render_template('alertas.html',
                           active_page='alertas',
                           alertas_count=contar_alertas(),
                           alertas=lista_alertas,
                           totales=totales_por_nivel)

# ==============================================================================
# UC6 - SEGMENTAR STOCK (Gianella)
# Vista principal para crear y gestionar reglas de segmentación de inventario.
# ==============================================================================
@app.route('/segmentacion')
@login_required
def segmentacion():
    # La lógica frontend pesada está en segmentacion.js (ver /api/segmentaciones)
    return render_template('segmentacion.html',
                           active_page='segmentacion',
                           alertas_count=contar_alertas())

@app.route('/historial')
@login_required
def historial():
    conn = get_db()
    registros = []
    if conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM v_historial_completo LIMIT 100")
        registros = cur.fetchall()
        conn.close()

    return render_template('historial.html',
                           active_page='dashboard',
                           alertas_count=contar_alertas(),
                           registros=registros)

@app.route('/perfil')
@login_required
def perfil():
    conn = get_db()
    usuario = None
    if conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE id=%s", (session['usuario_id'],))
        usuario = cur.fetchone()
        conn.close()

    return render_template('perfil.html',
                           active_page='perfil',
                           alertas_count=contar_alertas(),
                           usuario=usuario)

@app.route('/productos')
@login_required
def productos():
    return render_template('productos.html',
                           active_page='productos',
                           alertas_count=contar_alertas())

@app.route('/escanear')
@login_required
def escanear():
    return render_template('escanear.html',
                           active_page='escanear',
                           alertas_count=contar_alertas())

# ════════════════════════════════════════════════════════════
# UC5 - Xavier Ruiz Guevara - Gestión de productos.
# ════════════════════════════════════════════════════════════
@app.route('/api/productos', methods=['GET'])
@login_required
def api_get_productos():
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Error de BD'}), 500
    cur = conn.cursor(dictionary=True)
    q = request.args.get('q', '').strip()
    todos = request.args.get('todos', '0')
    filtro_activo = '' if todos == '1' else 'WHERE activo=1'
    if q:
        cur.execute(f"""
            SELECT * FROM productos WHERE
            (nombre LIKE %s OR sku LIKE %s OR categoria LIKE %s)
            {'AND activo=1' if todos != '1' else ''}
            ORDER BY nombre
        """, (f'%{q}%', f'%{q}%', f'%{q}%'))
    else:
        cur.execute(f"SELECT * FROM productos {filtro_activo} ORDER BY nombre")
    data = cur.fetchall()
    conn.close()
    return jsonify({'success': True, 'data': data})


@app.route('/api/productos', methods=['POST'])
@requiere_rol('supervisor', 'gerente')
def api_crear_producto():
    data = request.get_json() or {}
    sku = (data.get('sku') or '').strip().upper()
    nombre = (data.get('nombre') or '').strip()
    if not sku or not nombre:
        return jsonify({'success': False, 'message': 'SKU y nombre son obligatorios'}), 400

    try:
        stock = int(data.get('stock_total', 0))
        precio = float(data.get('precio_unitario', 0))
        venta = float(data.get('venta_dia', 0))
    except ValueError:
        return jsonify({'success': False, 'message': 'Valores numéricos inválidos'}), 400

    if stock < 0 or precio < 0 or venta < 0:
        return jsonify({'success': False, 'message': 'El stock, precio y venta diaria no pueden ser negativos'}), 400

    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Error BD'}), 500
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT id FROM productos WHERE sku=%s", (sku,))
    if cur.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': f'El SKU "{sku}" ya existe'}), 409

    try:
        cur.execute("""
            INSERT INTO productos
                (sku, nombre, categoria, stock_total, precio_unitario, venta_dia, ubicacion_gondola)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (sku, nombre,
              data.get('categoria', ''),
              stock,
              precio,
              venta,
              data.get('ubicacion_gondola', '')))
        nuevo_id = cur.lastrowid
        registrar_historial(conn, nuevo_id, 'CREATE',
                            motivo=f'Producto "{nombre}" agregado al catálogo')
        conn.commit()
        return jsonify({'success': True, 'message': 'Producto creado', 'id': nuevo_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/productos/<int:prod_id>', methods=['PUT'])
@requiere_rol('supervisor', 'gerente')
def api_actualizar_producto(prod_id):
    data = request.get_json() or {}
    nombre = (data.get('nombre') or '').strip()
    if not nombre:
        return jsonify({'success': False, 'message': 'Nombre obligatorio'}), 400

    try:
        stock = int(data.get('stock_total', 0))
        precio = float(data.get('precio_unitario', 0))
        venta = float(data.get('venta_dia', 0))
    except ValueError:
        return jsonify({'success': False, 'message': 'Valores numéricos inválidos'}), 400

    if stock < 0 or precio < 0 or venta < 0:
        return jsonify({'success': False, 'message': 'El stock, precio y venta diaria no pueden ser negativos'}), 400

    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Error BD'}), 500
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM productos WHERE id=%s", (prod_id,))
    anterior = cur.fetchone()
    if not anterior:
        conn.close()
        return jsonify({'success': False, 'message': 'Producto no encontrado'}), 404

    nuevo_sku = (data.get('sku') or anterior['sku']).strip().upper()
    cur.execute("SELECT id FROM productos WHERE sku=%s AND id!=%s", (nuevo_sku, prod_id))
    if cur.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': f'El SKU "{nuevo_sku}" ya está en uso'}), 409

    try:
        nuevo_stock = int(data.get('stock_total', anterior['stock_total']))
        cur.execute("""
           UPDATE productos SET
                sku=%s, nombre=%s, categoria=%s, stock_total=%s,
                precio_unitario=%s, venta_dia=%s, ubicacion_gondola=%s
            WHERE id=%s
        """, (nuevo_sku, nombre,
              data.get('categoria', anterior['categoria']),
              nuevo_stock,
              float(data.get('precio_unitario', anterior['precio_unitario'] or 0)),
              float(data.get('venta_dia', anterior['venta_dia'] or 0)),
              data.get('ubicacion_gondola', anterior['ubicacion_gondola'] or ''),
              prod_id))
        if nuevo_stock != anterior['stock_total']:
            registrar_historial(conn, prod_id, 'UPDATE',
                                'stock_total', anterior['stock_total'], nuevo_stock,
                                f'Edición desde catálogo por {session.get("nombre")}')
        conn.commit()
        return jsonify({'success': True, 'message': 'Producto actualizado'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/productos/<int:prod_id>', methods=['DELETE'])
@requiere_rol('gerente')
def api_eliminar_producto(prod_id):
    conn = get_db()
    if not conn:
        return jsonify({'success': False}), 500
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT nombre FROM productos WHERE id=%s", (prod_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'message': 'No encontrado'}), 404
    try:
        cur.execute("UPDATE productos SET activo=0 WHERE id=%s", (prod_id,))
        cur.execute("UPDATE alertas_quiebre SET activo=0 WHERE producto_id=%s", (prod_id,))
        cur.execute("UPDATE segmentacion_inventario SET activo=0 WHERE producto_id=%s", (prod_id,))
        registrar_historial(conn, prod_id, 'DELETE',
                            motivo=f'Producto desactivado por {session.get("nombre")}')
        conn.commit()
        return jsonify({'success': True, 'message': 'Producto desactivado'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/productos/buscar-sku/<sku>', methods=['GET'])
@login_required
def api_buscar_sku(sku):
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Error BD'}), 500
    cur = conn.cursor(dictionary=True)
    cur.execute("""
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
    prod = cur.fetchone()
    conn.close()
    if not prod:
        return jsonify({'success': False, 'message': 'SKU no encontrado'}), 404
    return jsonify({'success': True, 'data': prod})


# ════════════════════════════════════════════════════════════
# API — CONTEOS MANUALES  (desde el escáner)
# ════════════════════════════════════════════════════════════
@app.route('/api/conteos', methods=['POST'])
@login_required
def api_crear_conteo():
    data       = request.get_json() or {}
    prod_id    = data.get('producto_id')
    contado    = data.get('stock_contado')
    motivo     = data.get('motivo', '')

    if prod_id is None or contado is None:
        return jsonify({'success': False, 'message': 'producto_id y stock_contado son requeridos'}), 400

    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Error BD'}), 500
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT stock_total FROM productos WHERE id=%s AND activo=1", (prod_id,))
    prod = cur.fetchone()
    if not prod:
        conn.close()
        return jsonify({'success': False, 'message': 'Producto no encontrado'}), 404

    stock_sistema = prod['stock_total']
    try:
        cur.execute("""
            INSERT INTO conteos_manuales
                (producto_id, usuario_id, stock_sistema, stock_contado, motivo, estado)
            VALUES (%s, %s, %s, %s, %s, 'aplicado')
        """, (prod_id, session['usuario_id'], stock_sistema, int(contado), motivo))

        # Actualizar stock_total del producto con el valor contado
        cur.execute("UPDATE productos SET stock_total=%s WHERE id=%s", (int(contado), prod_id))

        registrar_historial(conn, prod_id, 'CONTEO',
                            'stock_total', stock_sistema, contado,
                            motivo or 'Conteo manual desde escáner')
        conn.commit()
        return jsonify({'success': True, 'message': 'Conteo registrado'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

# ════════════════════════════════════════════════════════════
# API — SEGMENTACIONES  (CRUD completo)
# ════════════════════════════════════════════════════════════
@app.route('/api/segmentaciones', methods=['GET'])
@login_required
def api_get_segmentaciones():
    conn = get_db()
    if not conn:
        return jsonify({'success': False}), 500
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT s.*, p.nombre, p.sku, p.stock_total
        FROM segmentacion_inventario s
        JOIN productos p ON s.producto_id = p.id
        ORDER BY s.fecha_creacion DESC
    """)
    data = cur.fetchall()
    conn.close()
    return jsonify({'success': True, 'data': data})

@app.route('/api/segmentaciones', methods=['POST'])
@requiere_rol('supervisor', 'gerente')
def api_crear_segmentacion():
    data = request.get_json() or {}
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Error BD'}), 500

    producto_id      = data.get('producto_id')
    stock_final      = int(data.get('stock_final', 0))
    stock_revendedor = int(data.get('stock_revendedor', 0))
    motivo           = data.get('motivo', '')

    # Validación: no superar stock total
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT stock_total FROM productos WHERE id=%s", (producto_id,))
    prod = cur.fetchone()
    if not prod:
        conn.close()
        return jsonify({'success': False, 'message': 'Producto no encontrado'}), 404
    if stock_final + stock_revendedor > prod['stock_total']:
        conn.close()
        return jsonify({'success': False,
                        'message': f"Total asignado ({stock_final + stock_revendedor}) "
                                   f"supera el stock disponible ({prod['stock_total']})"}), 400
    try:
        cur.execute("""
            INSERT INTO segmentacion_inventario
                (producto_id, usuario_id, stock_cliente_final, stock_revendedor,
                 limite_compra_final, limite_compra_revendedor, motivo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (producto_id, session.get('usuario_id'),
              stock_final, stock_revendedor,
              data.get('limite_compra_final', 0),
              data.get('limite_compra_revendedor', 0), motivo))
        registrar_historial(conn, producto_id, 'CREATE', motivo=motivo)
        conn.commit()
        return jsonify({'success': True, 'message': 'Segmentación creada correctamente'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/segmentaciones/<int:seg_id>', methods=['PUT'])
@requiere_rol('supervisor', 'gerente')
def api_actualizar_segmentacion(seg_id):
    data = request.get_json() or {}
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Error BD'}), 500

    stock_final      = int(data.get('stock_final', 0))
    stock_revendedor = int(data.get('stock_revendedor', 0))
    motivo           = data.get('motivo', '')

    cur = conn.cursor(dictionary=True)
    # Obtener datos anteriores para historial
    cur.execute("""
        SELECT s.*, p.stock_total FROM segmentacion_inventario s
        JOIN productos p ON s.producto_id = p.id WHERE s.id=%s
    """, (seg_id,))
    anterior = cur.fetchone()
    if not anterior:
        conn.close()
        return jsonify({'success': False, 'message': 'Registro no encontrado'}), 404

    if stock_final + stock_revendedor > anterior['stock_total']:
        conn.close()
        return jsonify({'success': False,
                        'message': f"Total ({stock_final + stock_revendedor}) supera stock ({anterior['stock_total']})"}), 400
    try:
        cur.execute("""
            UPDATE segmentacion_inventario
            SET stock_cliente_final=%s, stock_revendedor=%s,
                limite_compra_final=%s, limite_compra_revendedor=%s,
                motivo=%s, usuario_id=%s, updated_at=NOW()
            WHERE id=%s
        """, (stock_final, stock_revendedor,
              data.get('limite_compra_final', anterior['limite_compra_final']),
              data.get('limite_compra_revendedor', anterior['limite_compra_revendedor']),
              motivo, session.get('usuario_id'), seg_id))

        registrar_historial(conn, anterior['producto_id'], 'UPDATE',
                            'stock_cliente_final',
                            anterior['stock_cliente_final'], stock_final, motivo)
        conn.commit()
        return jsonify({'success': True, 'message': 'Actualizado correctamente'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/segmentaciones/<int:seg_id>', methods=['DELETE'])
@requiere_rol('gerente')
def api_eliminar_segmentacion(seg_id):
    conn = get_db()
    if not conn:
        return jsonify({'success': False}), 500
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT producto_id FROM segmentacion_inventario WHERE id=%s", (seg_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'message': 'No encontrado'}), 404
    try:
        registrar_historial(conn, row['producto_id'], 'DELETE',
                            motivo=f'Eliminado por {session.get("nombre")}')
        cur.execute("DELETE FROM segmentacion_inventario WHERE id=%s", (seg_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Eliminado correctamente'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/segmentaciones/<int:seg_id>/toggle', methods=['PATCH'])
@requiere_rol('supervisor', 'gerente')
def api_toggle_segmentacion(seg_id):
    conn = get_db()
    if not conn:
        return jsonify({'success': False}), 500
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT producto_id, activo FROM segmentacion_inventario WHERE id=%s", (seg_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'message': 'No encontrado'}), 404
    nuevo_estado = 0 if row['activo'] else 1
    cur.execute("UPDATE segmentacion_inventario SET activo=%s WHERE id=%s", (nuevo_estado, seg_id))
    registrar_historial(conn, row['producto_id'], 'TOGGLE',
                        'activo', row['activo'], nuevo_estado)
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'activo': nuevo_estado})

# ════════════════════════════════════════════════════════════
# API — ALERTAS
# ════════════════════════════════════════════════════════════
@app.route('/api/alertas', methods=['GET'])
@login_required
def api_get_alertas():
    conn = get_db()
    if not conn:
        return jsonify({'success': False}), 500
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM v_alertas_activas")
    data = cur.fetchall()
    conn.close()
    return jsonify({'success': True, 'data': data})

@app.route('/api/alertas/<int:alerta_id>', methods=['DELETE'])
@requiere_rol('supervisor', 'gerente')
def api_eliminar_alerta(alerta_id):
    conn = get_db()
    if not conn:
        return jsonify({'success': False}), 500
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT producto_id FROM alertas_quiebre WHERE id=%s", (alerta_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'message': 'No encontrado'}), 404
    cur.execute("UPDATE alertas_quiebre SET activo=0 WHERE id=%s", (alerta_id,))
    registrar_historial(conn, row['producto_id'], 'DELETE',
                        motivo='Alerta descartada manualmente')
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Alerta eliminada'})

# ════════════════════════════════════════════════════════════
# API — HISTORIAL
# ════════════════════════════════════════════════════════════
@app.route('/api/historial', methods=['GET'])
@login_required
def api_get_historial():
    conn = get_db()
    if not conn:
        return jsonify({'success': False}), 500
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM v_historial_completo LIMIT 200")
    data = cur.fetchall()
    conn.close()
    # Convertir datetime a string
    for row in data:
        if isinstance(row.get('fecha'), datetime):
            row['fecha'] = row['fecha'].strftime('%d/%m/%Y %H:%M')
    return jsonify({'success': True, 'data': data})


# ════════════════════════════════════════════════════════════
# FASE 3 — Cambio de contraseña desde Perfil
# ════════════════════════════════════════════════════════════
@app.route('/api/perfil/cambiar-clave', methods=['POST'])
@login_required
def api_cambiar_clave():
    from werkzeug.security import generate_password_hash
    data         = request.get_json() or {}
    clave_actual = data.get('clave_actual', '')
    clave_nueva  = data.get('clave_nueva',  '')

    # Validaciones backend (segunda línea de defensa)
    if not clave_actual or not clave_nueva:
        return jsonify({'success': False, 'message': 'Ambas claves son requeridas'}), 400
    if len(clave_nueva) < 8:
        return jsonify({'success': False, 'message': 'La nueva clave debe tener al menos 8 caracteres'}), 400
    if not any(c.isdigit() for c in clave_nueva):
        return jsonify({'success': False, 'message': 'La nueva clave debe contener al menos un número'}), 400
    if clave_actual == clave_nueva:
        return jsonify({'success': False, 'message': 'La nueva clave debe ser diferente a la actual'}), 400

    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Error de BD'}), 500

    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT password_hash FROM usuarios WHERE id=%s AND activo=1",
                (session['usuario_id'],))
    usuario = cur.fetchone()

    if not usuario:
        conn.close()
        return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404

    # Verificar clave actual
    if not check_password_hash(usuario['password_hash'], clave_actual):
        conn.close()
        return jsonify({'success': False, 'message': 'La contraseña actual es incorrecta'}), 403

    # Guardar nuevo hash
    nuevo_hash = generate_password_hash(clave_nueva)
    try:
        cur.execute("UPDATE usuarios SET password_hash=%s WHERE id=%s",
                    (nuevo_hash, session['usuario_id']))
        conn.commit()
        return jsonify({'success': True, 'message': 'Contraseña actualizada correctamente'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()


# ════════════════════════════════════════════════════════════
# FASE 4 — Exportación CSV del historial
# ════════════════════════════════════════════════════════════
@app.route('/historial/exportar', methods=['GET'])
@login_required
def exportar_historial_csv():
    import csv
    import io
    from flask import Response

    conn = get_db()
    if not conn:
        return "Error de base de datos", 500

    cur = conn.cursor(dictionary=True)
    # Soporte para filtrar por acción si se pasa ?accion=UPDATE
    accion = request.args.get('accion', '').strip().upper()
    if accion:
        cur.execute(
            "SELECT * FROM v_historial_completo WHERE accion=%s ORDER BY fecha DESC LIMIT 1000",
            (accion,)
        )
    else:
        cur.execute("SELECT * FROM v_historial_completo ORDER BY fecha DESC LIMIT 1000")

    registros = cur.fetchall()
    conn.close()

    # Construir CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)

    # Cabecera
    writer.writerow([
        'Fecha', 'Producto', 'SKU', 'Empleado', 'Rol Empleado',
        'Accion', 'Campo Modificado', 'Valor Anterior', 'Valor Nuevo', 'Motivo'
    ])

    for r in registros:
        fecha = r['fecha'].strftime('%d/%m/%Y %H:%M') if isinstance(r['fecha'], datetime) else str(r['fecha'])
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

    # Nombre de archivo con timestamp
    nombre_archivo = f"historial_tottus_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename="{nombre_archivo}"',
            'Content-Type': 'text/csv; charset=utf-8',
        }
    )

# ════════════════════════════════════════════════════════════
# FASE 4 — Exportación CSV del historial
# ════════════════════════════════════════════════════════════
@app.route('/historial/exportar', methods=['GET'])
@login_required
def exportar_historial_csv():
    import csv
    import io
    from flask import Response

    conn = get_db()
    if not conn:
        return "Error de base de datos", 500
    cur = conn.cursor(dictionary=True)
    accion = request.args.get('accion', '').strip().upper()
    if accion:
        cur.execute(
            "SELECT * FROM v_historial_completo WHERE accion=%s ORDER BY fecha DESC LIMIT 1000",
            (accion,)
        )
    else:
        cur.execute("SELECT * FROM v_historial_completo ORDER BY fecha DESC LIMIT 1000")

    registros = cur.fetchall()
    conn.close()

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

# ════════════════════════════════════════════════════════════
if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, port=5000)