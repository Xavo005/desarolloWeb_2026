# Manual del Programador: JWT + APIs — SGI DeyFarma

## 1. El Problema de Compatibilidad (Hotfix `collections.abc`)

### ¿Qué pasó?

`flask-jwt` usa `PyJWT 1.4.x`, una versión antigua. En **Python 3.10+**, el módulo `collections` eliminó acceso directo a clases de tipos abstractos como `Mapping`. Antes, todo el código Python podía hacer:

```python
from collections import Mapping  # Funcionaba en Python 3.9 e inferior
```

Desde Python 3.10, esas clases se movieron a un submódulo dedicado:

```python
from collections.abc import Mapping  # ✅ Correcto para Python 3.10+
```

### Archivos parchados

Se aplicó el fix en 4 archivos (sistema global y venv del proyecto):

| Archivo | Cambio |
|---|---|
| `site-packages/jwt/api_jwt.py` | `from collections import Mapping` → `from collections.abc import Mapping` |
| `site-packages/jwt/api_jws.py` | Mismo cambio |
| `venv/Lib/site-packages/jwt/api_jwt.py` | Mismo cambio |
| `venv/Lib/site-packages/jwt/api_jws.py` | Mismo cambio |

### Segundo fix: `_request_ctx_stack` eliminado en Flask 2.3

`flask-jwt` también usaba un objeto interno de Flask llamado `_request_ctx_stack` para guardar quién está logueado. Ese objeto fue eliminado en **Flask 2.3**. La solución es usar `flask.g` (el objeto de contexto de la petición):

```python
# ANTES (roto en Flask 2.3):
from flask import _request_ctx_stack
current_identity = LocalProxy(lambda: getattr(_request_ctx_stack.top, 'current_identity', None))
# ... y dentro de _jwt_required():
_request_ctx_stack.top.current_identity = identity

# DESPUÉS (correcto con Flask 2.3+):
from flask import g
current_identity = LocalProxy(lambda: getattr(g, 'current_identity', None))
# ... y dentro de _jwt_required():
g.current_identity = identity
```

### Tercer fix: `access_token.decode()` ya no es necesario

PyJWT ≥ 2.0 retorna el token como `str` en vez de `bytes`. El fix hace la decodificación condicional:

```python
# ANTES (roto con PyJWT moderno):
return jsonify({'access_token': access_token.decode('utf-8')})

# DESPUÉS (compatible con ambas versiones):
token = access_token.decode('utf-8') if isinstance(access_token, bytes) else access_token
return jsonify({'access_token': token})
```

---

## 2. Cómo Funciona JWT en el Proyecto

### 2.1 Inicialización (en `app.py`)

```python
# 1. Se importa JWT, el decorador y el proxy de identidad
from flask_jwt import JWT, jwt_required, current_identity

# 2. Función de autenticación: recibe usuario y contraseña, consulta la BD real
def authenticate(username, password):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, codigo_empleado, nombre, rol, password FROM usuarios WHERE codigo_empleado=%s AND activo=1",
                (username,)
            )
            row = cur.fetchone()
    if row and row.get('password') == password:
        return row   # Si coincide, devuelve el dict del usuario (esto se convierte en el 'identity')

# 3. Función de identidad: recibe el payload decodificado del token y busca el usuario en BD
def identity(payload):
    user_id = payload['identity']   # 'identity' es el campo que flask-jwt pone en el token
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, codigo_empleado, nombre, rol FROM usuarios WHERE id=%s AND activo=1",
                (user_id,)
            )
            return cur.fetchone()   # Retorna el usuario activo para esa petición

# 4. Se inicializa JWT vinculándolo a la app y las dos funciones
app = Flask(__name__)
app.secret_key = 'botica_sgi_secret_2026'
jwt = JWT(app, authenticate, identity)
# Esto registra automáticamente la ruta POST /auth para obtener el token
```

### 2.2 El decorador `@jwt_required()`

Cada endpoint protegido tiene este decorador encima:

```python
@app.route('/api_leer_productos_jwt', methods=['GET'])
@jwt_required()   # <--- Este decorador detiene la petición si no hay un token válido
def api_leer_productos_jwt():
    resultado = leer_productos()
    return jsonify({"code": 1, "data": resultado})
```

**¿Qué hace internamente?**
1. Lee el header `Authorization` de la petición HTTP.
2. Extrae el token: `Authorization: JWT <el_token_aqui>`.
3. Verifica la firma criptográfica del token con la `secret_key`.
4. Verifica que el token no esté expirado (el tiempo de expiración por defecto es 5 minutos).
5. Si todo es válido, llama a la función `identity(payload)` para cargar el usuario en `g.current_identity`.
6. Si algo falla, retorna automáticamente HTTP 401 (No autorizado).

### 2.3 Flujo completo en Postman

