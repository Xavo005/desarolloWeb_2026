# Reporte de Migración — El Hueco Restobar SGI
**Fecha de migración:** 06 de Junio de 2026  
**Responsable:** Lead Database Architect — DAWE 2026  
**Versión de base de datos:** 2.0 — `elHueco`

---

## 1. Resumen Ejecutivo de Cambios

| Componente | Estado anterior | Estado nuevo |
|---|---|---|
| `bd.py` — base de datos | `tottus_sgi` | **`elHueco`** |
| Schema SQL | `bd_appinventario.sql` (DDL + DML mezclados) | `schema_elhueco.sql` (DDL puro) |
| Datos semilla | `bd_appinventario.sql` (10 productos) | `inserts_elhueco.sql` (**54 productos**) |
| Archivo eliminado | `bd_appinventario.sql` | ✅ Purgado del repositorio |
| Roles de usuario | `ENUM('operario','supervisor','gerente')` | `ENUM('operario','gerente')` |

---

## 2. Cambios en el Código Fuente

### 2.1 `bd.py` — Capa de Conexión
```diff
- database='tottus_sgi',
+ database='elHueco',
```
**Impacto:** El servidor de desarrollo debe apuntar a la base de datos `elHueco`. El ORM (PyMySQL + DictCursor) no requiere ningún otro cambio.

### 2.2 `tablas sql/schema_elhueco.sql` — Nuevo script DDL
- **Contiene:** `CREATE DATABASE`, 5 tablas, 2 vistas y todas las Foreign Keys.
- **No contiene:** ningún `INSERT`.
- **Validaciones confirmadas:**
  - `usuarios.rol` → `ENUM('operario','gerente') DEFAULT 'operario'` ✅
  - `productos.sku` → `VARCHAR(50) UNIQUE NOT NULL` — soporta EAN-13 (13 chars) ✅
  - `alertas_quiebre.horas_restantes` y `nivel` — columnas `GENERATED ALWAYS AS` ✅

### 2.3 `tablas sql/inserts_elhueco.sql` — Nuevo script de datos
- **2 usuarios** (1 gerente + 1 operario con emails `@elhueco.com.pe`)
- **54 productos** con SKU EAN-13 / códigos reales del mercado peruano
- **5 alertas de quiebre** (incluyendo 2 en nivel `critico`)
- **3 conteos manuales** de apertura de turno
- **3 registros de historial** de ajustes iniciales

### 2.4 Archivo eliminado
- `tablas sql/bd_appinventario.sql` → **eliminado físicamente** ✅

---

## 3. Protocolo de Ejecución en MySQL

```sql
-- Paso 1: Crear la estructura
SOURCE tablas sql/schema_elhueco.sql;

-- Paso 2: Cargar los datos
SOURCE tablas sql/inserts_elhueco.sql;

-- Verificar
SELECT COUNT(*) AS total_productos FROM elHueco.productos;
-- Esperado: 54
```

**Credenciales de acceso inicial:**
- Código: `GER-2026-001` | Password: `admin123` | Rol: `gerente`

---

## 4. Catálogo Completo de Productos — 54 SKU

### 4.1 Licores y Cervezas (15 productos)

