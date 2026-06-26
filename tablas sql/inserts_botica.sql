-- ============================================================
--  BOTICA CENTRAL — DATOS SEMILLA (SEED DATA)
--  Archivo : inserts_botica.sql
--  Version : 2.0  |  Fecha: 2026-06-06
--  Contiene: usuarios, 54 productos EAN-13/SKU, alertas,
--            segmentacion, conteos e historial iniciales.
--  Ejecutar DESPUES de schema_botica.sql
-- ============================================================

USE `botica_sistema`;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- USUARIOS (1 gerente + 1 operario)
-- ============================================================
INSERT INTO `usuarios`
    (`codigo_empleado`, `nombre`, `email`, `password`, `rol`, `sede`, `palabra_clave`)
VALUES
    ('GER-2026-001', 'Carlos Mendoza',   'carlos.mendoza@boticacentral.com.pe',  'admin123',   'gerente',  'Chiclayo', 'ger'),
    ('OPE-2026-001', 'Rosa Herrera',     'rosa.herrera@boticacentral.com.pe',    'Botica2026', 'operario', 'Chiclayo', 'ope');

-- ============================================================
-- PRODUCTOS — 50 ITEMS COHERENTES (MEDICAMENTOS + CONVENIENCIA)
-- ============================================================
INSERT INTO `productos`
    (`sku`, `nombre`, `categoria`, `stock_total`, `ubicacion_gondola`, `precio_unitario`, `venta_dia`, `stock_minimo`)
VALUES

-- MEDICAMENTOS Y BIENESTAR (IDs 1 al 15)
('7750101001235', 'Panadol Antigripal Tableta Caja x 2u', 'Medicamentos OTC', 144, 'Góndola A - Analgésicos', 2.50, 18.0, 20),
('7750101004564', 'Ibuprofeno 400mg Tableta x 10u', 'Medicamentos OTC', 240, 'Góndola A - Analgésicos', 3.00, 30.0, 20),
('7750202001112', 'Amoxicilina 500mg Cápsula x 10u', 'Medicamentos Retenida', 120, 'Estante Interno - Antibióticos', 8.50, 15.0, 20),
('7750202002225', 'Cetirizina 10mg Tableta x 10u', 'Medicamentos OTC', 200, 'Góndola B - Antialérgicos', 4.50, 22.0, 20),
('7750303003332', 'Omeprazol 20mg Cápsula x 10u', 'Medicamentos OTC', 96, 'Góndola C - Gastro', 5.00, 12.0, 20),
('7750303004448', 'Apronax 550mg Tableta x 4u', 'Medicamentos OTC', 48, 'Góndola A - Analgésicos', 7.20, 8.0, 20),
('7750404005551', 'Nastizol Antigripal Jarabe 60ml', 'Medicamentos OTC', 36, 'Góndola B - Infantil', 14.50, 5.0, 20),
('7501001145621', 'Bismutol Suspensión Oral 150ml', 'Medicamentos OTC', 72, 'Góndola C - Gastro', 16.50, 9.0, 20),
('7750909001010', 'Sal de Andrews Efervescente x 5u', 'Medicamentos OTC', 60, 'Mostrador Principal', 1.50, 7.0, 20),
('7750123000987', 'Aspirina 100mg Tableta x 10u', 'Medicamentos OTC', 24, 'Góndola A - Analgésicos', 2.00, 3.0, 5),
('7501345678912', 'VapoRub Ungüento Pote 50g', 'Medicamentos OTC', 18, 'Góndola B - Alivio Respiratorio', 12.90, 2.0, 5),
('7750555001212', 'Alcohol Etílico 96 Grados 250ml', 'Cuidado de la Salud', 5, 'Góndola D - Primeros Auxilios', 4.50, 1.5, 5),
('0012000801123', 'Glucerna Líquida Vainilla Lata 237ml', 'Nutrición Especializada', 3, 'Góndola F - Suplementos', 11.50, 0.8, 5), -- ID 13: Bajo Stock Crítico
('4003754009997', 'Ensure Advance Vainilla Líquido 220ml', 'Nutrición Especializada', 8, 'Góndola F - Suplementos', 12.50, 1.2, 5),
('0050918005556', 'Suero Oral Electrolit Coco 625ml', 'Cuidado de la Salud', 12, 'Refrigerador de Turno', 8.50, 2.0, 5),

