-- ============================================================
--  EL HUECO RESTOBAR — DATOS SEMILLA (SEED DATA)
--  Archivo : inserts_elhueco.sql
--  Version : 2.0  |  Fecha: 2026-06-06
--  Contiene: usuarios, 54 productos EAN-13/SKU, alertas,
--            segmentacion, conteos e historial iniciales.
--  Ejecutar DESPUES de schema_elhueco.sql
-- ============================================================

USE `elHueco`;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- USUARIOS (1 gerente + 1 operario)
-- ============================================================
INSERT INTO `usuarios`
    (`codigo_empleado`, `nombre`, `email`, `password`, `rol`, `sede`, `palabra_clave`)
VALUES
    ('GER-2026-001', 'Carlos Mendoza',   'carlos.mendoza@elhueco.com.pe',  'admin123',   'gerente',  'Chiclayo', 'ger'),
    ('OPE-2026-001', 'Rosa Herrera',     'rosa.herrera@elhueco.com.pe',    'Hueco2026',  'operario', 'Chiclayo', 'ope');


-- ============================================================
-- PRODUCTOS — 54 ITEMS CON EAN-13 / SKU REALES DEL MERCADO PERUANO
--
-- Prefijos EAN-13 usados:
--   7751xxx  -> Backus (Pilsen, Cristal)
--   7753xxx  -> Backus premium / importados
--   7758xxx  -> Inca Kola / Coca-Cola Peru
--   7750xxx  -> Genericos Peru
--   6009xxx  -> Sudafrica (Jagermeister proxy)
--   8413xxx  -> Espana (Whisky proxy)
--   0012000x -> USA (Corona, Red Bull, Monster, Pringles)
--   7500xxx  -> Mexico (Doritos, Lays, Sabritas)
--   0070xxx  -> USA Snacks
-- ============================================================
INSERT INTO `productos`
    (`sku`, `nombre`, `categoria`, `stock_total`, `ubicacion_gondola`, `precio_unitario`, `venta_dia`)
VALUES

-- ============================================================
-- CERVEZAS Y LICORES
-- ============================================================
('7751010000017', 'Cerveza Pilsen Callao 650ml Bot.',  'Licores y Cervezas', 144, 'Refrigerador A, estante 1',  5.50,  18.0),
('7751010000024', 'Cerveza Pilsen Callao Lata 355ml', 'Licores y Cervezas', 240, 'Refrigerador A, estante 1',  3.80,  30.0),
('7751020000015', 'Cerveza Cristal 650ml Bot.',        'Licores y Cervezas', 120, 'Refrigerador A, estante 2',  5.20,  15.0),
('7751020000022', 'Cerveza Cristal Lata 355ml',        'Licores y Cervezas', 200, 'Refrigerador A, estante 2',  3.60,  22.0),
('7751030000012', 'Cerveza Cusquena Dorada 620ml',     'Licores y Cervezas',  96, 'Refrigerador A, estante 3',  6.00,  12.0),
('7751030000029', 'Cerveza Cusquena Trigo 620ml',      'Licores y Cervezas',  48, 'Refrigerador A, estante 3',  6.50,   8.0),
('7751030000036', 'Cerveza Cusquena Negra 620ml',      'Licores y Cervezas',  36, 'Refrigerador A, estante 3',  6.50,   5.0),
('0012000801334', 'Cerveza Corona Extra 355ml',         'Licores y Cervezas',  72, 'Refrigerador B, estante 1',  8.50,   9.0),
('5410228087681', 'Cerveza Stella Artois 330ml',        'Licores y Cervezas',  60, 'Refrigerador B, estante 1',  7.90,   7.0),
('7750621000012', 'Ron Cartavio Superior 750ml',        'Licores y Cervezas',  24, 'Licoreria, estante 1',      49.90,   3.0),
('7750800000018', 'Pisco Cuatro Gallos Puro 750ml',    'Licores y Cervezas',  18, 'Licoreria, estante 2',      39.90,   2.0),
('5000267023779', 'Whisky Red Label 750ml',             'Licores y Cervezas',   5, 'Licoreria, estante 3',      89.90,   1.5),
('5000267024028', 'Whisky Black Label 750ml',           'Licores y Cervezas',   3, 'Licoreria, estante 3',     149.90,   0.8),
('4003754001014', 'Jagermeister 700ml',                 'Licores y Cervezas',   8, 'Licoreria, estante 4',      89.90,   1.2),
('0050918001350', 'Vodka Smirnoff 750ml',               'Licores y Cervezas',  12, 'Licoreria, estante 2',      49.90,   2.0),