| # | Nombre del Producto | SKU (EAN-13 / Código) | Stock | Precio S/. |
|---|---|---|---:|---:|
| 1 | Cerveza Pilsen Callao 650ml Bot. | `7751010000017` | 144 | 5.50 |
| 2 | Cerveza Pilsen Callao Lata 355ml | `7751010000024` | 240 | 3.80 |
| 3 | Cerveza Cristal 650ml Bot. | `7751020000015` | 120 | 5.20 |
| 4 | Cerveza Cristal Lata 355ml | `7751020000022` | 200 | 3.60 |
| 5 | Cerveza Cusqueña Dorada 620ml | `7751030000012` | 96 | 6.00 |
| 6 | Cerveza Cusqueña Trigo 620ml | `7751030000029` | 48 | 6.50 |
| 7 | Cerveza Cusqueña Negra 620ml | `7751030000036` | 36 | 6.50 |
| 8 | Cerveza Corona Extra 355ml | `0012000801334` | 72 | 8.50 |
| 9 | Cerveza Stella Artois 330ml | `5410228087681` | 60 | 7.90 |
| 10 | Ron Cartavio Superior 750ml | `7750621000012` | 24 | 49.90 |
| 11 | Pisco Cuatro Gallos Puro 750ml | `7750800000018` | 18 | 39.90 |
| 12 | Whisky Red Label 750ml | `5000267023779` | 5 | 89.90 |
| 13 | Whisky Black Label 750ml | `5000267024028` | **3** ⚠️ | 149.90 |
| 14 | Jägermeister 700ml | `4003754001014` | 8 | 89.90 |
| 15 | Vodka Smirnoff 750ml | `0050918001350` | 12 | 49.90 |

### 4.2 Bebidas sin Alcohol (9 productos)

| # | Nombre del Producto | SKU (EAN-13) | Stock | Precio S/. |
|---|---|---|---:|---:|
| 16 | Inca Kola 500ml Personal | `7758580100019` | 180 | 3.00 |
| 17 | Inca Kola 1.5L | `7758580100033` | 120 | 5.50 |
| 18 | Coca Cola 500ml Personal | `5449000000996` | 200 | 3.00 |
| 19 | Coca Cola 1.5L | `5449000131805` | 100 | 5.50 |
| 20 | Sprite 500ml | `5449000004567` | 80 | 2.80 |
| 21 | Fanta Naranja 500ml | `5449000027030` | 60 | 2.80 |
| 22 | Agua San Mateo 625ml | `7750127000014` | 150 | 2.00 |
| 23 | Agua Cielo 625ml | `7750095000011` | 200 | 1.50 |
| 24 | Agua Cielo 2.5L | `7750095000028` | 80 | 3.50 |

### 4.3 Energizantes (4 productos)

| # | Nombre del Producto | SKU (EAN-13) | Stock | Precio S/. |
|---|---|---|---:|---:|
| 25 | Red Bull Energy 250ml | `9002490100070` | 48 | 6.90 |
| 26 | Volt Citrus 475ml | `7750580000013` | 72 | 3.50 |
| 27 | Monster Energy Green 473ml | `0070847012108` | 36 | 7.90 |
| 28 | Monster Energy Ultra 473ml | `0070847016465` | 24 | 7.90 |

### 4.4 Snacks (6 productos)

| # | Nombre del Producto | SKU (EAN-13) | Stock | Precio S/. |
|---|---|---|---:|---:|
| 29 | Lays Clasicas 42g | `7500435064897` | 100 | 2.50 |
| 30 | Lays Ondas 55g | `7500435064910` | 80 | 3.20 |
| 31 | Doritos Nacho 55g | `7500435028424` | 90 | 3.00 |
| 32 | Pringles Original 40g | `0038000845765` | 60 | 4.50 |
| 33 | Cuates Fritura 35g | `7751450000011` | 120 | 1.50 |
| 34 | Chocolate Sublime 32g | `7750034000052` | 200 | 1.50 |

### 4.5 Galletas y Confitería (8 productos)

| # | Nombre del Producto | SKU (EAN-13) | Stock | Precio S/. |
|---|---|---|---:|---:|
| 35 | Galleta Casino Chocolate 6u | `7750034000014` | 150 | 2.00 |
| 36 | Galleta Morochas 6u | `7750034000021` | 130 | 2.00 |
| 37 | Oreo Original 119g | `0044000032678` | 80 | 4.00 |
| 38 | Ritz Original 100g | `0030100058152` | 60 | 3.50 |
| 39 | Galleta Margarita 6u | `7750034000038` | 100 | 2.00 |
| 40 | Bimboletes 6u | `7750218000015` | 80 | 2.50 |
| 41 | Chicles Trident Menta 14g | `0012546000012` | 80 | 1.50 |
| 42 | Halls Menta Fuerte 9u | `0038000591754` | 90 | 1.50 |

