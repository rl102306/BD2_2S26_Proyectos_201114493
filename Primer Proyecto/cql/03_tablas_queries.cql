USE aerolinea;

-- ============================================================
-- Q1: Disponibilidad de asientos por clase para un vuelo.
-- Contadores actualizados en cada reserva/cancelación.
-- Una tabla counter no admite columnas normales, por eso la
-- capacidad por clase vive en tabla aparte con la misma clave.
-- ============================================================

CREATE TABLE disponibilidad_por_clase (
    vuelo_id uuid,
    clase text,
    asientos_ocupados counter,
    asientos_disponibles counter,
    PRIMARY KEY ((vuelo_id), clase)
);

CREATE TABLE capacidad_por_clase (
    vuelo_id uuid,
    clase text,
    capacidad_clase int,
    PRIMARY KEY ((vuelo_id), clase)
);

-- ============================================================
-- Q2: Historial cronológico de un pasajero en rango de fechas.
-- Partición = pasajero. Clustering por fecha_reserva DESC
-- permite ORDER BY y comparadores >= / <= sin ALLOW FILTERING.
-- Denormaliza vuelo, reserva y pago en una sola fila.
-- ============================================================

CREATE TABLE reservas_por_pasajero (
    pasajero_id uuid,
    fecha_reserva timestamp,
    reserva_id uuid,
    vuelo_id uuid,
    codigo_vuelo text,
    origen text,
    destino text,
    fecha_salida timestamp,
    numero_asiento text,
    clase text,
    estado_reserva text,
    estado_pago text,
    monto decimal,
    PRIMARY KEY ((pasajero_id), fecha_reserva, reserva_id)
) WITH CLUSTERING ORDER BY (fecha_reserva DESC, reserva_id ASC);

-- ============================================================
-- Q3: Manifiesto de vuelo ordenado por número de asiento.
-- Partición = vuelo, clustering = numero_asiento ASC.
-- Denormaliza pasajero + reserva + pago (evita 3 JOINs).
-- ============================================================

CREATE TABLE manifiesto_por_vuelo (
    vuelo_id uuid,
    numero_asiento text,
    pasajero_id uuid,
    nombre_pasajero text,
    documento text,
    clase text,
    estado_reserva text,
    estado_pago text,
    reserva_id uuid,
    PRIMARY KEY ((vuelo_id), numero_asiento)
) WITH CLUSTERING ORDER BY (numero_asiento ASC);

-- ============================================================
-- Q4: Porcentaje de ocupación por ruta y rango de fechas.
-- Bucketing (origen, destino, anio_mes) para evitar particiones
-- gigantes en rutas con años de historia.
-- ============================================================

CREATE TABLE reservas_por_ruta_mes (
    origen text,
    destino text,
    anio_mes text,
    fecha_salida timestamp,
    vuelo_id uuid,
    reservas_confirmadas counter,
    PRIMARY KEY ((origen, destino, anio_mes), fecha_salida, vuelo_id)
) WITH CLUSTERING ORDER BY (fecha_salida ASC, vuelo_id ASC);

CREATE TABLE vuelos_por_ruta_mes (
    origen text,
    destino text,
    anio_mes text,
    fecha_salida timestamp,
    vuelo_id uuid,
    codigo_vuelo text,
    capacidad int,
    PRIMARY KEY ((origen, destino, anio_mes), fecha_salida, vuelo_id)
) WITH CLUSTERING ORDER BY (fecha_salida ASC, vuelo_id ASC);

-- ============================================================
-- Q5: Top N de vuelos por ingresos generados.
-- ingresos_por_vuelo acumula con counter (monto en centavos).
-- top_ingresos_por_mes es el ranking: monto_total es clustering
-- key DESC, por lo que LIMIT N lee las primeras N filas de la
-- partición sin ordenar en cliente. Al cambiar el monto se hace
-- DELETE de la fila previa + INSERT de la nueva.
-- ============================================================

CREATE TABLE ingresos_por_vuelo (
    anio_mes text,
    vuelo_id uuid,
    monto_total counter,
    PRIMARY KEY ((anio_mes), vuelo_id)
);

CREATE TABLE top_ingresos_por_mes (
    anio_mes text,
    monto_total bigint,
    vuelo_id uuid,
    codigo_vuelo text,
    origen text,
    destino text,
    PRIMARY KEY ((anio_mes), monto_total, vuelo_id)
) WITH CLUSTERING ORDER BY (monto_total DESC, vuelo_id ASC);

-- ============================================================
-- TTL: reservas pendientes que expiran automáticamente a las 24h.
-- Las tablas counter no admiten TTL, por eso se aplica aquí.
-- ============================================================

CREATE TABLE reservas_pendientes_por_vuelo (
    vuelo_id uuid,
    reserva_id uuid,
    pasajero_id uuid,
    numero_asiento text,
    fecha_reserva timestamp,
    PRIMARY KEY ((vuelo_id), reserva_id)
) WITH default_time_to_live = 86400;
