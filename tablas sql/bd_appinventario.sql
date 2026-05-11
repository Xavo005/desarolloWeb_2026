-- ============================================================
-- TOTTUS SGI — Base de Datos Completa
-- Motor: MySQL / XAMPP (InnoDB)
-- Versión: 2.0 — Incluye: usuarios, roles, historial, 
--           conteos, alertas y segmentación
-- 
-- INSTRUCCIONES:
-- 1. Importa este archivo en phpMyAdmin
-- 2. Ejecuta: python crear_admin.py  (para el usuario admin)
-- ============================================================

DROP DATABASE IF EXISTS tottus_sgi;
CREATE DATABASE tottus_sgi
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE tottus_sgi;

-- ============================================================
-- TABLA 1: usuarios (con roles)
-- ============================================================
CREATE TABLE usuarios (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    codigo_empleado VARCHAR(20)  UNIQUE NOT NULL,   -- EMP-2024-XXX
    nombre          VARCHAR(100) NOT NULL,
    email           VARCHAR(100) UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    rol             ENUM('operario','supervisor','gerente') DEFAULT 'operario',
    sede            VARCHAR(100) DEFAULT 'Chiclayo - Mall Aventura',
    activo          TINYINT(1)   DEFAULT 1,
    ultimo_login    DATETIME,
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Usuario admin se crea con crear_admin.py (werkzeug hash)
-- Usuarios de prueba con rol supervisor y operario:
INSERT INTO usuarios (codigo_empleado, nombre, email, password_hash, rol, sede) VALUES
('SUP-2024-001', 'María Gonzales',  'maria.gonzales@tottus.com.pe',  'PENDIENTE_HASH', 'supervisor', 'Chiclayo - Mall Aventura'),
('OPE-2024-001', 'Juan Ríos',       'juan.rios@tottus.com.pe',       'PENDIENTE_HASH', 'operario',   'Chiclayo - Mall Aventura');

-- ============================================================
-- TABLA 2: productos
-- ============================================================
CREATE TABLE productos (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    sku               VARCHAR(50)    UNIQUE NOT NULL,
    nombre            VARCHAR(100)   NOT NULL,
    categoria         VARCHAR(50),
    stock_total       INT            NOT NULL DEFAULT 0,
    ubicacion_gondola VARCHAR(100),              -- ej. "Góndola 3, estante 2"
    precio_unitario   DECIMAL(10,2),
    activo            TINYINT(1)     DEFAULT 1,
    created_at        DATETIME       DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO productos (sku, nombre, categoria, stock_total, ubicacion_gondola, precio_unitario) VALUES
('LAC-001', 'Leche Gloria Entera 1L',    'Lácteos',    240, 'Góndola 1, estante 1', 4.20),
('ARR-002', 'Arroz Costeño 5kg',         'Granos',     150, 'Góndola 2, estante 3', 12.90),
('ACE-003', 'Aceite Primor 1L',          'Aceites',     80, 'Góndola 3, estante 2', 8.50),
('AZU-004', 'Azúcar Rubia 1kg',          'Abarrotes',  320, 'Góndola 2, estante 1', 3.10),
('DET-005', 'Detergente Ariel 2kg',      'Limpieza',    95, 'Góndola 5, estante 4', 18.90),
('LAC-006', 'Leche Gloria 750ml',        'Lácteos',    180, 'Góndola 1, estante 2', 3.20),
('YOG-007', 'Yogurt Gloria Fresa 1L',    'Lácteos',     60, 'Góndola 1, estante 3', 5.80),
('PAP-008', 'Papel Higiénico Elite x4',  'Higiene',    200, 'Góndola 6, estante 1', 7.50),
('FID-009', 'Fideos Don Vittorio 500g',  'Granos',     130, 'Góndola 2, estante 4', 2.80),
('SAL-010', 'Sal Marina La Lobera 500g', 'Abarrotes',  400, 'Góndola 4, estante 2', 1.20);

-- ============================================================
-- TABLA 3: segmentacion_inventario
-- ============================================================
CREATE TABLE segmentacion_inventario (
    id                        INT AUTO_INCREMENT PRIMARY KEY,
    producto_id               INT NOT NULL,
    usuario_id                INT,
    stock_cliente_final       INT NOT NULL,
    stock_revendedor          INT NOT NULL,
    limite_compra_final       INT DEFAULT 0,
    limite_compra_revendedor  INT DEFAULT 0,
    motivo                    TEXT,
    activo                    TINYINT(1) DEFAULT 1,
    fecha_creacion            DATETIME   DEFAULT CURRENT_TIMESTAMP,
    updated_at                DATETIME   DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT,
    FOREIGN KEY (usuario_id)  REFERENCES usuarios(id)  ON DELETE SET NULL
) ENGINE=InnoDB;

INSERT INTO segmentacion_inventario
    (producto_id, usuario_id, stock_cliente_final, stock_revendedor, limite_compra_final, limite_compra_revendedor, motivo)
VALUES
(1, NULL, 180, 60,  3, 15, 'Alta demanda - temporada escolar'),
(2, NULL, 100, 50,  5, 20, 'Control de revendedores en campaña'),
(3, NULL,  52, 28,  3, 10, 'Stock bajo - prioridad cliente final'),
(4, NULL, 250, 70,  2, 10, 'Producto básico - restricción revendedor');

-- ============================================================
-- TABLA 4: historial_ajustes
-- ============================================================
CREATE TABLE historial_ajustes (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    producto_id      INT          NOT NULL,
    usuario_id       INT          NOT NULL,
    empleado_nombre  VARCHAR(100),              -- desnormalizado para lectura rápida
    accion           ENUM('CREATE','UPDATE','DELETE','TOGGLE','CONTEO') NOT NULL,
    campo_modificado VARCHAR(80),               -- ej. 'stock_cliente_final'
    valor_anterior   VARCHAR(255),
    valor_nuevo      VARCHAR(255),
    motivo           TEXT,
    fecha            DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id)  REFERENCES usuarios(id)  ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Historial de ejemplo
INSERT INTO historial_ajustes (producto_id, usuario_id, empleado_nombre, accion, campo_modificado, valor_anterior, valor_nuevo, motivo, fecha) VALUES
(1, 2, 'María Gonzales', 'UPDATE', 'stock_cliente_final', '200', '180', 'Ajuste por merma detectada', NOW() - INTERVAL 2 HOUR),
(3, 2, 'María Gonzales', 'CREATE', NULL,                  NULL,  NULL,  'Primera segmentación del día', NOW() - INTERVAL 5 HOUR),
(2, 3, 'Juan Ríos',      'CONTEO', 'stock_total',         '155', '150', 'Conteo físico turno mañana',   NOW() - INTERVAL 7 HOUR);

-- ============================================================
-- TABLA 5: alertas_quiebre
-- ============================================================
CREATE TABLE alertas_quiebre (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    producto_id      INT,
    producto         VARCHAR(100)   NOT NULL,
    sku              VARCHAR(50)    NOT NULL,
    categoria        VARCHAR(50),
    unidades         INT            NOT NULL,
    venta_dia        DECIMAL(8,2)   NOT NULL DEFAULT 0,
    horas_restantes  DECIMAL(8,2)   GENERATED ALWAYS AS (
                         CASE WHEN venta_dia > 0
                              THEN ROUND((unidades / venta_dia) * 24, 1)
                              ELSE 9999
                         END
                     ) STORED,
    nivel            ENUM('critico','urgente','advertencia','ok') GENERATED ALWAYS AS (
                         CASE
                             WHEN venta_dia <= 0                                THEN 'ok'
                             WHEN (unidades / venta_dia) * 24 <= 24            THEN 'critico'
                             WHEN (unidades / venta_dia) * 24 <= 72            THEN 'urgente'
                             WHEN (unidades / venta_dia) * 24 <= 120           THEN 'advertencia'
                             ELSE 'ok'
                         END
                     ) STORED,
    estado_transf    VARCHAR(100) DEFAULT 'Sin transferencia activa',
    activo           TINYINT(1)   DEFAULT 1,
    updated_at       DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE SET NULL
) ENGINE=InnoDB;

INSERT INTO alertas_quiebre (producto_id, producto, sku, categoria, unidades, venta_dia, estado_transf) VALUES
(1, 'Leche Gloria Entera 1L',  'LAC-001', 'Lácteos',   12,  8.0,  'Transferencia en tránsito'),
(2, 'Arroz Costeño 5kg',       'ARR-002', 'Granos',    45, 15.0,  'Pedido generado'),
(4, 'Azúcar Rubia 1kg',        'AZU-004', 'Abarrotes', 58, 12.0,  'Sin transferencia activa'),
(5, 'Detergente Ariel 2kg',    'DET-005', 'Limpieza',   8,  5.0,  'Urgente - sin stock en CD'),
(7, 'Yogurt Gloria Fresa 1L',  'YOG-007', 'Lácteos',   60, 10.0,  'Sin transferencia activa');

-- ============================================================
-- TABLA 6: conteos_manuales
-- ============================================================
CREATE TABLE conteos_manuales (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    producto_id     INT         NOT NULL,
    usuario_id      INT         NOT NULL,
    stock_sistema   INT         NOT NULL,
    stock_contado   INT         NOT NULL,
    diferencia      INT         GENERATED ALWAYS AS (stock_contado - stock_sistema) STORED,
    motivo          TEXT,
    estado          ENUM('pendiente','aplicado','rechazado') DEFAULT 'pendiente',
    fecha           DATETIME    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id)  REFERENCES usuarios(id)  ON DELETE RESTRICT
) ENGINE=InnoDB;

INSERT INTO conteos_manuales (producto_id, usuario_id, stock_sistema, stock_contado, motivo, estado) VALUES
(1, 3, 20, 12, 'Merma detectada en góndola - productos vencidos', 'aplicado'),
(3, 2, 82, 80, 'Conteo rutina turno mañana', 'aplicado');

-- ============================================================
-- VISTAS ÚTILES (para reportes rápidos)
-- ============================================================

-- Vista: Estado completo de alertas con producto y nivel calculado
CREATE OR REPLACE VIEW v_alertas_activas AS
SELECT 
    a.id,
    a.sku,
    a.producto,
    a.categoria,
    a.unidades,
    a.venta_dia,
    a.horas_restantes,
    a.nivel,
    a.estado_transf,
    p.stock_total,
    p.ubicacion_gondola
FROM alertas_quiebre a
LEFT JOIN productos p ON a.producto_id = p.id
WHERE a.activo = 1
ORDER BY a.horas_restantes ASC;

-- Vista: Historial con nombres de empleado y producto
CREATE OR REPLACE VIEW v_historial_completo AS
SELECT 
    h.id,
    h.fecha,
    h.empleado_nombre,
    u.rol AS empleado_rol,
    p.nombre AS producto_nombre,
    p.sku,
    h.accion,
    h.campo_modificado,
    h.valor_anterior,
    h.valor_nuevo,
    h.motivo
FROM historial_ajustes h
JOIN productos p ON h.producto_id = p.id
JOIN usuarios u  ON h.usuario_id  = u.id
ORDER BY h.fecha DESC;

-- ============================================================
-- FIN DEL SCRIPT
-- Siguiente paso: ejecutar python crear_admin.py
-- ============================================================