```
1. POST http://localhost:5000/auth
   Body (JSON): {"username": "E001", "password": "Tottus2026"}
   Respuesta:   {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}

2. Copiar el access_token

3. Cualquier endpoint protegido:
   GET http://localhost:5000/api_leer_productos_jwt
   Header: Authorization: JWT eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   Respuesta: {"code": 1, "data": [...]}
```

---

## 3. Tabla Completa de Endpoints JWT

### 🔓 Endpoint Público (obtener token)

| Método | Ruta | Body | Descripción |
|---|---|---|---|
| POST | `/auth` | `{"username": "E001", "password": "clave"}` | Retorna el JWT |

### 🔒 Endpoints Protegidos — PRODUCTOS

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api_guardar_producto_jwt` | Insertar nuevo producto |
| POST | `/api_actualizar_producto` | Modificar producto existente |
| POST | `/api_eliminar_producto` | Desactivar producto (soft delete) |
| GET/POST | `/api_leer_productoxid` | Leer un producto por su ID |
| GET | `/api_leer_productos_jwt` | Leer todos los productos |

### 🔒 Endpoints Protegidos — ALERTAS

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api_guardar_alerta` | Registrar nueva alerta |
| POST | `/api_actualizar_alerta` | Modificar alerta existente |
| POST | `/api_eliminar_alerta` | Eliminar alerta |
| GET/POST | `/api_leer_alertaxid` | Leer una alerta por ID |
| GET | `/api_leer_alertas_jwt` | Leer todas las alertas activas |

### 🔒 Endpoints Protegidos — SEGMENTACION

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api_guardar_segmentacion_jwt` | Registrar nueva segmentación |
| POST | `/api_actualizar_segmentacion` | Modificar segmentación |
| POST | `/api_eliminar_segmentacion` | Eliminar segmentación |
| GET/POST | `/api_leer_segmentacionxid` | Leer segmentación por ID |
| GET | `/api_leer_segmentaciones_jwt` | Leer todas las segmentaciones |

### 🔒 Endpoints Protegidos — HISTORIAL

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api_guardar_historial` | Registrar entrada en historial |
| POST | `/api_actualizar_historial` | Modificar motivo de un registro |
| POST | `/api_eliminar_historial` | Eliminar registro del historial |
| GET/POST | `/api_leer_historialxid` | Leer registro por ID |
| GET | `/api_leer_historial_jwt` | Leer los últimos 200 registros |

