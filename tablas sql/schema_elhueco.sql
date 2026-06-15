-- ============================================================
--  BOTICA CENTRAL — SCHEMA Y DATOS DE BASE DE DATOS
--  Archivo   : botica_sistema.sql
--  Versión   : 3.0  |  Fecha: 2026-06-15
--  Contiene  : CREATE DATABASE + Tablas + Vistas + Inserts Coherentes
-- ============================================================

DROP DATABASE IF EXISTS `botica_sistema`;
CREATE DATABASE `botica_sistema`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `botica_sistema`;

SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- TABLA: USUARIOS
-- ============================================================
CREATE TABLE `usuarios` (
    `id`              INT              AUTO_INCREMENT PRIMARY KEY,
    `codigo_empleado` VARCHAR(20)      UNIQUE NOT NULL,
    `nombre`          VARCHAR(100)     NOT NULL,
    `email`           VARCHAR(100)     UNIQUE,
    `password`        VARCHAR(20)      NOT NULL,
    `rol`             ENUM('operario','gerente') DEFAULT 'operario',
    `sede`            VARCHAR(100)     DEFAULT 'Chiclayo',
    `palabra_clave`   VARCHAR(100)     NOT NULL,
    `activo`          TINYINT(1)       DEFAULT 1,
    `ultimo_login`    DATETIME         NULL,
    `created_at`      DATETIME         DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- TABLA: PRODUCTOS (Soporta Medicamentos y Golosinas/Snacks)
-- ============================================================
CREATE TABLE `productos` (
    `id`                INT               AUTO_INCREMENT PRIMARY KEY,
    `sku`               VARCHAR(50)       UNIQUE NOT NULL,
    `nombre`            VARCHAR(150)      NOT NULL,
    `categoria`         VARCHAR(60),
    `stock_total`       INT               NOT NULL DEFAULT 0,
    `ubicacion_gondola` VARCHAR(100),
    `precio_unitario`   DECIMAL(10,2),
    `venta_dia`         DECIMAL(8,2)      DEFAULT 0,
    `activo`            TINYINT(1)        DEFAULT 1,
    `created_at`        DATETIME          DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- TABLA: SEGMENTACION_INVENTARIO
-- ============================================================
CREATE TABLE `segmentacion_inventario` (
    `id`                        INT        AUTO_INCREMENT PRIMARY KEY,
    `producto_id`               INT        NOT NULL,
    `usuario_id`                INT,
    `stock_cliente_final`       INT        NOT NULL,
    `stock_revendedor`          INT        NOT NULL,
    `limite_compra_final`       INT        DEFAULT 0,
    `limite_compra_revendedor`  INT        DEFAULT 0,
    `motivo`                    TEXT,
    `activo`                    TINYINT(1) DEFAULT 1,
    `fecha_creacion`            DATETIME   DEFAULT CURRENT_TIMESTAMP,
    `updated_at`                DATETIME   DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`producto_id`) REFERENCES `productos`(`id`) ON DELETE RESTRICT,
    FOREIGN KEY (`usuario_id`)  REFERENCES `usuarios`(`id`)  ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================================
-- TABLA: ALERTAS_QUIEBRE (Columnas generadas automatizadas)
-- ============================================================
CREATE TABLE `alertas_quiebre` (
    `id`              INT           AUTO_INCREMENT PRIMARY KEY,
    `producto_id`     INT,
    `producto`        VARCHAR(150)  NOT NULL,
    `sku`             VARCHAR(50)   NOT NULL,
    `categoria`       VARCHAR(60),
    `unidades`        INT           NOT NULL,
    `stock_minimo`    INT           NOT NULL DEFAULT 0,
    `venta_dia`       DECIMAL(8,2)  NOT NULL DEFAULT 0,
    `horas_restantes` DECIMAL(8,2)  GENERATED ALWAYS AS (
                          CASE WHEN `venta_dia` > 0
                               THEN ROUND((`unidades` / `venta_dia`) * 24, 1)
                               ELSE 9999
                          END
                      ) STORED,
    `nivel`           ENUM('critico','urgente','advertencia','ok') GENERATED ALWAYS AS (
                          CASE
                              WHEN `venta_dia` <= 0                                  THEN 'ok'
                              WHEN (`unidades` / `venta_dia`) * 24 <= 24             THEN 'critico'
                              WHEN (`unidades` / `venta_dia`) * 24 <= 72             THEN 'urgente'
                              WHEN (`unidades` / `venta_dia`) * 24 <= 120            THEN 'advertencia'
                              ELSE 'ok'
                          END
                      ) STORED,
    `estado_transf`   VARCHAR(100)  DEFAULT 'Sin transferencia activa',
    `activo`          TINYINT(1)    DEFAULT 1,
    `updated_at`      DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`producto_id`) REFERENCES `productos`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================================
-- TABLA: CONTEOS_MANUALES
-- ============================================================
CREATE TABLE `conteos_manuales` (
    `id`            INT       AUTO_INCREMENT PRIMARY KEY,
    `producto_id`   INT       NOT NULL,
    `usuario_id`    INT       NOT NULL,
    `stock_sistema` INT       NOT NULL,
    `stock_contado` INT       NOT NULL,
    `diferencia`    INT       GENERATED ALWAYS AS (`stock_contado` - `stock_sistema`) STORED,
    `motivo`        TEXT,
    `estado`        ENUM('pendiente','aplicado','rechazado') DEFAULT 'pendiente',
    `fecha`         DATETIME  DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`producto_id`) REFERENCES `productos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`usuario_id`)  REFERENCES `usuarios`(`id`)  ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ============================================================
-- TABLA: HISTORIAL_AJUSTES
-- ============================================================
CREATE TABLE `historial_ajustes` (
    `id`               INT           AUTO_INCREMENT PRIMARY KEY,
    `producto_id`      INT           NOT NULL,
    `usuario_id`       INT           NOT NULL,
    `empleado_nombre`  VARCHAR(100),
    `accion`           ENUM('CREATE','UPDATE','DELETE','TOGGLE','CONTEO') NOT NULL,
    `campo_modificado` VARCHAR(80),
    `valor_anterior`   VARCHAR(255),
    `valor_nuevo`      VARCHAR(255),
    `motivo`           TEXT,
    `fecha`            DATETIME      DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`producto_id`) REFERENCES `productos`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`usuario_id`)  REFERENCES `usuarios`(`id`)  ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ============================================================
-- VISTAS DEL SISTEMA
-- ============================================================
CREATE OR REPLACE VIEW `v_alertas_activas` AS
SELECT
    a.id, a.producto_id, a.sku, a.producto, a.categoria, p.stock_total AS unidades,
    a.stock_minimo, a.venta_dia, a.horas_restantes, a.nivel, a.estado_transf, p.ubicacion_gondola
FROM `alertas_quiebre` a
LEFT JOIN `productos` p ON a.producto_id = p.id
WHERE a.activo = 1
ORDER BY a.horas_restantes ASC;

CREATE OR REPLACE VIEW `v_historial_completo` AS
SELECT
    h.id, h.fecha, h.empleado_nombre, u.rol AS empleado_rol, p.nombre AS producto_nombre,
    p.sku, h.accion, h.campo_modificado, h.valor_anterior, h.valor_nuevo, h.motivo
FROM `historial_ajustes` h
JOIN `productos` p ON h.producto_id = p.id
JOIN `usuarios`  u ON h.usuario_id  = u.id
ORDER BY h.fecha DESC;

SET FOREIGN_KEY_CHECKS = 1;