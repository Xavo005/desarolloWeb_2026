# 🛒 Tottus SGI — Sistema Gerencial de Inventario
**Sprint 1** · Flask · MySQL · XAMPP · Mobile-First

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql)
![License](https://img.shields.io/badge/License-Académico-green)

Sistema web de gestión de inventario diseñado para tiendas Tottus. Permite a supervisores y operarios controlar alertas de quiebre, segmentar stock entre clientes finales y revendedores, y mantener un historial de auditoría completo con trazabilidad por usuario.

---

## 📋 Funcionalidades del Sprint 1

| Módulo | Descripción |
|---|---|
| 🔐 **Login** | Autenticación con código de empleado + contraseña hasheada (werkzeug) |
| 📊 **Dashboard** | Métricas en tiempo real: quiebres, alertas urgentes, accesos rápidos |
| 🔔 **Alertas** | Panel de quiebres con nivel automático (crítico/urgente/advertencia) + CRUD |
| 📦 **Segmentación** | CRUD completo de reglas de distribución de stock CF vs. Revendedor |
| 📋 **Historial** | Auditoría de ajustes: quién · qué · cuándo · delta de cambio |
| 👤 **Perfil** | Datos del empleado, sede asignada, configuración y cierre de sesión |

---

## 🏗️ Arquitectura

```
desarolloWeb_2026/
├── app.py                  # Backend Flask unificado (rutas + API + sesiones)
├── crear_admin.py          # Script único: crea el usuario admin con hash seguro
├── requirements.txt        # Dependencias Python
├── .env                    # Variables de entorno (NO subir al repositorio)
│
├── static/
│   ├── CSS/
│   │   ├── style.css       # Design System completo (tokens + componentes)
│   │   └── estilos.css     # Estilos legacy (alertas)
│   └── JS/
│       ├── main.js         # Toast + Modal reutilizables (todas las páginas)
│       └── segmentacion.js # Lógica CRUD de segmentación
│
├── templates/
│   ├── base.html           # Master Template: Sidebar (PC) + TabBar (Móvil)
│   ├── login.html          # Pública · Split-screen PC / Card Móvil
│   ├── dashboard.html      # Privada · Métricas + accesos rápidos
│   ├── alertas.html        # Privada · AlertCards + botones CRUD
│   ├── segmentacion.html   # Privada · Formulario ajuste + tabla CRUD
│   ├── historial.html      # Privada · Registro de auditoría con filtros
│   └── perfil.html         # Privada · Datos de usuario + configuración
│
├── tablas sql/
│   └── bd_appinventario.sql  # Schema completo: 6 tablas + 2 vistas + datos
│
└── docs/
    └── paginas.md          # Documentación detallada de cada página
```

---

## 🗄️ Modelo de Base de Datos

```
usuarios ──────────┐
                   ├─── historial_ajustes
productos ─────────┤
    │              ├─── conteos_manuales
    ├── segmentacion_inventario
    └── alertas_quiebre

VISTAS:
  v_alertas_activas    → alertas_quiebre JOIN productos
  v_historial_completo → historial_ajustes JOIN productos JOIN usuarios
```

| Tabla | Propósito |
|---|---|
| `usuarios` | Empleados con roles: operario / supervisor / gerente |
| `productos` | Catálogo con SKU, stock, categoría y ubicación en góndola |
| `segmentacion_inventario` | Reglas CF vs. Revendedor por producto |
| `alertas_quiebre` | Alertas con nivel calculado automáticamente (campo GENERATED) |
| `historial_ajustes` | Auditoría completa con usuario_id y delta de cambio |
| `conteos_manuales` | Registros de conteo físico vs. sistema |

---

## 🚀 Instalación y puesta en marcha

### Pre-requisitos
- Python 3.11+
- XAMPP (Apache + MySQL activos)
- Git

### Pasos

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd desarolloWeb_2026

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Importar la base de datos
# → Abrir http://localhost/phpmyadmin
# → Importar: tablas sql/bd_appinventario.sql

# 4. Crear el usuario administrador
python crear_admin.py
# ✅ Código: ADMIN-001  |  Clave: tottus2026

# 5. Ejecutar la aplicación
python app.py
# → Abrir: http://localhost:5000
```

### Variables de entorno (`.env`)
```env
FLASK_SECRET_KEY=tu_clave_secreta_aqui
DB_HOST=localhost
DB_NAME=tottus_sgi
DB_USER=root
DB_PASSWORD=
FLASK_DEBUG=True
```

---

## 🔑 Credenciales de prueba

| Código | Contraseña | Rol |
|---|---|---|
| `ADMIN-001` | `tottus2026` | Gerente (acceso total) |
| `SUP-2024-001` | *(crear con script)* | Supervisor |
| `OPE-2024-001` | *(crear con script)* | Operario |

---

## 🔐 Sistema de Roles y Permisos

| Acción | Operario | Supervisor | Gerente |
|---|:---:|:---:|:---:|
| Ver dashboard y alertas | ✅ | ✅ | ✅ |
| Crear segmentación | ❌ | ✅ | ✅ |
| Editar segmentación | ❌ | ✅ | ✅ |
| **Eliminar segmentación** | ❌ | ❌ | ✅ |
| Ver historial | ✅ | ✅ | ✅ |

---

## 🧭 Navegación del Sistema

```
[Login] ──→ [Dashboard]
                ├──→ [Alertas]     → modal confirmar → [Eliminar alerta]
                │        └──→ [Segmentación]  (Editar)
                ├──→ [Segmentación] (CRUD completo)
                ├──→ [Historial]   (filtros + búsqueda)
                └──→ [Perfil]      → [Logout]
```

---

## 🎨 Design System

| Token | Valor | Uso |
|---|---|---|
| `--primary` | `#00A34D` | Botones, header, nav activo |
| `--danger` | `#D32F2F` | Eliminar, alertas críticas |
| `--warning` | `#FFB300` | Editar, alertas urgentes |
| `--bg` | `#F4F7F5` | Fondo de todas las páginas |
| `--font` | `Inter` | Tipografía global |
| `--radius-card` | `16px` | Todas las cards |

---

## 📱 Responsive

| Breakpoint | Layout |
|---|---|
| < 768px (Móvil) | Header fijo + TabBar inferior de 5 ítems |
| ≥ 768px (PC) | Sidebar lateral de 240px + contenido a la derecha |

---

## 📌 Pendientes para Sprint 2

- [ ] Cambio de contraseña desde Perfil
- [ ] Exportación de historial en PDF/Excel
- [ ] Módulo de Escáner QR/Barcode
- [ ] Predicción de quiebre por velocidad de venta
- [ ] Operaciones masivas (batch) en alertas
- [ ] Recuperación de contraseña por email

---

## 👥 Equipo

Proyecto académico USAT · Desarrollo Web 2026  
Grupo: GRUPAL_DAWE
