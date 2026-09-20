"""
Pruebas de tolerancia a fallos y comparacion de Consistency Levels.

Mide latencia y disponibilidad de una consulta representativa bajo
CL ONE, QUORUM y ALL. Se ejecuta en tres escenarios:
  1. Clúster completo (3 nodos)
  2. Un nodo caido
  3. Clúster recuperado

Uso:  python3 scripts/pruebas_fallos.py "etiqueta del escenario"
"""

import sys
import time

from cassandra import Unavailable, ReadTimeout, OperationTimedOut
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, ConsistencyLevel

etiqueta = sys.argv[1] if len(sys.argv) > 1 else "sin etiqueta"
REPETICIONES = 30

cluster = Cluster(["127.0.0.1"])
s = cluster.connect("aerolinea")
s.default_timeout = 20

vuelo = s.execute("SELECT vuelo_id, codigo_vuelo FROM vuelos_por_id LIMIT 1").one()
cql = ("SELECT numero_asiento, nombre_pasajero, estado_pago "
       "FROM manifiesto_por_vuelo WHERE vuelo_id=%s")

print(f"\n{'='*72}")
print(f"ESCENARIO: {etiqueta}")
print(f"Consulta: manifiesto del vuelo {vuelo.codigo_vuelo}")
print(f"Repeticiones por nivel: {REPETICIONES}")
print(f"{'='*72}")
print(f"{'CL':8s} {'exitosas':>9s} {'fallidas':>9s} {'prom(ms)':>10s} "
      f"{'min(ms)':>9s} {'p95(ms)':>9s}  error")

for nivel in ("ONE", "QUORUM", "ALL"):
    st = SimpleStatement(cql, consistency_level=getattr(ConsistencyLevel, nivel))
    lat = []
    errores = 0
    ultimo = ""
    for _ in range(REPETICIONES):
        t0 = time.perf_counter()
        try:
            list(s.execute(st, (vuelo.vuelo_id,)))
            lat.append((time.perf_counter() - t0) * 1000)
        except (Unavailable, ReadTimeout, OperationTimedOut) as e:
            errores += 1
            ultimo = type(e).__name__
        except Exception as e:
            errores += 1
            ultimo = type(e).__name__
    if lat:
        lat.sort()
        p95 = lat[min(int(len(lat) * 0.95), len(lat) - 1)]
        print(f"{nivel:8s} {len(lat):9d} {errores:9d} {sum(lat)/len(lat):10.2f} "
              f"{lat[0]:9.2f} {p95:9.2f}  {ultimo}")
    else:
        print(f"{nivel:8s} {0:9d} {errores:9d} {'-':>10s} {'-':>9s} {'-':>9s}  {ultimo}")

cluster.shutdown()
