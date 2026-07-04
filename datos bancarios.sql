-- 1. LIMPIEZA PREVIA TOTAL
DROP VIEW IF EXISTS vw_dashboard_bancario CASCADE;
DROP TABLE IF EXISTS pagos CASCADE;
DROP TABLE IF EXISTS prestamos CASCADE;
DROP TABLE IF EXISTS clientes CASCADE;
DROP TABLE IF EXISTS sucursales CASCADE;

-- 2. CREACIÓN DE TABLAS RELACIONALES
CREATE TABLE sucursales (
    sucursal_id SERIAL PRIMARY KEY,
    nombre_sucursal VARCHAR(50),
    ciudad VARCHAR(50),
    presupuesto_asignado NUMERIC(12,2)
);

CREATE TABLE clientes (
    cliente_id SERIAL PRIMARY KEY,
    sucursal_id INT REFERENCES sucursales(sucursal_id),
    genero VARCHAR(15),
    edad INT,
    ingreso_anual NUMERIC(10,2),
    puntaje_crediticio INT,
    nivel_riesgo VARCHAR(20)
);

CREATE TABLE prestamos (
    prestamo_id SERIAL PRIMARY KEY,
    cliente_id INT REFERENCES clientes(cliente_id),
    tipo_prestamo VARCHAR(40),
    monto_prestamo NUMERIC(10,2),
    tasa_interes NUMERIC(5,2),
    plazo_meses INT,
    estado_prestamo VARCHAR(30)
);

CREATE TABLE pagos (
    pago_id SERIAL PRIMARY KEY,
    prestamo_id INT REFERENCES prestamos(prestamo_id),
    monto_pagado NUMERIC(10,2),
    fecha_pago DATE
);

-- 3. INSERCIÓN DE SUCURSALES (Contexto local y realista)
INSERT INTO sucursales (nombre_sucursal, ciudad, presupuesto_asignado) VALUES
('Agencia Central', 'Lima', 5000000.00),
('Agencia Calle Real', 'Huancayo', 2500000.00),
('Agencia Yanahuara', 'Arequipa', 3000000.00),
('Agencia El Sol', 'Cusco', 2000000.00),
('Agencia Víctor Larco', 'Trujillo', 2800000.00);

-- 4. GENERACIÓN MASIVA DE CLIENTES (250 Clientes Automáticos)
INSERT INTO clientes (sucursal_id, genero, edad, ingreso_anual, puntaje_crediticio)
SELECT 
    floor(random() * 5 + 1)::int AS sucursal_id,
    (ARRAY['Masculino', 'Femenino'])[floor(random() * 2 + 1)] AS genero,
    floor(random() * (68 - 21 + 1) + 21)::int AS edad,
    floor(random() * (150000 - 18000 + 1) + 18000)::numeric(10,2) AS ingreso_anual,
    floor(random() * (850 - 450 + 1) + 450)::int AS puntaje_crediticio
FROM generate_series(1, 250);

-- Actualizar nivel de riesgo en base al puntaje crediticio
UPDATE clientes SET nivel_riesgo = 
    CASE 
        WHEN puntaje_crediticio >= 720 THEN 'Bajo'
        WHEN puntaje_crediticio >= 600 THEN 'Medio'
        ELSE 'Alto'
    END;

-- 5. GENERACIÓN MASIVA DE PRÉSTAMOS (350 Préstamos Automáticos)
INSERT INTO prestamos (cliente_id, tipo_prestamo, monto_prestamo, tasa_interes, plazo_meses, estado_prestamo)
SELECT 
    floor(random() * 250 + 1)::int AS cliente_id,
    (ARRAY['Crédito Vehicular', 'Préstamo Personal', 'Crédito Hipotecario', 'Capital de Trabajo', 'Tarjeta de Crédito'])[floor(random() * 5 + 1)] AS tipo_prestamo,
    floor(random() * (80000 - 3000 + 1) + 3000)::numeric(10,2) AS monto_prestamo,
    round((random() * (26 - 9) + 9)::numeric, 2) AS tasa_interes,
    (ARRAY[12, 24, 36, 48, 60])[floor(random() * 5 + 1)] AS plazo_meses,
    (ARRAY['Al Día', 'Al Día', 'Al Día', 'Al Día', 'En Mora (30-60 días)', 'Incobrable'])[floor(random() * 6 + 1)] AS estado_prestamo
FROM generate_series(1, 350);

-- 6. GENERACIÓN MASIVA DE HISTORIAL DE PAGOS (1,000 Transacciones)
INSERT INTO pagos (prestamo_id, monto_pagado, fecha_pago)
SELECT 
    floor(random() * 350 + 1)::int AS prestamo_id,
    round((random() * (1500 - 200) + 200)::numeric, 2) AS monto_pagado,
    DATE '2025-01-01' + (floor(random() * 180)::int)
FROM generate_series(1, 1000);

-- 7. VISTA MAESTRA PARA EL DASHBOARD
CREATE OR REPLACE VIEW vw_dashboard_bancario AS
SELECT 
    c.cliente_id,
    c.genero,
    c.edad,
    c.ingreso_anual,
    c.puntaje_crediticio,
    c.nivel_riesgo,
    s.nombre_sucursal,
    s.ciudad,
    p.prestamo_id,
    p.tipo_prestamo,
    p.monto_prestamo,
    p.tasa_interes,
    p.plazo_meses,
    p.estado_prestamo,
    COALESCE(SUM(pg.monto_pagado), 0) AS total_pagado
FROM clientes c
JOIN sucursales s ON c.sucursal_id = s.sucursal_id
JOIN prestamos p ON c.cliente_id = p.cliente_id
LEFT JOIN pagos pg ON p.prestamo_id = pg.prestamo_id
GROUP BY 
    c.cliente_id, c.genero, c.edad, c.ingreso_anual, c.puntaje_crediticio, c.nivel_riesgo,
    s.nombre_sucursal, s.ciudad, p.prestamo_id, p.tipo_prestamo, p.monto_prestamo, 
    p.tasa_interes, p.plazo_meses, p.estado_prestamo;