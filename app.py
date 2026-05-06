from flask import Flask, render_template, request, jsonify
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)


DB_CONFIG = {
    'host': 'localhost',
    'database': 'tottus_inventory',
    'user': 'root',
    'password': ''  # En XAMPP suele ser vacío
}

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error de conexión: {e}")
        return None



@app.route('/')
def index():
    return render_template('segmentacion.html')

@app.route('/api/productos', methods=['GET'])
def get_productos():
    conn = get_connection()
    if not conn: return jsonify({'success': False, 'message': 'Error de BD'}), 500
    
    cursor = conn.cursor(dictionary=True)
    q = request.args.get('q', '')
    
    query = "SELECT * FROM productos"
    if q:
        query += " WHERE nombre LIKE %s OR sku LIKE %s"
        cursor.execute(query, (f"%{q}%", f"%{q}%"))
    else:
        cursor.execute(query)
        
    productos = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'success': True, 'data': productos})

@app.route('/api/segmentaciones', methods=['GET'])
def get_segmentaciones():
    conn = get_connection()
    if not conn: return jsonify({'success': False}), 500
    
    cursor = conn.cursor(dictionary=True)
    # Hacemos un JOIN para traer el nombre y sku del producto
    query = """
        SELECT s.*, p.nombre, p.sku 
        FROM segmentacion_inventario s
        JOIN productos p ON s.producto_id = p.id
        ORDER BY s.fecha_creacion DESC
    """
    cursor.execute(query)
    segmentaciones = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'success': True, 'data': segmentaciones})

@app.route('/api/segmentaciones', methods=['POST'])
def crear_segmentacion():
    data = request.get_json()
    conn = get_connection()
    if not conn: return jsonify({'success': False, 'message': 'Error BD'}), 500
    
    try:
        cursor = conn.cursor()
        # Nota: Los nombres aquí deben ser los mismos de tu tabla en phpMyAdmin
        query = """
            INSERT INTO segmentacion_inventario 
            (producto_id, stock_cliente_final, stock_revendedor, limite_compra_final, limite_compra_revendedor, motivo)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        valores = (
            data['producto_id'], 
            data['stock_final'], 
            data['stock_revendedor'],
            data.get('limite_compra_final', 0), 
            data.get('limite_compra_revendedor', 0),
            data.get('motivo', '')
        )
        cursor.execute(query, valores)
        conn.commit() # ¡IMPORTANTE! Sin esto MySQL no guarda los cambios
        return jsonify({'success': True, 'message': 'Guardado correctamente'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/segmentaciones/<int:seg_id>/toggle', methods=['PATCH'])
def toggle_segmentacion(seg_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Cambiamos el estado (si es 1 pasa a 0, si es 0 pasa a 1)
    query = "UPDATE segmentacion_inventario SET activo = NOT activo WHERE id = %s"
    cursor.execute(query, (seg_id,))
    conn.commit()
    
    cursor.close()
    conn.close()
    return jsonify({'success': True, 'message': 'Estado actualizado'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)