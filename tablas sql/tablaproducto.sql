
CREATE TABLE productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    categoria VARCHAR(50),
    stock_total INT NOT NULL
) ENGINE=InnoDB;


CREATE TABLE  segmentacion_inventario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    producto_id INT NOT NULL,
    stock_cliente_final INT NOT NULL,
    stock_revendedor INT NOT NULL,
    limite_compra_final INT DEFAULT 0,
    limite_compra_revendedor INT DEFAULT 0,
    motivo TEXT,
    activo TINYINT(1) DEFAULT 1,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
) ENGINE=InnoDB;

-- 3. Insertar productos iniciales
INSERT INTO productos (sku, nombre, categoria, stock_total) VALUES
('LAC-001', 'Leche Gloria Entera 1L', 'Lácteos', 240),
('ARR-002', 'Arroz Costeño 5kg', 'Granos', 150),
('ACE-003', 'Aceite Primor 1L', 'Aceites', 80),
('AZU-004', 'Azúcar Rubia 1kg', 'Abarrotes', 320),
('DET-005', 'Detergente Ariel 2kg', 'Limpieza', 95);