-- BEBIDAS DE CONVENIENCIA (IDs 16 al 24)
('7758580100019', 'Inca Kola Mediana Personal 500ml', 'Bebidas y Aguas', 180, 'Refrigerador de Turno', 3.00, 25.0, 30),
('7758580100033', 'Agua Mineral San Mateo 600ml s/g', 'Bebidas y Aguas', 120, 'Refrigerador de Turno', 2.00, 14.0, 15), -- ID 17: Ajuste de conteo
('5449000000996', 'Coca Cola Personal 500ml', 'Bebidas y Aguas', 200, 'Refrigerador de Turno', 3.00, 28.0, 30),
('5449000131805', 'Coca Cola Sin Azúcar 500ml', 'Bebidas y Aguas', 100, 'Refrigerador de Turno', 3.00, 12.0, 15),
('5449000004567', 'Sprite Botella Personal 500ml', 'Bebidas y Aguas', 80, 'Refrigerador de Turno', 2.80, 9.0, 30),
('5449000027030', 'Fanta Naranja Personal 500ml', 'Bebidas y Aguas', 60, 'Refrigerador de Turno', 2.80, 8.0, 30),
('7750127000014', 'Agua Cielo con Gas 625ml', 'Bebidas y Aguas', 150, 'Refrigerador de Turno', 1.50, 20.0, 30),
('7750095000011', 'Agua Cielo sin Gas 625ml', 'Bebidas y Aguas', 200, 'Refrigerador de Turno', 1.50, 22.0, 30),
('7750095000028', 'Bebida Hidratante Gatorade Confort 500ml', 'Bebidas y Aguas', 80, 'Refrigerador de Turno', 3.50, 8.0, 15),

-- ENERGIZANTES Y SUPLEMENTOS (IDs 25 al 28)
('9002490100070', 'Red Bull Energy Drink 250ml', 'Energizantes', 48, 'Refrigerador de Turno', 7.50, 8.0, 10),
('7750580000013', 'Volt Citrus Energizante 475ml', 'Energizantes', 72, 'Refrigerador de Turno', 3.00, 10.0, 10),
('0070847012108', 'Monster Energy Original 473ml', 'Energizantes', 36, 'Refrigerador de Turno', 8.50, 5.0, 10),
('0070847016465', 'Monster Energy Ultra Zero 473ml', 'Energizantes', 24, 'Refrigerador de Turno', 8.50, 3.0, 10),

-- SNACKS Y GOLOSINAS (IDs 29 al 40)
('7500435064897', 'Papas Lays Clásicas 42g', 'Snacks y Galletas', 100, 'Estante de Conveniencia 1', 2.50, 12.0, 15),
('7500435064910', 'Papas Lays Ondas Paprika 55g', 'Snacks y Galletas', 80, 'Estante de Conveniencia 1', 3.20, 9.0, 15),
('7500435028424', 'Doritos Mega Queso 55g', 'Snacks y Galletas', 90, 'Estante de Conveniencia 1', 3.00, 10.0, 15),
('0038000845765', 'Pringles Original Pequeña 40g', 'Snacks y Galletas', 60, 'Estante de Conveniencia 1', 4.50, 7.0, 15),
('7751450000011', 'Cuates Fritura Picante 35g', 'Snacks y Galletas', 120, 'Estante de Conveniencia 1', 1.50, 14.0, 15),
('7750034000014', 'Galleta Casino Chocolate 6u', 'Snacks y Galletas', 150, 'Estante de Conveniencia 2', 1.20, 18.0, 15),
('7750034000021', 'Chocolate Sublime Clásico 30g', 'Golosinas y Dulces', 0, 'Mostrador de Caja', 1.50, 15.0, 15), -- ID 35: Agotado / Quiebre
('0044000032678', 'Galleta Oreo Original Tubo', 'Snacks y Galletas', 80, 'Estante de Conveniencia 2', 2.50, 9.0, 15),
('0030100058152', 'Galleta Ritz Crackers Original', 'Snacks y Galletas', 60, 'Estante de Conveniencia 2', 2.00, 7.0, 15),
('7750034000038', 'Galleta Margarita Sayón 6u', 'Snacks y Galletas', 100, 'Estante de Conveniencia 2', 1.00, 12.0, 15),
('7750218000015', 'Barra de Cereal Ángel Fresa', 'Snacks y Galletas', 80, 'Estante de Conveniencia 2', 1.50, 9.0, 15),
('7750034000045', 'Chocolate Princesa Barra 35g', 'Golosinas y Dulces', 200, 'Mostrador de Caja', 1.80, 22.0, 20),

