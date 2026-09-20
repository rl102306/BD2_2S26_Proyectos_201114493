"""Segunda pasada: latencias limpias sobre parametros ya conocidos.
Separa la seleccion de parametros (escaneo) de la medicion real."""

import time
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, ConsistencyLevel

cluster = Cluster(["127.0.0.1"])
s = cluster.connect("aerolinea")
s.default_timeout = 60

REPS = 20


def medir(titulo, cql, params):
    st = SimpleStatement(cql, consistency_level=ConsistencyLevel.QUORUM)
    list(s.execute(st, params))          # warm-up, no se mide
    lat = []
    for _ in range(REPS):
        t0 = time.perf_counter()
        filas = list(s.execute(st, params))
        lat.append((time.perf_counter() - t0) * 1000)
    lat.sort()
    print(f"{titulo:52s} filas={len(filas):4d}  "
          f"prom={sum(lat)/len(lat):7.2f} ms  min={lat[0]:6.2f}  p95={lat[int(REPS*0.95)-1]:7.2f}")


# --- Seleccion de parametros con buena densidad de datos (fuera de la medicion) ---
ruta = None
for r in s.execute("SELECT origen, destino, anio_mes FROM vuelos_por_ruta_mes LIMIT 2000"):
    n = len(list(s.execute(
        "SELECT vuelo_id FROM vuelos_por_ruta_mes "
        "WHERE origen=%s AND destino=%s AND anio_mes=%s",
        (r.origen, r.destino, r.anio_mes))))
    if n >= 2:
        ruta = (r.origen, r.destino, r.anio_mes, n)
        break

pas = None
for r in s.execute("SELECT pasajero_id FROM reservas_por_pasajero LIMIT 3000"):
    n = len(list(s.execute(
        "SELECT reserva_id FROM reservas_por_pasajero WHERE pasajero_id=%s",
        (r.pasajero_id,))))
    if n >= 4:
        pas = r.pasajero_id
        break

vuelo = s.execute("SELECT vuelo_id, codigo_vuelo, origen, destino, fecha_salida "
                  "FROM vuelos_por_id LIMIT 1").one()
mes = vuelo.fecha_salida.strftime("%Y-%m")

print("PARAMETROS")
print(f"  vuelo    : {vuelo.codigo_vuelo} {vuelo.origen}->{vuelo.destino}  {vuelo.vuelo_id}")
print(f"  pasajero : {pas}")
print(f"  ruta Q4  : {ruta[0]}->{ruta[1]} {ruta[2]} ({ruta[3]} vuelos)")
print(f"\nLatencias sobre {REPS} ejecuciones, Consistency Level QUORUM\n")

medir("Q1 Disponibilidad por clase (counter)",
      "SELECT clase, asientos_ocupados, asientos_disponibles "
      "FROM disponibilidad_por_clase WHERE vuelo_id=%s", (vuelo.vuelo_id,))

medir("Q2 Historial de pasajero (rango sobre clustering key)",
      "SELECT fecha_reserva, codigo_vuelo, estado_reserva, estado_pago, monto "
      "FROM reservas_por_pasajero WHERE pasajero_id=%s "
      "AND fecha_reserva>=%s AND fecha_reserva<=%s",
      (pas, "2026-01-01", "2026-12-31"))

medir("Q3 Manifiesto de vuelo (denormalizado, 1 particion)",
      "SELECT numero_asiento, nombre_pasajero, clase, estado_reserva, estado_pago "
      "FROM manifiesto_por_vuelo WHERE vuelo_id=%s", (vuelo.vuelo_id,))

medir("Q4a Contador de confirmadas por ruta-mes (bucketing)",
      "SELECT vuelo_id, reservas_confirmadas FROM reservas_por_ruta_mes "
      "WHERE origen=%s AND destino=%s AND anio_mes=%s", (ruta[0], ruta[1], ruta[2]))

medir("Q4b Capacidad por ruta-mes",
      "SELECT vuelo_id, codigo_vuelo, capacidad FROM vuelos_por_ruta_mes "
      "WHERE origen=%s AND destino=%s AND anio_mes=%s", (ruta[0], ruta[1], ruta[2]))

medir("Q5 Top 10 por ingresos (clustering DESC + LIMIT)",
      "SELECT codigo_vuelo, monto_total FROM top_ingresos_por_mes "
      "WHERE anio_mes=%s LIMIT 10", (mes,))

# --- Q4 resuelta completa, con la ruta de mayor densidad ---
print(f"\nQ4 resultado: ocupacion ruta {ruta[0]}->{ruta[1]} en {ruta[2]}")
cnt = {r.vuelo_id: r.reservas_confirmadas for r in s.execute(
    "SELECT vuelo_id, reservas_confirmadas FROM reservas_por_ruta_mes "
    "WHERE origen=%s AND destino=%s AND anio_mes=%s", (ruta[0], ruta[1], ruta[2]))}
for c in s.execute(
        "SELECT vuelo_id, codigo_vuelo, capacidad, fecha_salida FROM vuelos_por_ruta_mes "
        "WHERE origen=%s AND destino=%s AND anio_mes=%s", (ruta[0], ruta[1], ruta[2])):
    conf = cnt.get(c.vuelo_id, 0)
    print(f"    {c.codigo_vuelo}  {c.fecha_salida:%Y-%m-%d}  "
          f"{conf:3d}/{c.capacidad}  = {conf*100/c.capacidad:5.1f}%")

cluster.shutdown()
