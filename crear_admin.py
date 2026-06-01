"""
crear_admin.py
Ejecuta UNA SOLA VEZ después de importar bd_appinventario.sql
Crea el usuario admin con contraseña hasheada correctamente.

Uso:  python crear_admin.py
"""
import os
import mysql.connector
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

ADMIN = {
    'codigo_empleado': 'ADMIN-001',
    'nombre':          'Administrador Sistema',
    'email':           'admin@tottus.com.pe',
    'password':        'tottus2026',
    'rol':             'gerente',
    'sede':            'Chiclayo - Mall Aventura',
}

def main():
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'tottus_sgi'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
    )
    cursor = conn.cursor()

    # Verificar si ya existe
    cursor.execute("SELECT id FROM usuarios WHERE codigo_empleado = %s", (ADMIN['codigo_empleado'],))
    if cursor.fetchone():
        print("⚠️  El admin ya existe. No se duplicó.")
    else:
        pwd_hash = generate_password_hash(ADMIN['password'])
        cursor.execute("""
            INSERT INTO usuarios (codigo_empleado, nombre, email, password_hash, rol, sede)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (ADMIN['codigo_empleado'], ADMIN['nombre'], ADMIN['email'],
              pwd_hash, ADMIN['rol'], ADMIN['sede']))
        conn.commit()
        print("✅ Admin creado:")
        print(f"   Código: {ADMIN['codigo_empleado']}")
        print(f"   Clave:  {ADMIN['password']}")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