-- CUIDADO PERSONAL (IDs 41 al 44)
('7750250000011', 'Crema Dental Colgate Triple Acción 75ml', 'Cuidado Personal', 40, 'Góndola E - Dental', 5.50, 6.0, 8),
('7750250000028', 'Shampoo Head & Shoulders Limpieza 180ml', 'Cuidado Personal', 35, 'Góndola E - Cabello', 14.50, 5.0, 8),
('7750250000035', 'Jabón Líquido Protex Antibacterial 221ml', 'Cuidado Personal', 30, 'Góndola E - Baño', 11.00, 4.0, 8),
('7750250000042', 'Desodorante Rexona Clinical Men 48g', 'Cuidado Personal', 25, 'Góndola E - Higiene', 18.90, 3.0, 8),

-- VARIOS DE MOSTRADOR / CONFITERÍA DE CAJA (IDs 45 al 50)
('7702009023110', 'Pastillas Halls Menta Extra Fuerte 9u', 'Golosinas y Dulces', 0, 'Mostrador de Caja', 1.20, 3.5, 10), -- ID 45: Crítico Absoluto (0)
('7702009026661', 'Chicles Trident Menta Paquete 14g', 'Golosinas y Dulces', 5, 'Mostrador de Caja', 1.50, 3.0, 12), -- ID 46: Alerta Bajo Mínimo
('7702009030002', 'Chupetín Globo Pop Unidad', 'Golosinas y Dulces', 10, 'Mostrador de Caja', 0.50, 2.5, 8),
('0012546000012', 'Gomitas Ambrosoli Frugele 90g', 'Golosinas y Dulces', 80, 'Estante de Conveniencia 2', 3.80, 8.0, 20),
('0038000591754', 'Mentos Fruit Caramelos 37g', 'Golosinas y Dulces', 90, 'Mostrador de Caja', 1.50, 10.0, 20),
('7750034000052', 'Cura de Gasa Protectora Hansaplast 10u', 'Cuidado de la Salud', 120, 'Góndola D - Primeros Auxilios', 4.50, 12.0, 20);


-- ============================================================
-- ALERTAS DE QUIEBRE (Relación directa con stocks críticos)
-- ============================================================
INSERT INTO `alertas_quiebre` (`producto_id`, `estado_transf`)
VALUES
    (45, 'Urgente - sin stock'),       -- Pastillas Halls Menta
    (46, 'Pedido generado'),           -- Chicles Trident Menta
    (13, 'Sin transferencia activa');  -- Glucerna Líquida


-- ============================================================
-- CONTEOS MANUALES DE APERTURA (Adaptado al negocio de botica)
-- ============================================================
INSERT INTO `conteos_manuales`
    (`producto_id`, `usuario_id`, `stock_sistema`, `stock_contado`, `motivo`, `estado`)
VALUES
    (1,  2, 150, 144, 'Conteo de apertura - 6 tabletas dañadas/blísters rotos en caja', 'aplicado'),
    (17, 2, 190, 180, 'Conteo rutina turno mañana - ajuste góndola bebidas', 'aplicado'),
    (35, 2,   2,   0, 'Quiebre confirmado - faltante físico de Sublime en caja', 'aplicado');


-- ============================================================
-- HISTORIAL INICIAL (Logs operativos coherentes)
-- ============================================================
INSERT INTO `historial_ajustes`
    (`producto_id`, `usuario_id`, `empleado_nombre`, `accion`,
     `campo_modificado`, `valor_anterior`, `valor_nuevo`, `motivo`, `fecha`)
VALUES
    (1,  1, 'Carlos Mendoza', 'CREATE', NULL,          NULL,  NULL,  'Carga inicial del catálogo maestro Botica Central', NOW() - INTERVAL 1 DAY),
    (17, 2, 'Rosa Herrera',   'CONTEO', 'stock_total', '190', '180', 'Conteo rutina apertura - verificación San Mateo',     NOW() - INTERVAL 6 HOUR),
    (35, 2, 'Rosa Herrera',   'CONTEO', 'stock_total', '2',   '0',   'Quiebre detectado - Chocolate Sublime agotado',      NOW() - INTERVAL 3 HOUR);

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- FIN DEL SCRIPT DE DATOS
-- Acceso inicial: codigo=GER-2026-001 | password=admin123
-- ============================================================