### 🔒 Endpoints Protegidos — USUARIOS/TRABAJADORES

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api_guardar_usuario_jwt` | Registrar nuevo trabajador |
| POST | `/api_actualizar_usuario` | Modificar datos de trabajador |
| POST | `/api_eliminar_usuario` | Desactivar trabajador |
| GET/POST | `/api_leer_usuarioxid` | Leer trabajador por ID |
| GET | `/api_leer_usuarios_jwt` | Leer todos los trabajadores |

---

## 4. Colección Postman v2.1

Copia el siguiente JSON completo y guárdalo como `sgi_deyfarma.postman_collection.json`. Luego en Postman: **Import → File → selecciona el archivo**.

```json
{
  "info": {
    "name": "SGI DeyFarma — API JWT",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    { "key": "base_url", "value": "http://localhost:5000" },
    { "key": "token", "value": "PEGAR_TOKEN_AQUI" }
  ],
  "item": [
    {
      "name": "1. Obtener Token JWT",
      "request": {
        "method": "POST",
        "header": [{ "key": "Content-Type", "value": "application/json" }],
        "url": "{{base_url}}/auth",
        "body": { "mode": "raw", "raw": "{\"username\": \"E001\", \"password\": \"Tottus2026\"}" }
      }
    },
    {
      "name": "PRODUCTOS",
      "item": [
        { "name": "Guardar Producto", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_guardar_producto_jwt", "body": { "mode": "raw", "raw": "{\"sku\": \"MED-001\", \"nombre\": \"Paracetamol 500mg\", \"categoria\": \"Analgesicos\", \"stock_total\": 100, \"precio_unitario\": 0.50, \"venta_dia\": 10, \"ubicacion_gondola\": \"A1\"}" } } },
        { "name": "Actualizar Producto", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_actualizar_producto", "body": { "mode": "raw", "raw": "{\"id\": 1, \"sku\": \"MED-001\", \"nombre\": \"Paracetamol 500mg\", \"categoria\": \"Analgesicos\", \"stock_total\": 120, \"precio_unitario\": 0.55, \"venta_dia\": 12, \"ubicacion_gondola\": \"A1\"}" } } },
        { "name": "Eliminar Producto", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_eliminar_producto", "body": { "mode": "raw", "raw": "{\"id\": 1}" } } },
        { "name": "Leer Producto por ID", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_leer_productoxid", "body": { "mode": "raw", "raw": "{\"id\": 1}" } } },
        { "name": "Listar Todos los Productos", "request": { "method": "GET", "header": [{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_leer_productos_jwt" } }
      ]
    },
    {
      "name": "ALERTAS",
      "item": [
        { "name": "Guardar Alerta", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_guardar_alerta", "body": { "mode": "raw", "raw": "{\"producto_id\": 1, \"sku\": \"MED-001\", \"producto\": \"Paracetamol\", \"categoria\": \"Analgesicos\", \"venta_dia\": 10, \"stock_minimo\": 20, \"estado_transf\": \"pendiente\"}" } } },
        { "name": "Actualizar Alerta", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_actualizar_alerta", "body": { "mode": "raw", "raw": "{\"id\": 1, \"unidades\": 15, \"venta_dia\": 8, \"estado_transf\": \"en_transito\", \"stock_minimo\": 20}" } } },
        { "name": "Eliminar Alerta", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_eliminar_alerta", "body": { "mode": "raw", "raw": "{\"id\": 1}" } } },
        { "name": "Leer Alerta por ID", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_leer_alertaxid", "body": { "mode": "raw", "raw": "{\"id\": 1}" } } },
        { "name": "Listar Todas las Alertas", "request": { "method": "GET", "header": [{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_leer_alertas_jwt" } }
      ]
    },
    {
      "name": "SEGMENTACION",
      "item": [
        { "name": "Guardar Segmentacion", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_guardar_segmentacion_jwt", "body": { "mode": "raw", "raw": "{\"producto_id\": 1, \"stock_cliente_final\": 50, \"stock_revendedor\": 30, \"limite_compra_final\": 5, \"limite_compra_revendedor\": 20, \"motivo\": \"Control inicial\"}" } } },
        { "name": "Actualizar Segmentacion", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_actualizar_segmentacion", "body": { "mode": "raw", "raw": "{\"id\": 1, \"stock_cliente_final\": 60, \"stock_revendedor\": 40, \"limite_compra_final\": 5, \"limite_compra_revendedor\": 25, \"motivo\": \"Ajuste de stock\"}" } } },
        { "name": "Eliminar Segmentacion", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_eliminar_segmentacion", "body": { "mode": "raw", "raw": "{\"id\": 1}" } } },
        { "name": "Leer Segmentacion por ID", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_leer_segmentacionxid", "body": { "mode": "raw", "raw": "{\"id\": 1}" } } },
        { "name": "Listar Todas las Segmentaciones", "request": { "method": "GET", "header": [{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_leer_segmentaciones_jwt" } }
      ]
    },
    {
      "name": "HISTORIAL",
      "item": [
        { "name": "Guardar Historial", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_guardar_historial", "body": { "mode": "raw", "raw": "{\"producto_id\": 1, \"accion\": \"UPDATE\", \"campo\": \"stock_total\", \"valor_anterior\": \"100\", \"valor_nuevo\": \"120\", \"motivo\": \"Reposicion de stock\"}" } } },
        { "name": "Actualizar Historial", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_actualizar_historial", "body": { "mode": "raw", "raw": "{\"id\": 1, \"motivo\": \"Corrección de motivo\"}" } } },
        { "name": "Eliminar Historial", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_eliminar_historial", "body": { "mode": "raw", "raw": "{\"id\": 1}" } } },
        { "name": "Leer Historial por ID", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_leer_historialxid", "body": { "mode": "raw", "raw": "{\"id\": 1}" } } },
        { "name": "Listar Todo el Historial", "request": { "method": "GET", "header": [{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_leer_historial_jwt" } }
      ]
    },
    {
      "name": "USUARIOS",
      "item": [
        { "name": "Guardar Usuario", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_guardar_usuario_jwt", "body": { "mode": "raw", "raw": "{\"nombre\": \"Juan Perez\", \"codigo_empleado\": \"E099\", \"email\": \"juan@deyfarma.com\", \"sede\": \"chiclayo\", \"rol\": \"operario\", \"password\": \"Tottus2026\"}" } } },
        { "name": "Actualizar Usuario", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_actualizar_usuario", "body": { "mode": "raw", "raw": "{\"id\": 1, \"nombre\": \"Juan Perez Actualizado\", \"codigo_empleado\": \"E099\", \"email\": \"juan2@deyfarma.com\", \"sede\": \"chiclayo\", \"rol\": \"gerente\", \"password\": \"Tottus2026\"}" } } },
        { "name": "Eliminar Usuario", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_eliminar_usuario", "body": { "mode": "raw", "raw": "{\"id\": 99}" } } },
        { "name": "Leer Usuario por ID", "request": { "method": "POST", "header": [{"key": "Content-Type","value": "application/json"},{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_leer_usuarioxid", "body": { "mode": "raw", "raw": "{\"id\": 1}" } } },
        { "name": "Listar Todos los Usuarios", "request": { "method": "GET", "header": [{"key": "Authorization","value": "JWT {{token}}"}], "url": "{{base_url}}/api_leer_usuarios_jwt" } }
      ]
    }
  ]
}
```
