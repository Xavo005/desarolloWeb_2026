from flask import Blueprint, jsonify
from bd import obtenerconexion

api_bp = Blueprint('api_bp', __name__)

@api_bp.route('/api/productos', methods=['GET'])
def get_productos():
    try:
        conn = obtenerconexion()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM productos")
            resultado = cursor.fetchall()
        conn.close()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500