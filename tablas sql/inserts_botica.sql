-- ============================================================
--  BOTICA — DATOS SEMILLA (SEED DATA)
--  Archivo : inserts_botica.sql
--  Version : 3.0  |  Fecha: 2026-06-14
--  Contiene: usuarios, 54 productos EAN-13/SKU, alertas,
--            segmentacion, conteos e historial iniciales.
--  Ejecutar DESPUES de schema_botica.sql
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;

-- 1. USUARIOS
INSERT INTO `usuarios` 
    (`id`, `codigo_empleado`, `nombre`, `email`, `password`, `rol`, `sede`, `palabra_clave`)
VALUES
    (1, 'GER-2026-001', 'Carlos Mendoza', 'carlos.mendoza@botica.com.pe', 'admin123', 'gerente', 'Chiclayo', 'ger'),
    (2, 'OPE-2026-001', 'Rosa Herrera',   'rosa.herrera@botica.com.pe',   'Botica2026', 'operario', 'Chiclayo', 'ope');

-- 2. PRODUCTOS (Con IDs explícitos para blindar las Llaves Foráneas)
INSERT INTO `productos` 
    (`id`, `sku`, `nombre`, `categoria`, `stock_total`, `ubicacion_gondola`, `precio_unitario`, `venta_dia`)
VALUES
-- --- MEDICAMENTOS ESENCIALES ---
(1,  '7750001000016', 'Paracetamol 500mg Blíster x10', 'Medicamentos', 144, 'Estantería A - Fila 1', 2.00, 15.0),
(2,  '7750001000023', 'Ibuprofeno 400mg Blíster x10', 'Medicamentos', 120, 'Estantería A - Fila 1', 2.50, 12.0),
(3,  '7750001000030', 'Amoxicilina 500mg Blíster x10', 'Medicamentos', 90,  'Estantería A - Fila 2', 4.00, 8.0),
(4,  '7750001000047', 'Loratadina 10mg Blíster x10', 'Medicamentos', 200, 'Estantería A - Fila 2', 3.00, 10.0),
(5,  '7750001000054', 'Omeprazol 20mg Blíster x10', 'Medicamentos', 180, 'Estantería A - Fila 3', 3.50, 9.0),
(6,  '7750001000078', 'Apronax 550mg Blíster x4', 'Medicamentos', 85,  'Estantería B - Fila 1', 5.50, 11.0),
(7,  '7750001000085', 'Panadol Antigripal Blíster x2', 'Medicamentos', 300, 'Estantería B - Fila 1', 3.00, 22.0),
(8,  '7750001000108', 'Bismutol Suspensión Frasco 150ml', 'Medicamentos', 40,  'Estantería B - Fila 3', 16.50, 4.0),
(9,  '7750001000115', 'Sal de Andrews Caja x50 Sobres', 'Medicamentos', 60,  'Estantería C - Fila 1', 35.00, 2.5),
-- CASO CRÍTICO 1: Nastizol sin stock en sistema
(10, '7750001000139', 'Nastizol Antigripal Elixir Frasco', 'Medicamentos', 0,   'Estantería B - Fila 2', 14.00, 3.5), 

-- --- CUIDADO PERSONAL E HIGIENE ---
(11, '7702001023451', 'Jabón Líquido Protex Aloe 400ml', 'Cuidado Personal', 45, 'Góndola Higiene - Nivel 1', 11.90, 3.0),
(12, '7750123000452', 'Crema Dental Colgate Total 12 90g', 'Cuidado Personal', 80, 'Góndola Higiene - Nivel 2', 7.50, 5.0),
(13, '7501006561439', 'Shampoo Pantene Restauración 400ml', 'Cuidado Personal', 180, 'Góndola Higiene - Nivel 3', 17.90, 4.0),
-- CASO CRÍTICO 2: Alcohol en Gel con stock peligroso de 5 unidades
(14, '7750023450011', 'Alcohol en Gel Antibacterial 500ml', 'Cuidado Personal', 5, 'Mostrador Principal', 9.50, 3.0), 
-- CASO CRÍTICO 3: Mascarillas KN95 al límite
(15, '7750987654321', 'Mascarillas KN95 Empaque x10', 'Cuidado Personal', 3,   'Mostrador Principal', 15.00, 0.8), 

-- --- BIENESTAR Y SUEROS ---
(16, '7501031311306', 'Ensure Clinical Vainilla Lata 400g', 'Bienestar', 15, 'Góndola Nutrición', 55.00, 1.2),
(17, '7750006002312', 'Suero Oral Frutiflex Piña 500ml', 'Bienestar', 64, 'Vitrina Fría', 4.50, 6.0),

