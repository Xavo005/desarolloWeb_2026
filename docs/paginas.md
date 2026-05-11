# 📄 Documentación de Páginas — Tottus SGI

Sistema Gerencial de Inventario · Sprint 1 · Flask + MySQL/XAMPP

---

## Índice
1. [Login](#1-login)
2. [Dashboard](#2-dashboard)
3. [Alertas Operativas](#3-alertas-operativas)
4. [Segmentación / Productos](#4-segmentación--productos)
5. [Historial de Ajustes](#5-historial-de-ajustes)
6. [Perfil de Usuario](#6-perfil-de-usuario)
7. [Componentes Globales](#7-componentes-globales-base)

---

## 1. Login
**Ruta:** `/login`  
**Archivo:** `templates/login.html`  
**Acceso:** Público (no requiere sesión)

### Funcionalidad
Punto de entrada del sistema. Autentica al usuario mediante su código de empleado y contraseña. Al ingresar correctamente, inicia una sesión Flask con `usuario_id`, `nombre`, `rol` y `sede`.

### Campos del formulario
| Campo | Tipo | Descripción |
|---|---|---|
| Código de Empleado | `text` | Formato `EMP-XXXX-XXX` |
| Contraseña | `password` | Hash verificado con werkzeug |
| Recordarme | `checkbox` | UI only (Sprint 2) |

### Lógica de autenticación (app.py)
```
POST /login
  → Consulta usuarios WHERE codigo_empleado = %s AND activo = 1
  → check_password_hash(hash, clave)
  → Si OK: session['usuario_id'], session['rol'], session['nombre']
  → Redirige a /dashboard
  → Si falla: muestra error inline (no expone si el código o la clave son incorrectos)
```

### Diseño responsive
- **Móvil (390px):** Card blanca centrada sobre fondo gris.
- **PC (1440px):** Split-screen. Lado izquierdo verde `#00A34D` con logo; derecho con formulario.

### Seguridad aplicada
- Contraseña hasheada con `pbkdf2:sha256` (werkzeug).
- `session.clear()` antes de crear la nueva sesión.
- Actualiza `ultimo_login` en BD al ingresar.

---

## 2. Dashboard
**Ruta:** `/dashboard`  
**Archivo:** `templates/dashboard.html`  
**Acceso:** Requiere login (`@login_required`)  
**TabBar activo:** 🏠 Inicio

### Funcionalidad
Vista principal post-login. Muestra el estado general del inventario de la sede asignada al empleado, incluyendo métricas críticas y accesos rápidos a las funciones más usadas.

### Datos mostrados
| Sección | Fuente de datos | Descripción |
|---|---|---|
| Saludo + sede | `session` | Nombre del empleado y sede asignada |
| Quiebres activos | `alertas_quiebre WHERE nivel='critico'` | Conteo de alertas críticas |
| Total productos | `productos WHERE activo=1` | Inventario total |
| Alertas urgentes | `contar_alertas()` | Badge del header |
| Alertas recientes | `alertas_quiebre ORDER BY horas_restantes LIMIT 3` | Top 3 más urgentes |

### Accesos rápidos (Quick Access Grid)
- 📷 **Escanear Producto** → `/segmentacion`
- 🔔 **Ver Alertas** → `/alertas`
- 📋 **Historial** → `/historial`
- 👤 **Mi Perfil** → `/perfil`

### Banner de alerta
Si hay alertas urgentes, aparece un banner ámbar: *"N productos en riesgo de quiebre"* con enlace a `/alertas`.

### Reloj dinámico
JavaScript actualiza la fecha y hora cada 60 segundos sin recargar la página.

---

## 3. Alertas Operativas
**Ruta:** `/alertas`  
**Archivo:** `templates/alertas.html`  
**Acceso:** Requiere login  
**TabBar activo:** 🔔 Alertas

### Funcionalidad
Panel de control de quiebres de inventario. Cada alerta representa un producto cuyo stock está en riesgo de agotarse. Incluye operaciones CRUD completas.

### Datos mostrados
Fuente: `VIEW v_alertas_activas` (JOIN de `alertas_quiebre` + `productos`), ordenadas por `horas_restantes ASC`.

### AlertCard — componente por producto
Cada tarjeta muestra:
- **Nombre + SKU** del producto
- **Categoría** (badge gris)
- **3 métricas:** unidades actuales · ventas/día · horas restantes
- **Barra de progreso** coloreada según nivel:
  - 🔴 `critico` → rojo  (< 24h)
  - 🟠 `urgente` → ámbar (< 72h)
  - 🔵 `advertencia` → azul (< 120h)
  - 🟢 `ok` → verde
- **Estado de transferencia** (texto informativo)

### ⚠️ Botones CRUD (corrección de auditoría)
Presentes en **cada tarjeta**:
| Botón | Color | Acción |
|---|---|---|
| `✏️ Editar` | Ámbar `#FFB300` | Redirige a `/segmentacion?alerta_id=N` |
| `🗑️ Eliminar` | Rojo `#D32F2F` | Llama `DELETE /api/alertas/{id}` con modal de confirmación |

### Estadísticas superiores
Grid de 3 tarjetas con conteo de alertas por nivel (crítico / urgente / ok). Fuente: `GROUP BY nivel`.

### Empty State
Si no hay alertas: pantalla con ícono de check verde y mensaje *"¡Todo en orden! No hay alertas de quiebre activas."*

### API consumida
```
GET  /api/alertas          → lista completa (v_alertas_activas)
DELETE /api/alertas/{id}   → desactiva alerta (activo=0) + registra en historial
```

---

## 4. Segmentación / Productos
**Ruta:** `/segmentacion`  
**Archivo:** `templates/segmentacion.html`  
**Acceso:** Requiere login  
**TabBar activo:** 📦 Productos

### Funcionalidad
Módulo central de gestión de inventario. Permite crear, editar, activar/desactivar y eliminar reglas de segmentación que distribuyen el stock entre clientes finales y revendedores.

### Formulario de Ajuste (parte superior)
| Campo | Descripción |
|---|---|
| Producto | Dropdown dinámico cargado desde `/api/productos` |
| Stock Cliente Final | Unidades asignadas a clientes finales |
| Stock Revendedor | Unidades asignadas a revendedores |
| Límite por Cliente | Máximo de unidades por compra (cliente final) |
| Límite por Revendedor | Máximo de unidades por compra (revendedor) |
| Motivo | Justificación del ajuste (texto libre) |

### Validación en tiempo real
Al cambiar los valores de stock, un contador muestra:  
*"Usando: X + Y = Z / N disponibles"*  
Si Z > N → advertencia roja y el formulario no envía.

### Tabla de segmentaciones activas
Lista todas las reglas activas con columnas: Producto/SKU · Stock CF · Stock Rev · Límites · Estado · Acciones.

### ⚠️ CRUD completo
| Operación | Endpoint | Rol requerido |
|---|---|---|
| CREATE (nueva regla) | `POST /api/segmentaciones` | supervisor, gerente |
| READ (lista) | `GET /api/segmentaciones` | cualquiera |
| UPDATE (editar) | `PUT /api/segmentaciones/{id}` | supervisor, gerente |
| DELETE (eliminar) | `DELETE /api/segmentaciones/{id}` | **solo gerente** |
| TOGGLE (activar/desactivar) | `PATCH /api/segmentaciones/{id}/toggle` | supervisor, gerente |

### Registro automático en historial
Cada operación CUD llama internamente a `registrar_historial()` que guarda: quién · qué · cuándo · valor anterior → nuevo.

---

## 5. Historial de Ajustes
**Ruta:** `/historial`  
**Archivo:** `templates/historial.html`  
**Acceso:** Requiere login  
**TabBar activo:** 🏠 Inicio (sub-sección)

### Funcionalidad
Registro de auditoría completo de todas las operaciones realizadas sobre el inventario. Responde la pregunta *"¿Quién hizo qué y cuándo?"*

### Datos mostrados
Fuente: `VIEW v_historial_completo` (JOIN de `historial_ajustes` + `productos` + `usuarios`).

### Columnas por registro
| Dato | Descripción |
|---|---|
| Punto de color | Verde (crear/ok) · Ámbar (actualizar) · Rojo (eliminar) |
| Producto + SKU | Nombre del producto afectado |
| Fecha y hora | Timestamp del ajuste |
| Empleado | Nombre del usuario que realizó la acción |
| Campo modificado | Qué campo cambió (ej. `stock_cliente_final`) |
| Valor anterior → nuevo | Delta del cambio |

### Filtros disponibles
- **Chips de acción:** Todos / Creación / Ajuste / Eliminado / Conteo
- **Búsqueda en tiempo real** por SKU o nombre de producto (sin recarga de página)

### Badges de estado
| Acción | Badge |
|---|---|
| `CREATE` | Verde `Creación` |
| `UPDATE` / `CONTEO` | Ámbar `Ajuste` / `Conteo` |
| `DELETE` | Rojo `Eliminado` |

### Exportación
Botón *"Exportar CSV"* → llama `/api/historial` (JSON) para descarga. (PDF en Sprint 2)

---

## 6. Perfil de Usuario
**Ruta:** `/perfil`  
**Archivo:** `templates/perfil.html`  
**Acceso:** Requiere login  
**TabBar activo:** 👤 Perfil

### Funcionalidad
Vista personal del empleado autenticado. Muestra sus datos, sede asignada y permite configurar preferencias del sistema.

### Secciones
| Sección | Contenido |
|---|---|
| Hero | Avatar con iniciales, nombre completo, rol, código de empleado, turno |
| Sede Asignada | Nombre de tienda y zona |
| Configuración | Toggle de notificaciones, modo oscuro, idioma, ayuda |
| Seguridad | Enlace a cambiar contraseña (Sprint 2) |
| Cerrar Sesión | `GET /logout` → `session.clear()` → redirige a `/login` |

### Datos fuente
`SELECT * FROM usuarios WHERE id = session['usuario_id']`

---

## 7. Componentes Globales (base)
**Archivo:** `templates/base.html`  
Todas las páginas autenticadas heredan de este template con `{% extends 'base.html' %}`.

### MasterHeader (móvil)
- Barra verde `#00A34D`, 60px, fija en top.
- Izquierda: "TOTTUS" bold.
- Centro: título de la página (`{% block page_title %}`).
- Derecha: ícono de campana con badge rojo de alertas urgentes.

### Sidebar (PC ≥ 768px)
- Panel izquierdo fijo, 240px, fondo blanco.
- 5 ítems de navegación (mismo orden que Tab-Bar).
- **Active state:** fondo verde claro + borde izquierdo verde + texto verde.
- Sección de usuario en el fondo: avatar · nombre · rol · cerrar sesión.

### Tab-Bar (móvil < 768px)
- Barra inferior fija, 80px, 5 ítems.
- Ícono central "Escanear" elevado en círculo verde (botón prominente).
- **Active state:** ícono + label en verde `#00A34D`.

### Tabla de active states
| Página | Ítem activo |
|---|---|
| Dashboard | 🏠 Inicio |
| Alertas | 🔔 Alertas |
| Segmentación | 📦 Productos |
| Historial | 🏠 Inicio |
| Perfil | 👤 Perfil |
| Escáner | ✦ Escanear |

### Sistema de Toast (main.js)
```javascript
showToast('Mensaje', 'success' | 'error' | 'warning', duracionMs)
```
Aparece en esquina inferior derecha, desaparece automáticamente.

### Modal de Confirmación (main.js)
```javascript
showModal('¿Está seguro?', () => { /* acción si confirma */ })
```
Overlay oscuro + card centrada con botones Cancelar / Sí, eliminar.

---

*Documentación generada para Sprint 1 · Mayo 2026*
