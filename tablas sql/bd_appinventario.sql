DROP DATABASE IF EXISTS `tottus_sgi`;
CREATE DATABASE `tottus_sgi`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `tottus_sgi`;

SET FOREIGN_KEY_CHECKS = 0;

-- ==========================================
-- TABLA: USUARIOS
-- ==========================================
CREATE TABLE `usuarios` (
    `id`                INT          AUTO_INCREMENT PRIMARY KEY,
    `codigo_empleado`   VARCHAR(20)  UNIQUE NOT NULL,
    `nombre`            VARCHAR(100) NOT NULL,
    `email`             VARCHAR(100) UNIQUE,
    `password`          VARCHAR(255) NOT NULL, -- Aumentado a 255 para futuros hashes
    `rol`               ENUM('operario','supervisor','gerente') DEFAULT 'operario',
    `sede`              VARCHAR(100) DEFAULT 'Chiclayo',
    `palabra_clave`     VARCHAR(100) NOT NULL,
    `activo`            TINYINT(1)   DEFAULT 1,
    `ultimo_login`      DATETIME     NULL,
    `created_at`        DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ==========================================
-- TABLA: PRODUCTOS
-- ==========================================
CREATE TABLE `productos` (
    `id`                INT          AUTO_INCREMENT PRIMARY KEY,
    `sku`               VARCHAR(50)  UNIQUE NOT NULL,
    `nombre`            VARCHAR(100) NOT NULL,
    `categoria`         VARCHAR(50),
    `stock_total`       INT          NOT NULL DEFAULT 0,
    `ubicacion_gondola` VARCHAR(100),
    `precio_unitario`   DECIMAL(10,2),
    `venta_dia`         DECIMAL(8,2) DEFAULT 0,
    `activo`            TINYINT(1)   DEFAULT 1,
    `created_at`        DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ==========================================
-- TABLA: SEGMENTACION_INVENTARIO
-- ==========================================
CREATE TABLE `segmentacion_inventario` (
    `id`                         INT        AUTO_INCREMENT PRIMARY KEY,
    `producto_id`                INT        NOT NULL,
    `usuario_id`                 INT,
    `stock_cliente_final`        INT        NOT NULL,
    `stock_revendedor`           INT        NOT NULL,
    `limite_compra_final`        INT        DEFAULT 0,
    `limite_compra_revendedor`   INT        DEFAULT 0,
    `motivo`                     TEXT,
    `activo`                     TINYINT(1) DEFAULT 1,
    `fecha_creacion`             DATETIME   DEFAULT CURRENT_TIMESTAMP,
    `updated_at`                 DATETIME   DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`producto_id`) REFERENCES `productos`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`usuario_id`)  REFERENCES `usuarios`(`id`)  ON DELETE SET NULL
) ENGINE=InnoDB;

-- ==========================================
-- TABLA: ALERTAS_QUIEBRE
-- ==========================================
CREATE TABLE `alertas_quiebre` (
    `id`              INT          AUTO_INCREMENT PRIMARY KEY,
    `producto_id`     INT,
    `producto`        VARCHAR(100) NOT NULL,
    `sku`             VARCHAR(50)  NOT NULL,
    `categoria`       VARCHAR(50),
    `unidades`        INT          NOT NULL,
    `venta_dia`       DECIMAL(8,2) NOT NULL DEFAULT 0,
    `estado_transf`   VARCHAR(100) DEFAULT 'Sin transferencia activa',
    `activo`          TINYINT(1)   DEFAULT 1,
    `updated_at`      DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`producto_id`) REFERENCES `productos`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ==========================================
-- TABLA: CONTEOS_MANUALES
-- ==========================================
CREATE TABLE `conteos_manuales` (
    `id`            INT       AUTO_INCREMENT PRIMARY KEY,
    `producto_id`   INT       NOT NULL,
    `usuario_id`    INT       NOT NULL,
    `stock_sistema` INT       NOT NULL,
    `stock_contado` INT       NOT NULL,
    `motivo`        TEXT,
    `estado`        ENUM('pendiente','aplicado','rechazado') DEFAULT 'pendiente',
    `fecha`         DATETIME  DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`producto_id`) REFERENCES `productos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`usuario_id`)  REFERENCES `usuarios`(`id`)  ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ==========================================
-- TABLA: HISTORIAL_AJUSTES
-- ==========================================
CREATE TABLE `historial_ajustes` (
    `id`                INT          AUTO_INCREMENT PRIMARY KEY,
    `producto_id`       INT          NOT NULL,
    `usuario_id`        INT          NOT NULL,
    `empleado_nombre`   VARCHAR(100),
    `accion`            ENUM('CREATE','UPDATE','DELETE','TOGGLE','CONTEO') NOT NULL,
    `campo_modificado`  VARCHAR(80),
    `valor_anterior`    VARCHAR(255),
    `valor_nuevo`       VARCHAR(255),
    `motivo`            TEXT,
    `fecha`             DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`producto_id`) REFERENCES `productos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`usuario_id`)  REFERENCES `usuarios`(`id`)  ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ==========================================
-- VISTAS (Creadas después de las tablas)
-- ==========================================
CREATE OR REPLACE VIEW `v_alertas_activas` AS
SELECT
    a.id, a.producto_id, a.sku, a.producto, a.categoria, a.unidades, a.venta_dia,
    ROUND((CASE WHEN a.venta_dia > 0 THEN (a.unidades / a.venta_dia) * 24 ELSE 9999 END), 1) AS horas_restantes,
    (CASE 
        WHEN a.venta_dia <= 0 THEN 'ok'
        WHEN (a.unidades / a.venta_dia) * 24 <= 24 THEN 'critico'
        WHEN (a.unidades / a.venta_dia) * 24 <= 72 THEN 'urgente'
        WHEN (a.unidades / a.venta_dia) * 24 <= 120 THEN 'advertencia'
        ELSE 'ok'
    END) AS nivel,
    a.estado_transf, p.stock_total, p.ubicacion_gondola
FROM `alertas_quiebre` a
LEFT JOIN `productos` p ON a.producto_id = p.id
WHERE a.activo = 1;

CREATE OR REPLACE VIEW `v_historial_completo` AS
SELECT h.*, p.nombre AS producto_nombre, p.sku, u.rol AS empleado_rol
FROM `historial_ajustes` h
JOIN `productos` p ON h.producto_id = p.id
JOIN `usuarios` u ON h.usuario_id = u.id;

-- ==========================================
-- DATOS DE INSERCIÓN
-- ==========================================
INSERT INTO `usuarios` (`codigo_empleado`, `nombre`, `email`, `password`, `rol`, `sede`, `palabra_clave`)
VALUES ('GER-2026-001', 'Eduardo Valdez', 'eduardo.valdezz@tottus.com.pe', 'admin123', 'gerente', 'Chiclayo', 'ger');

INSERT INTO `productos` (`sku`, `nombre`, `categoria`, `stock_total`, `ubicacion_gondola`, `precio_unitario`, `venta_dia`)
VALUES ('LAC-001', 'Leche Gloria Entera 1L', 'Lácteos', 240, 'Góndola 1', 4.20, 8.0);

SET FOREIGN_KEY_CHECKS = 1;