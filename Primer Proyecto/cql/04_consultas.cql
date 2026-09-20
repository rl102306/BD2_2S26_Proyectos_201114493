-- ============================================================
-- Las 5 consultas del negocio. Ninguna usa ALLOW FILTERING.
-- Parametros de ejemplo tomados del dataset cargado.
-- ============================================================

USE aerolinea;

-- Q1. Disponibilidad de asientos por clase para un vuelo.
-- Lee contadores precalculados; no cuenta filas en tiempo de consulta.
SELECT clase, asientos_ocupados, asientos_disponibles
FROM disponibilidad_por_clase
WHERE vuelo_id = 5e8120ae-9633-4f76-890a-fd3502e41bd9;

SELECT clase, capacidad_clase
FROM capacidad_por_clase
WHERE vuelo_id = 5e8120ae-9633-4f76-890a-fd3502e41bd9;

-- Q2. Historial cronologico de un pasajero en un rango de fechas.
-- Rango sobre clustering key, con estado de pago denormalizado.
SELECT fecha_reserva, codigo_vuelo, origen, destino, fecha_salida,
       numero_asiento, clase, estado_reserva, estado_pago, monto
FROM reservas_por_pasajero
WHERE pasajero_id = 8d92b228-e768-4fa8-8090-39af7b49df67
  AND fecha_reserva >= '2026-01-01'
  AND fecha_reserva <= '2026-12-31';

-- Q3. Manifiesto de vuelo ordenado por numero de asiento.
-- Una sola particion; tres entidades denormalizadas, sin JOIN.
SELECT numero_asiento, nombre_pasajero, documento, clase,
       estado_reserva, estado_pago
FROM manifiesto_por_vuelo
WHERE vuelo_id = 5e8120ae-9633-4f76-890a-fd3502e41bd9;

-- Q4. Porcentaje de ocupacion por ruta y rango de fechas.
-- Particion bucketizada (origen, destino, anio_mes).
-- El porcentaje se obtiene dividiendo reservas_confirmadas / capacidad.
SELECT vuelo_id, fecha_salida, reservas_confirmadas
FROM reservas_por_ruta_mes
WHERE origen = 'PTY' AND destino = 'LIM' AND anio_mes = '2026-07';

SELECT vuelo_id, codigo_vuelo, fecha_salida, capacidad
FROM vuelos_por_ruta_mes
WHERE origen = 'PTY' AND destino = 'LIM' AND anio_mes = '2026-07';

-- Q5. Top N de vuelos por ingresos generados.
-- monto_total es clustering key DESC: el LIMIT se resuelve leyendo
-- las primeras N filas de la particion, sin ordenar en el cliente.
-- Los montos estan almacenados en centavos.
SELECT codigo_vuelo, origen, destino, monto_total, vuelo_id
FROM top_ingresos_por_mes
WHERE anio_mes = '2026-09'
LIMIT 10;
