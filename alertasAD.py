import pymysql.cursors

class clsAlertaQuiebre:
    def __init__(self, p_producto, p_sku, p_categoria, p_unidades, 
                 p_venta_dia, p_horas_restantes, p_estado_transf):
        self.producto = p_producto
        self.sku = p_sku
        self.categoria = p_categoria
        self.unidades = p_unidades
        self.venta_dia = p_venta_dia
        self.horas_restantes = p_horas_restantes
        self.estado_transf = p_estado_transf

def obtenerconexion():
    try:
        connection = pymysql.connect(host='localhost',
                                    user='root',
                                    password='',
                                    database='avance', 
                                    cursorclass=pymysql.cursors.DictCursor)
        return connection
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def listar_alertas_quiebre():
    lista = []
    try:
        conn = obtenerconexion()
        if conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM alertas_quiebre ORDER BY horas_restantes ASC"
                cursor.execute(sql)
                resultados = cursor.fetchall()
                for r in resultados:
                    obj = clsAlertaQuiebre(r['producto'], r['sku'], r['categoria'], 
                                           r['unidades'], r['venta_dia'], 
                                           r['horas_restantes'], r['estado_transf'])
                    lista.append(obj)
            conn.close()
    except Exception as e:
        print(f"Error al recuperar alertas: {repr(e)}")
    return lista