-- ============================================================
-- BEBIDAS SIN ALCOHOL
-- ============================================================
('7758580100019', 'Inca Kola 500ml Personal',           'Bebidas',            180, 'Refrigerador C, estante 1',  3.00,  25.0),
('7758580100033', 'Inca Kola 1.5L',                     'Bebidas',            120, 'Refrigerador C, estante 1',  5.50,  14.0),
('5449000000996', 'Coca Cola 500ml Personal',            'Bebidas',            200, 'Refrigerador C, estante 2',  3.00,  28.0),
('5449000131805', 'Coca Cola 1.5L',                      'Bebidas',            100, 'Refrigerador C, estante 2',  5.50,  12.0),
('5449000004567', 'Sprite 500ml',                        'Bebidas',             80, 'Refrigerador C, estante 3',  2.80,   9.0),
('5449000027030', 'Fanta Naranja 500ml',                 'Bebidas',             60, 'Refrigerador C, estante 3',  2.80,   8.0),
('7750127000014', 'Agua San Mateo 625ml',                'Bebidas',            150, 'Refrigerador D, estante 1',  2.00,  20.0),
('7750095000011', 'Agua Cielo 625ml',                    'Bebidas',            200, 'Refrigerador D, estante 1',  1.50,  22.0),
('7750095000028', 'Agua Cielo 2.5L',                     'Bebidas',             80, 'Refrigerador D, estante 2',  3.50,   8.0),

-- ============================================================
-- ENERGIZANTES
-- ============================================================
('9002490100070', 'Red Bull Energy 250ml',               'Energizantes',        48, 'Refrigerador D, estante 3',  6.90,   8.0),
('7750580000013', 'Volt Citrus 475ml',                   'Energizantes',        72, 'Refrigerador D, estante 3',  3.50,  10.0),
('0070847012108', 'Monster Energy Green 473ml',          'Energizantes',        36, 'Refrigerador D, estante 4',  7.90,   5.0),
('0070847016465', 'Monster Energy Ultra 473ml',          'Energizantes',        24, 'Refrigerador D, estante 4',  7.90,   3.0),

-- ============================================================
-- SNACKS Y GALLETAS
-- ============================================================
('7500435064897', 'Lays Clasicas 42g',                   'Snacks',             100, 'Gondola 1, estante 1',       2.50,  12.0),
('7500435064910', 'Lays Ondas 55g',                      'Snacks',              80, 'Gondola 1, estante 1',       3.20,   9.0),
('7500435028424', 'Doritos Nacho 55g',                   'Snacks',              90, 'Gondola 1, estante 2',       3.00,  10.0),
('0038000845765', 'Pringles Original 40g',               'Snacks',              60, 'Gondola 1, estante 2',       4.50,   7.0),
('7751450000011', 'Cuates Fritura 35g',                  'Snacks',             120, 'Gondola 1, estante 3',       1.50,  14.0),
('7750034000014', 'Galleta Casino Chocolate 6u',         'Galletas',           150, 'Gondola 2, estante 1',       2.00,  18.0),
('7750034000021', 'Galleta Morochas 6u',                 'Galletas',           130, 'Gondola 2, estante 1',       2.00,  15.0),
('0044000032678', 'Oreo Original 119g',                  'Galletas',            80, 'Gondola 2, estante 2',       4.00,   9.0),
('0030100058152', 'Ritz Original 100g',                  'Galletas',            60, 'Gondola 2, estante 2',       3.50,   7.0),
('7750034000038', 'Galleta Margarita 6u',                'Galletas',           100, 'Gondola 2, estante 3',       2.00,  12.0),
('7750218000015', 'Bimboletes 6u',                       'Galletas',            80, 'Gondola 2, estante 3',       2.50,   9.0),
('7750034000045', 'Chocolate Sublime 32g',               'Confiteria',         200, 'Gondola 3, estante 1',       1.50,  22.0),

