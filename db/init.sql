-- Idempotente: se puede ejecutar varias veces sin duplicar datos
IF DB_ID('OrdenesDB') IS NULL CREATE DATABASE OrdenesDB;
GO
USE OrdenesDB;
GO
IF OBJECT_ID('dbo.ordenes','U') IS NULL
CREATE TABLE dbo.ordenes (
    id INT IDENTITY(1,1) PRIMARY KEY,
    cliente NVARCHAR(100) NOT NULL,
    fecha DATE NOT NULL DEFAULT (CAST(GETDATE() AS DATE)),
    estado NVARCHAR(20) NOT NULL DEFAULT 'Pendiente'
        CONSTRAINT ck_ordenes_estado CHECK (estado IN ('Pendiente','Pagada','Anulada')),
    total DECIMAL(12,2) NOT NULL DEFAULT 0
);
GO
IF OBJECT_ID('dbo.orden_detalle','U') IS NULL
CREATE TABLE dbo.orden_detalle (
    id INT IDENTITY(1,1) PRIMARY KEY,
    orden_id INT NOT NULL
        CONSTRAINT fk_detalle_orden FOREIGN KEY REFERENCES dbo.ordenes(id) ON DELETE CASCADE,
    producto NVARCHAR(100) NOT NULL,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio_unitario DECIMAL(12,2) NOT NULL CHECK (precio_unitario >= 0),
    subtotal DECIMAL(12,2) NOT NULL
);
GO
IF NOT EXISTS (SELECT 1 FROM dbo.ordenes)
BEGIN
    DECLARE @o INT;

    INSERT INTO dbo.ordenes (cliente, fecha, estado) VALUES (N'Pulperia Don Chepe', '2026-11-02', 'Pagada');
    SET @o = SCOPE_IDENTITY();
    INSERT INTO dbo.orden_detalle (orden_id, producto, cantidad, precio_unitario, subtotal) VALUES
      (@o, N'Cafe Marcala 1 lb', 12, 95.00, 1140.00),
      (@o, N'Frijoles rojos 5 lb', 10, 120.00, 1200.00),
      (@o, N'Tortillas de maiz (paquete)', 30, 25.00, 750.00);

    INSERT INTO dbo.ordenes (cliente, fecha, estado) VALUES (N'Comedor Dona Maria, Comayaguela', '2026-11-04', 'Pendiente');
    SET @o = SCOPE_IDENTITY();
    INSERT INTO dbo.orden_detalle (orden_id, producto, cantidad, precio_unitario, subtotal) VALUES
      (@o, N'Queso seco (lb)', 8, 85.00, 680.00),
      (@o, N'Platano maduro (docena)', 5, 60.00, 300.00);

    INSERT INTO dbo.ordenes (cliente, fecha, estado) VALUES (N'Supermercado La Colonia Express', '2026-11-05', 'Pagada');
    SET @o = SCOPE_IDENTITY();
    INSERT INTO dbo.orden_detalle (orden_id, producto, cantidad, precio_unitario, subtotal) VALUES
      (@o, N'Cafe Marcala 1 lb', 40, 95.00, 3800.00),
      (@o, N'Azucar (libra)', 60, 18.00, 1080.00),
      (@o, N'Aceite 1 litro', 24, 55.00, 1320.00);

    INSERT INTO dbo.ordenes (cliente, fecha, estado) VALUES (N'Baleadas Express San Pedro Sula', '2026-11-07', 'Anulada');
    SET @o = SCOPE_IDENTITY();
    INSERT INTO dbo.orden_detalle (orden_id, producto, cantidad, precio_unitario, subtotal) VALUES
      (@o, N'Harina de trigo (libra)', 50, 22.00, 1100.00),
      (@o, N'Crema salvadorena (pinta)', 20, 45.00, 900.00);

    INSERT INTO dbo.ordenes (cliente, fecha, estado) VALUES (N'Hotel Marina Copan', '2026-11-10', 'Pendiente');
    SET @o = SCOPE_IDENTITY();
    INSERT INTO dbo.orden_detalle (orden_id, producto, cantidad, precio_unitario, subtotal) VALUES
      (@o, N'Cafe Marcala 1 lb', 15, 95.00, 1425.00),
      (@o, N'Miel de abeja (botella)', 6, 150.00, 900.00),
      (@o, N'Huevos (carton 30)', 10, 140.00, 1400.00);

    UPDATE o SET total = (SELECT ISNULL(SUM(subtotal),0) FROM dbo.orden_detalle d WHERE d.orden_id = o.id)
    FROM dbo.ordenes o;
END
GO
