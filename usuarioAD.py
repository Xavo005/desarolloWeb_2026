from bd import obtenerconexion

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

def insertar_trabajador(p_trabajador):
    try:
        conn = obtenerconexion()
        if not conn: 
            return False
        
        with conn:
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
        print(f"Error en insertar_trabajador: {str(e)}")
        return False

def actualizar_trabajador(p_trabajador):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql  = " UPDATE `usuarios` "
                    sql += "    SET `nombre` = %s, `codigo_empleado` = %s, "
                    sql += "        `email` = %s, `sede` = %s, "
                    sql += "        `rol` = %s, `palabra_clave` = %s "
                    sql += "  WHERE `id` = %s "
                    
                    cursor.execute(sql, (
                        p_trabajador.nombre, 
                        p_trabajador.codigo_empleado, 
                        p_trabajador.email or '', 
                        p_trabajador.sede or 'chiclayo', 
                        p_trabajador.rol or 'operario', 
                        p_trabajador.palabra_clave or '', 
                        p_trabajador.id
                    ))
                    
                    if p_trabajador.password:
                        cursor.execute("UPDATE `usuarios` SET `password` = %s WHERE `id` = %s", (p_trabajador.password, p_trabajador.id))
                        
                conn.commit()
            return True
        return False
    except Exception as e:
        print(f"Error en actualizar_trabajador: {repr(e)}")
        return False

def eliminar_trabajador(p_id):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE `usuarios` SET `activo` = 0 WHERE `id` = %s", (p_id,))
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False

def cambiar_contrasena(p_trabajador_id, p_clave_actual, p_nueva_clave):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = " SELECT id, password FROM usuarios WHERE id = %s AND activo = 1 "
                    cursor.execute(sql, (p_trabajador_id,))
                    row = cursor.fetchone()
                    if not row: return False
                    pwd_bd = row.get('password') if isinstance(row, dict) else row[1]
                    if pwd_bd != p_clave_actual: return False
                    cursor.execute("UPDATE `usuarios` SET `password` = %s WHERE `id` = %s", (p_nueva_clave, p_trabajador_id))
                conn.commit()
            return True
        return False
    except Exception as e:
        print(f"Error en cambiar_contrasena: {repr(e)}")
        return False

def restablecer_contrasena(p_codigo_empleado, p_palabra_clave, p_nueva_clave):
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  " SELECT id, palabra_clave FROM usuarios WHERE codigo_empleado = %s AND activo = 1 "
                    cursor.execute(sql, (p_codigo_empleado,))
                    row = cursor.fetchone()
                    if not row or row['palabra_clave'] != p_palabra_clave: return False
                    cursor.execute("UPDATE `usuarios` SET `password` = %s WHERE `id` = %s", (p_nueva_clave, row['id']))
                conn.commit()
            return True
        return False
    except Exception as e:
        print(repr(e))
        return False