-- ============================================================
-- HELADOS D'ONOFRIO
-- ============================================================
('7750250000011', 'Helado Jet Chocolate 70ml',           'Helados',             40, 'Congelador, estante 1',      2.50,   6.0),
('7750250000028', 'Helado Sin Parar 70ml',               'Helados',             35, 'Congelador, estante 1',      2.50,   5.0),
('7750250000035', 'Helado Frio Rico Naranja 70ml',       'Helados',             30, 'Congelador, estante 1',      2.00,   4.0),
('7750250000042', 'Helado Alaska Cream 70ml',            'Helados',             25, 'Congelador, estante 2',      3.00,   3.0),

-- ============================================================
-- VARIOS MINIMARKET
-- ============================================================
('7702009023110', 'Cigarros Lucky Strike Box 20u',       'Tabacos',              0, 'Caja registradora',         13.00,   3.5),
('7702009026661', 'Cigarros Pall Mall Rojo Box 20u',     'Tabacos',              5, 'Caja registradora',         11.00,   3.0),
('7702009030002', 'Cigarros Hamilton Box 20u',           'Tabacos',             10, 'Caja registradora',          9.50,   2.5),
('0012546000012', 'Chicles Trident Menta 14g',           'Confiteria',          80, 'Gondola 3, estante 2',       1.50,   8.0),
('0038000591754', 'Halls Menta Fuerte 9u',               'Confiteria',          90, 'Gondola 3, estante 2',       1.50,  10.0),
('7750034000052', 'Chupetines Globo 10u',                'Confiteria',         120, 'Gondola 3, estante 3',       1.00,  12.0);


-- ============================================================
-- ALERTAS DE QUIEBRE (productos con stock critico o en 0)
-- ============================================================
INSERT INTO `alertas_quiebre`
    (`producto_id`, `producto`, `sku`, `categoria`, `unidades`, `stock_minimo`, `venta_dia`, `estado_transf`)
VALUES
    -- Critico: stock = 0
    (35, 'Cigarros Lucky Strike Box 20u', '7702009023110', 'Tabacos',          0,  10,  3.5, 'Urgente - sin stock'),
    -- Critico: stock = 5 con venta alta
    (36, 'Cigarros Pall Mall Rojo Box 20u', '7702009026661', 'Tabacos',        5,  12,  3.0, 'Pedido generado'),
    -- Critico: Whisky Black Label stock = 3
    (13, 'Whisky Black Label 750ml', '5000267024028', 'Licores y Cervezas',    3,   6,  0.8, 'Sin transferencia activa'),
    -- Urgente: stock = 5, venta moderada
    (36, 'Cigarros Pall Mall Rojo Box 20u', '7702009026661', 'Tabacos',        5,  12,  3.0, 'Pedido pendiente de aprobacion'),
    -- Advertencia: Cusquena Negra stock bajo
    (7,  'Cerveza Cusquena Negra 620ml', '7751030000036', 'Licores y Cervezas', 36,  30,  5.0, 'Pedido en proceso');


-- ============================================================
-- CONTEOS MANUALES DE APERTURA
-- ============================================================
INSERT INTO `conteos_manuales`
    (`producto_id`, `usuario_id`, `stock_sistema`, `stock_contado`, `motivo`, `estado`)
VALUES
    (1,  2,  150, 144, 'Conteo de apertura - 6 botellas rotas en despacho', 'aplicado'),
    (17, 2,  190, 180, 'Conteo rutina turno mañana', 'aplicado'),
    (35, 2,    2,   0, 'Quiebre confirmado - faltante en caja', 'aplicado');


-- ============================================================
-- HISTORIAL INICIAL
-- ============================================================
INSERT INTO `historial_ajustes`
    (`producto_id`, `usuario_id`, `empleado_nombre`, `accion`,
     `campo_modificado`, `valor_anterior`, `valor_nuevo`, `motivo`, `fecha`)
VALUES
    (1,  1, 'Carlos Mendoza', 'CREATE', NULL,          NULL,  NULL,  'Carga inicial catalogo El Hueco',           NOW() - INTERVAL 1 DAY),
    (17, 2, 'Rosa Herrera',   'CONTEO', 'stock_total', '190', '180', 'Conteo rutina apertura',                    NOW() - INTERVAL 6 HOUR),
    (35, 2, 'Rosa Herrera',   'CONTEO', 'stock_total', '2',   '0',   'Quiebre detectado - Lucky Strike agotado',  NOW() - INTERVAL 3 HOUR);


SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- FIN DEL SCRIPT DE DATOS
-- Acceso inicial: codigo=GER-2026-001 | password=admin123
-- Ejecutar schema_elhueco.sql PRIMERO
-- ============================================================