-- --- SNACKS Y GOLOSINAS (Adicionales de mostrador de Botica) ---
(18, '7500435064897', 'Papas Lays Clásicas 42g', 'Snacks y Golosinas', 100, 'Caramelera Mostrador', 2.50, 12.0),
(19, '7500435028424', 'Doritos Nacho 55g', 'Snacks y Golosinas', 90,  'Caramelera Mostrador', 3.00, 10.0),
(20, '7750034000045', 'Chocolate Sublime Extragrande 40g', 'Snacks y Golosinas', 200, 'Caja Registradora', 1.80, 22.0),
(21, '7750034000014', 'Galleta Casino Chocolate 6u', 'Snacks y Golosinas', 150, 'Caramelera Mostrador', 1.20, 18.0),
(22, '7750034000022', 'Galleta Morochas Nestlé 6u', 'Snacks y Golosinas', 130, 'Caramelera Mostrador', 1.20, 15.0),
-- CASO DE ADVERTENCIA: Caramelos Halls con alta rotación y stock bajando
(23, '0038000591754', 'Caramelos Halls Menta Fuerte 9u', 'Snacks y Golosinas', 36, 'Caja Registradora', 1.50, 5.0), 
(24, '0012546000012', 'Chicles Trident Menta 14g', 'Snacks y Golosinas', 80,  'Caja Registradora', 2.00, 8.0),

-- --- BEBIDAS SIN ALCOHOL ---
(25, '7758580100019', 'Inca Kola Botella Personal 500ml', 'Bebidas', 180, 'Vitrina Fría', 3.00, 25.0),
(26, '5449000000996', 'Coca Cola Botella Personal 500ml', 'Bebidas', 200, 'Vitrina Fría', 3.00, 28.0),
(27, '7750095000011', 'Agua San Luis Sin Gas 625ml', 'Bebidas', 200, 'Vitrina Fría', 1.50, 22.0);

-- 3. ALERTAS DE QUIEBRE (Perfectamente mapeadas con los IDs de arriba)
INSERT INTO `alertas_quiebre`
    (`producto_id`, `producto`, `sku`, `categoria`, `unidades`, `stock_minimo`, `venta_dia`, `estado_transf`)
VALUES
    -- Crítico: ID 10 (Nastizol) está en Stock 0
    (10, 'Nastizol Antigripal Elixir Frasco', '7750001000139', 'Medicamentos', 0, 10, 3.5, 'Urgente - sin stock'),
    -- Crítico: ID 14 (Alcohol en gel) está en Stock 5 con alta demanda
    (14, 'Alcohol en Gel Antibacterial 500ml', '7750023450011', 'Cuidado Personal', 5, 20, 3.0, 'Pedido central generado'),
    -- Crítico: ID 15 (Mascarillas) stock 3
    (15, 'Mascarillas KN95 Empaque x10', '7750987654321', 'Cuidado Personal', 3, 10, 0.8, 'Sin transferencia activa'),
    -- Advertencia: ID 23 (Halls Menta) stock bajo por alta venta en caja
    (23, 'Caramelos Halls Menta Fuerte 9u', '0038000591754', 'Snacks y Golosinas', 36, 40, 5.0, 'Pedido en proceso');

-- 4. CONTEOS MANUALES
INSERT INTO `conteos_manuales`
    (`producto_id`, `usuario_id`, `stock_sistema`, `stock_contado`, `motivo`, `estado`)
VALUES
    (1,  2, 150, 144, 'Mermas detectadas: 6 blísteres dañados/humedecidos en almacén', 'aplicado'),
    (13, 2, 190, 180, 'Conteo de rutina en góndola de higiene - turno mañana', 'aplicado'),
    (10, 2,   2,   0, 'Quiebre confirmado en inspección visual de estanterías', 'aplicado');

-- 5. HISTORIAL DE AJUSTES
INSERT INTO `historial_ajustes`
    (`producto_id`, `usuario_id`, `empleado_nombre`, `accion`, `campo_modificado`, `valor_anterior`, `valor_nuevo`, `motivo`, `fecha`)
VALUES
    (1,  1, 'Carlos Mendoza', 'CREATE', NULL, NULL, NULL, 'Carga inicial e inventariado del catálogo de la Botica', NOW() - INTERVAL 1 DAY),
    (13, 2, 'Rosa Herrera',   'CONTEO', 'stock_total', '190', '180', 'Ajuste regular por conteo matutino', NOW() - INTERVAL 6 HOUR),
    (10, 2, 'Rosa Herrera',   'CONTEO', 'stock_total', '2',   '0',   'Alerta de quiebre - Nastizol Agotado', NOW() - INTERVAL 3 HOUR);

SET FOREIGN_KEY_CHECKS = 1;
-- ============================================================
-- FIN DEL SCRIPT CORREGIDO
-- Acceso inicial: codigo=GER-2026-001 | password=admin123
-- ============================================================