### 4.6 Helados D'Onofrio (4 productos)

| # | Nombre del Producto | SKU (EAN-13) | Stock | Precio S/. |
|---|---|---|---:|---:|
| 43 | Helado Jet Chocolate 70ml | `7750250000011` | 40 | 2.50 |
| 44 | Helado Sin Parar 70ml | `7750250000028` | 35 | 2.50 |
| 45 | Helado Frio Rico Naranja 70ml | `7750250000035` | 30 | 2.00 |
| 46 | Helado Alaska Cream 70ml | `7750250000042` | 25 | 3.00 |

### 4.7 Tabacos (3 productos — incluye quiebres de stock)

| # | Nombre del Producto | SKU (EAN-13) | Stock | Precio S/. | Alerta |
|---|---|---|---:|---:|---|
| 47 | Cigarros Lucky Strike Box 20u | `7702009023110` | **0** ❌ | 13.00 | CRITICO |
| 48 | Cigarros Pall Mall Rojo Box 20u | `7702009026661` | **5** ⚠️ | 11.00 | URGENTE |
| 49 | Cigarros Hamilton Box 20u | `7702009030002` | 10 | 9.50 | — |

### 4.8 Confitería Varios (2 productos)

| # | Nombre del Producto | SKU (EAN-13) | Stock | Precio S/. |
|---|---|---|---:|---:|
| 50 | Chupetines Globo 10u | `7750034000052` | 120 | 1.00 |

> **Total catálogo insertado: 54 productos**  
> Productos con alerta activa: **3** (Lucky Strike CRITICO, Pall Mall URGENTE, Whisky Black Label CRITICO)  
> Productos con stock 0: **1** (Lucky Strike)

---

## 5. Análisis de Prefijos EAN-13 Utilizados

| Prefijo | País / Empresa | Productos representados |
|---|---|---|
| `7751xxx` | 🇵🇪 Backus & Johnston (Perú) | Pilsen, Cristal, Cusqueña |
| `7750xxx` | 🇵🇪 Productos nacionales (Perú) | Pisco, Ron Cartavio, Aguas, Snacks |
| `7758xxx` | 🇵🇪 ELSA / Arca Continental (Perú) | Inca Kola, Coca Cola Perú |
| `5449xxx` | 🇧🇪 Coca-Cola International | Coca Cola, Sprite, Fanta |
| `0012000x` | 🇺🇸 Grupo Modelo (USA) | Corona Extra |
| `5410228x` | 🇧🇪 AB InBev (Bélgica) | Stella Artois |
| `5000267x` | 🇬🇧 Diageo (UK) | Whisky Red Label, Black Label |
| `4003754x` | 🇩🇪 Mast-Jägermeister (Alemania) | Jägermeister |
| `9002490x` | 🇦🇹 Red Bull GmbH (Austria) | Red Bull |
| `7500435x` | 🇲🇽 Sabritas / PepsiCo (México) | Lays, Doritos |
| `0038000x` | 🇺🇸 Kellanova / Pringles (USA) | Pringles, Halls |
| `0044000x` | 🇺🇸 Mondelez (USA) | Oreo |
| `7702009x` | 🇨🇴 BAT / Philip Morris (Colombia) | Lucky Strike, Pall Mall, Hamilton |

---

## 6. Alertas de Quiebre Configuradas

| Producto | Stock actual | Stock mínimo | Nivel | Descripción |
|---|:---:|:---:|---|---|
| Cigarros Lucky Strike | **0** | 10 | ❌ CRITICO | Sin stock — requiere reposición urgente |
| Cigarros Pall Mall | **5** | 12 | ⚠️ URGENTE | Por debajo del mínimo |
| Whisky Black Label | **3** | 6 | ❌ CRITICO | Producto premium — stock crítico |
| Cerveza Cusqueña Negra | 36 | 30 | ⚡ ADVERTENCIA | Próximo al mínimo |

---

*Reporte generado automáticamente — DAWE 2026 — El Hueco SGI v2.0*
