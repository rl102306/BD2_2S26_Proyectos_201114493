USE aerolinea;

-- ============================================================
-- TABLAS DE ENTIDAD (lookup puntual por clave primaria)
-- ============================================================

CREATE TABLE pasajeros_por_id (
    pasajero_id uuid,
    nombre text,
    email text,
    documento text,
    telefono text,
    nacionalidad text,
    PRIMARY KEY ((pasajero_id))
);

CREATE TABLE aeronaves_por_id (
    aeronave_id uuid,
    modelo text,
    aerolinea text,
    matricula text,
    capacidad int,
    PRIMARY KEY ((aeronave_id))
);

CREATE TABLE vuelos_por_id (
    vuelo_id uuid,
    codigo_vuelo text,
    aeronave_id uuid,
    modelo_aeronave text,
    origen text,
    destino text,
    fecha_salida timestamp,
    fecha_llegada timestamp,
    estado text,
    capacidad int,
    PRIMARY KEY ((vuelo_id))
);

CREATE TABLE asientos_por_vuelo (
    vuelo_id uuid,
    clase text,
    numero_asiento text,
    estado text,
    PRIMARY KEY ((vuelo_id), clase, numero_asiento)
) WITH CLUSTERING ORDER BY (clase ASC, numero_asiento ASC);

CREATE TABLE reservas_por_id (
    reserva_id uuid,
    pasajero_id uuid,
    vuelo_id uuid,
    numero_asiento text,
    clase text,
    fecha_reserva timestamp,
    estado_reserva text,
    PRIMARY KEY ((reserva_id))
);

CREATE TABLE pagos_por_reserva (
    reserva_id uuid,
    pago_id uuid,
    monto decimal,
    metodo_pago text,
    fecha_pago timestamp,
    estado_pago text,
    PRIMARY KEY ((reserva_id))
);
