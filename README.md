# 🛒 Tottus SGI — Sistema Gerencial de Inventario
**Sprint 1 & 2** · Flask · MySQL · XAMPP · Mobile-First

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql)
![Sprint](https://img.shields.io/badge/Sprint-2%20completo-00A34D)
![License](https://img.shields.io/badge/License-Académico-green)

Sistema web de gestión de inventario para tiendas Tottus. Permite controlar alertas de quiebre, segmentar stock, escanear productos en góndola y mantener auditoría completa con trazabilidad por usuario.

---

## 📋 Funcionalidades por Sprint

### ✅ Sprint 1 — Base del sistema
| Módulo | Descripción |
|---|---|
| 🔐 **Login** | Autenticación con código de empleado + contraseña hasheada |
| 📊 **Dashboard** | Métricas en tiempo real: quiebres, alertas urgentes, accesos rápidos |
| 🔔 **Alertas** | Panel de quiebres con nivel automático + CRUD completo |
| 📦 **Segmentación** | CRUD de reglas de distribución de stock CF vs. Revendedor |
| 📋 **Historial** | Auditoría: quién · qué · cuándo · delta de cambio |
| 👤 **Perfil** | Datos del empleado, sede asignada, configuración |

### ✅ Sprint 2 — Catálogo, Escáner y Seguridad
| Módulo | Descripción |
|---|---|
| 🗂️ **Catálogo de Productos** | CRUD completo con validación de SKU único y control por roles |
| 📷 **Escáner QR/Barcode** | Lectura EAN-13 desde cámara del celular (QuaggaJS, sin app) |
| 🔑 **Cambio de Contraseña** | Formulario seguro con indicador de fortaleza en tiempo real |
| 📄 **Exportación CSV** | Descarga del historial con nombre con timestamp |

---

## 🏗️ Arquitectura

```
desarolloWeb_2026/
├── app.py                    # Backend Flask unificado (791 líneas)
├── crear_admin.py            # Crea usuario admin con hash seguro
├── requirements.txt
├── .env                      # Variables de entorno (NO al repositorio)
│
├── static/
│   ├── css/
│   │   └── style.css         # Design System completo
│   └── js/
│       ├── main.js           # Toast + Modal (todas las páginas)
│       ├── productos.js      # CRUD catálogo [Sprint 2]
│       ├── escanear.js       # QuaggaJS + flujo escáner [Sprint 2]
│       └── segmentacion.js
│
├── templates/
│   ├── base.html             # Master Template: Sidebar (PC) + TabBar (Móvil)
│   ├── login.html
│   ├── dashboard.html
│   ├── alertas.html
│   ├── productos.html        # [Sprint 2]
│   ├── escanear.html         # [Sprint 2]
│   ├── segmentacion.html
│   ├── historial.html        # + exportar CSV [Sprint 2]
│   └── perfil.html           # + cambio de clave [Sprint 2]
│
├── tablas sql/
│   └── bd_appinventario.sql  # 6 tablas + 2 vistas
│
└── docs/
    └── paginas.md            # Documentación técnica por página
```

---

## 🗄️ Modelo de Base de Datos

| Tabla | Propósito |
|---|---|
| `usuarios` | Empleados con roles: operario / supervisor / gerente |
| `productos` | Catálogo con SKU, stock, precio y velocidad de venta |
| `segmentacion_inventario` | Reglas CF vs. Revendedor por producto |
| `alertas_quiebre` | Alertas con nivel calculado por columna GENERATED |
| `historial_ajustes` | Auditoría completa con delta de cambio |
| `conteos_manuales` | Conteo físico vs. sistema (desde escáner) |

---

## 🚀 Instalación

```bash
# 1. Clonar
git clone <url-del-repo> && cd desarolloWeb_2026

# 2. Dependencias
pip install -r requirements.txt

# 3. Importar BD en phpMyAdmin
#    → tablas sql/bd_appinventario.sql

# 4. Migración Sprint 2 (si BD ya existe del Sprint 1)
#    → phpMyAdmin → SQL:
ALTER TABLE productos ADD COLUMN venta_dia DECIMAL(8,2) DEFAULT 0;

# 5. Crear admin
python crear_admin.py
# Código: ADMIN-001 | Clave: tottus2026

# 6. Ejecutar
python app.py  # → http://localhost:5000
```

### `.env`
```env
FLASK_SECRET_KEY=tu_clave_secreta_aqui
DB_HOST=localhost
DB_NAME=tottus_sgi
DB_USER=root
DB_PASSWORD=
FLASK_DEBUG=True
```

---

## 🔐 Roles y Permisos

| Acción | Operario | Supervisor | Gerente |
|---|:---:|:---:|:---:|
| Ver dashboard y alertas | ✅ | ✅ | ✅ |
| Crear / Editar productos | ❌ | ✅ | ✅ |
| **Eliminar productos** | ❌ | ❌ | ✅ |
| Crear / Editar segmentación | ❌ | ✅ | ✅ |
| **Eliminar segmentación** | ❌ | ❌ | ✅ |
| Escanear y registrar conteo | ✅ | ✅ | ✅ |
| Ver historial y exportar CSV | ✅ | ✅ | ✅ |
| Cambiar su propia contraseña | ✅ | ✅ | ✅ |

---

## 🔌 API Endpoints

### Productos
| Método | Ruta | Rol |
|---|---|---|
| GET | `/api/productos` | Todos |
| POST | `/api/productos` | Supervisor+ |
| PUT | `/api/productos/<id>` | Supervisor+ |
| DELETE | `/api/productos/<id>` | Gerente |
| GET | `/api/productos/buscar-sku/<sku>` | Todos |

### Segmentaciones
| Método | Ruta | Rol |
|---|---|---|
| GET/POST | `/api/segmentaciones` | Todos / Supervisor+ |
| PUT/DELETE | `/api/segmentaciones/<id>` | Supervisor+ / Gerente |
| PATCH | `/api/segmentaciones/<id>/toggle` | Supervisor+ |

### Alertas / Historial / Conteos / Perfil
| Método | Ruta | Descripción |
|---|---|---|
| GET/DELETE | `/api/alertas` | Listar / Descartar alerta |
| GET | `/api/historial` | JSON últimos 200 |
| GET | `/historial/exportar` | Descarga CSV (`?accion=` filtro) |
| POST | `/api/conteos` | Conteo manual desde escáner |
| POST | `/api/perfil/cambiar-clave` | Cambiar contraseña |

---

## 🎨 Design System

| Token | Valor | Uso |
|---|---|---|
| `--primary` | `#00A34D` | Botones, header, nav activo |
| `--danger` | `#D32F2F` | Eliminar, alertas críticas |
| `--warning` | `#FFB300` | Editar, alertas urgentes |
| `--bg` | `#F4F7F5` | Fondo general |
| `--font` | `Inter` | Tipografía global |
| `--radius-card` | `16px` | Todas las cards |

---

## 📱 Responsive

| Breakpoint | Layout |
|---|---|
| < 768px | Header fijo + TabBar inferior de 5 ítems |
| ≥ 768px | Sidebar lateral 240px + contenido a la derecha |

---

## ✅ Sprint 2 — Completado

- [x] CRUD de Productos desde la web con roles
- [x] Escáner QR/Barcode con QuaggaJS (EAN-13, sin app)
- [x] Registro de conteos manuales desde el escáner
- [x] Cambio de contraseña con indicador de fortaleza
- [x] Exportación de historial en CSV con timestamp

---

## 📌 Pendientes para Sprint 3

- [ ] Gestión de Usuarios (CRUD de empleados, solo gerente)
- [ ] Recuperación de contraseña por email (token temporal)
- [ ] Exportación de historial en PDF
- [ ] Predicción dinámica de quiebre (basada en historial real)
- [ ] Paginación del historial en backend
- [ ] Operaciones masivas en alertas (resolver varias a la vez)
- [ ] Dashboard con gráficas (Chart.js: stock por categoría, tendencias)
- [ ] Ocultar botones en UI según rol del usuario
- [ ] Tests automatizados (pytest para endpoints críticos)

---

## 👥 Equipo

Proyecto académico USAT · Desarrollo Web 2026
Grupo: GRUPAL_DAWE
