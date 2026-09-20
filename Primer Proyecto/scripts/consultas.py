"""Ejecuta las 5 consultas del negocio con datos reales y mide su latencia."""

import time
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, ConsistencyLevel

cluster = Cluster(["127.0.0.1"])
s = cluster.connect("aerolinea")
s.default_timeout = 60


def medir(titulo, cql, params=(), mostrar=6):
    st = SimpleStatement(cql, consistency_level=ConsistencyLevel.QUORUM)
    t0 = time.perf_counter()
    filas = list(s.execute(st, params))
    ms = (time.perf_counter() - t0) * 1000
    print(f"\n=== {titulo} ===")
    print(f"CQL: {' '.join(cql.split())}")
    print(f"Latencia: {ms:.2f} ms | filas devueltas: {len(filas)}")
    for f in filas[:mostrar]:
        print("   ", f)
    return filas


# Datos de ejemplo tomados del propio dataset
vuelo = s.execute("SELECT vuelo_id, codigo_vuelo, origen, destino, fecha_salida "
                  "FROM vuelos_por_id LIMIT 1").one()
pasajero = s.execute("SELECT pasajero_id FROM reservas_por_pasajero LIMIT 1").one()
mes = vuelo.fecha_salida.strftime("%Y-%m")

print("PARAMETROS DE PRUEBA")
print(f"  vuelo_id    = {vuelo.vuelo_id}")
print(f"  codigo      = {vuelo.codigo_vuelo} ({vuelo.origen} -> {vuelo.destino})")
print(f"  pasajero_id = {pasajero.pasajero_id}")
print(f"  anio_mes    = {mes}")

medir("Q1 Disponibilidad de asientos por clase",
      "SELECT clase, asientos_ocupados, asientos_disponibles "
      "FROM disponibilidad_por_clase WHERE vuelo_id=%s", (vuelo.vuelo_id,))

medir("Q1b Capacidad por clase (tabla complementaria)",
      "SELECT clase, capacidad_clase FROM capacidad_por_clase WHERE vuelo_id=%s",
      (vuelo.vuelo_id,))

medir("Q2 Historial cronologico de un pasajero",
      "SELECT fecha_reserva, codigo_vuelo, origen, destino, numero_asiento, "
      "clase, estado_reserva, estado_pago, monto FROM reservas_por_pasajero "
      "WHERE pasajero_id=%s AND fecha_reserva>=%s AND fecha_reserva<=%s",
      (pasajero.pasajero_id, "2026-01-01", "2026-12-31"))

medir("Q3 Manifiesto de vuelo ordenado por asiento",
      "SELECT numero_asiento, nombre_pasajero, documento, clase, "
      "estado_reserva, estado_pago FROM manifiesto_por_vuelo WHERE vuelo_id=%s",
      (vuelo.vuelo_id,))

# Q4: combina contador de confirmadas con capacidad de la aeronave
print(f"\n=== Q4 Porcentaje de ocupacion ruta {vuelo.origen}->{vuelo.destino}, mes {mes} ===")
t0 = time.perf_counter()
cnt = {r.vuelo_id: r.reservas_confirmadas for r in s.execute(
    "SELECT vuelo_id, reservas_confirmadas FROM reservas_por_ruta_mes "
    "WHERE origen=%s AND destino=%s AND anio_mes=%s",
    (vuelo.origen, vuelo.destino, mes))}
caps = list(s.execute(
    "SELECT vuelo_id, codigo_vuelo, capacidad, fecha_salida FROM vuelos_por_ruta_mes "
    "WHERE origen=%s AND destino=%s AND anio_mes=%s",
    (vuelo.origen, vuelo.destino, mes)))
print(f"Latencia (2 consultas): {(time.perf_counter()-t0)*1000:.2f} ms")
for c in caps[:8]:
    conf = cnt.get(c.vuelo_id, 0)
    print(f"    {c.codigo_vuelo}  {c.fecha_salida:%Y-%m-%d}  "
          f"{conf}/{c.capacidad} = {conf*100/c.capacidad:.1f}% ocupacion")

medir(f"Q5 Top 10 vuelos por ingresos generados ({mes})",
      "SELECT codigo_vuelo, origen, destino, monto_total FROM top_ingresos_por_mes "
      "WHERE anio_mes=%s LIMIT 10", (mes,), mostrar=10)

print("\nNota: los montos de Q5 estan en centavos.")
cluster.shutdown()
