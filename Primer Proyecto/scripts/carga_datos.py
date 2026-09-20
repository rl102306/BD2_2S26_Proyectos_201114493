"""
Carga masiva del sistema de reservas aéreas en Apache Cassandra.

Genera aeronaves, vuelos, asientos, pasajeros, reservas y pagos, y escribe
en todas las tablas denormalizadas del modelo usando Batch Writes.

Reglas de negocio aplicadas durante la generación:
  - Un asiento de un vuelo se asigna a un solo pasajero (muestreo sin repetición).
  - Las reservas nunca superan la capacidad de la aeronave (control de sobreventa).
  - Si el vuelo está cancelado, sus reservas y pagos quedan cancelada/reembolsado.
  - Toda reserva tiene un pago asociado con su estado correspondiente.

Uso:  python3 scripts/carga_datos.py
"""

import random
import time
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from cassandra import WriteTimeout, OperationTimedOut
from cassandra.cluster import Cluster
from cassandra.query import BatchStatement, BatchType

KEYSPACE       = "aerolinea"
CANT_AERONAVES = 40
CANT_VUELOS    = 520
CANT_PASAJEROS = 25000
TAM_BATCH      = 25
MAX_PENDIENTES = 8
REINTENTOS     = 5

AEROPUERTOS = ["GUA", "SAL", "SJO", "PTY", "MEX", "MIA", "LAX",
               "JFK", "BOG", "LIM", "MAD", "IAH", "YYZ", "SCL"]
MODELOS = ["Airbus A320", "Airbus A321neo", "Boeing 737-800",
           "Boeing 787-9", "Embraer E190"]
AEROLINEAS = ["Avianca", "Copa Airlines", "Volaris", "American Airlines"]
METODOS_PAGO = ["tarjeta_credito", "tarjeta_debito", "transferencia", "efectivo"]

NOMBRES = ["Carlos", "Maria", "Jose", "Ana", "Luis", "Sofia", "Pedro", "Lucia",
           "Jorge", "Elena", "Diego", "Paola", "Andres", "Gabriela", "Marco",
           "Daniela", "Rodrigo", "Valeria", "Fernando", "Camila"]
APELLIDOS = ["Gomez", "Lopez", "Ramirez", "Morales", "Castillo", "Hernandez",
             "Perez", "Rodriguez", "Aguilar", "Mendoza", "Vasquez", "Ortiz",
             "Cabrera", "Alvarado", "Sandoval", "Estrada", "Reyes", "Cruz"]
PAISES = ["Guatemala", "El Salvador", "Honduras", "Mexico", "Costa Rica",
          "Panama", "Colombia", "Estados Unidos", "Espana", "Peru"]

random.seed(42)


class Ejecutor:
    """Acumula statements en batches y los envia de forma asincrona,
    con reintentos ante WriteTimeout para no perder datos."""

    def __init__(self, session, tipo=BatchType.UNLOGGED):
        self.session = session
        self.tipo = tipo
        self.batch = BatchStatement(batch_type=tipo)
        self.n = 0
        self.pendientes = []
        self.total = 0

    def add(self, stmt, params):
        self.batch.add(stmt, params)
        self.n += 1
        self.total += 1
        if self.n >= TAM_BATCH:
            self.flush()

    def flush(self):
        if self.n == 0:
            return
        b = self.batch
        self.pendientes.append((self.session.execute_async(b), b))
        self.batch = BatchStatement(batch_type=self.tipo)
        self.n = 0
        if len(self.pendientes) >= MAX_PENDIENTES:
            self.esperar()

    def esperar(self):
        for fut, b in self.pendientes:
            self._resolver(fut, b)
        self.pendientes = []

    def _resolver(self, fut, batch):
        for intento in range(REINTENTOS):
            try:
                fut.result()
                return
            except (WriteTimeout, OperationTimedOut):
                espera = 2 ** intento
                print(f"    timeout, reintento {intento + 1} en {espera}s...")
                time.sleep(espera)
                fut = self.session.execute_async(batch)
        raise RuntimeError("Batch fallido tras varios reintentos")

    def cerrar(self):
        self.flush()
        self.esperar()


def generar_asientos(capacidad):
    """Devuelve [(numero_asiento, clase)]. 6 asientos por fila, formato 000L."""
    asientos = []
    for fila in range(1, capacidad // 6 + 1):
        if fila <= 2:
            clase = "primera"
        elif fila <= 7:
            clase = "ejecutiva"
        else:
            clase = "economica"
        for letra in "ABCDEF":
            asientos.append((f"{fila:03d}{letra}", clase))
    return asientos


def rango_precio(clase):
    return {"primera": (800, 2500),
            "ejecutiva": (400, 1200),
            "economica": (90, 450)}[clase]


def nombre_aleatorio():
    return f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"


cluster = Cluster(["127.0.0.1"], port=9042)
session = cluster.connect(KEYSPACE)
session.default_timeout = 120

print("Preparando statements...")

ps_pasajero = session.prepare(
    "INSERT INTO pasajeros_por_id (pasajero_id, nombre, email, documento, telefono, "
    "nacionalidad) VALUES (?, ?, ?, ?, ?, ?)")

ps_aeronave = session.prepare(
    "INSERT INTO aeronaves_por_id (aeronave_id, modelo, aerolinea, matricula, capacidad) "
    "VALUES (?, ?, ?, ?, ?)")

ps_vuelo = session.prepare(
    "INSERT INTO vuelos_por_id (vuelo_id, codigo_vuelo, aeronave_id, modelo_aeronave, "
    "origen, destino, fecha_salida, fecha_llegada, estado, capacidad) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")

ps_asiento = session.prepare(
    "INSERT INTO asientos_por_vuelo (vuelo_id, clase, numero_asiento, estado) "
    "VALUES (?, ?, ?, ?)")

ps_capacidad = session.prepare(
    "INSERT INTO capacidad_por_clase (vuelo_id, clase, capacidad_clase) VALUES (?, ?, ?)")

ps_reserva_id = session.prepare(
    "INSERT INTO reservas_por_id (reserva_id, pasajero_id, vuelo_id, numero_asiento, "
    "clase, fecha_reserva, estado_reserva) VALUES (?, ?, ?, ?, ?, ?, ?)")

ps_pago = session.prepare(
    "INSERT INTO pagos_por_reserva (reserva_id, pago_id, monto, metodo_pago, fecha_pago, "
    "estado_pago) VALUES (?, ?, ?, ?, ?, ?)")

ps_hist = session.prepare(
    "INSERT INTO reservas_por_pasajero (pasajero_id, fecha_reserva, reserva_id, vuelo_id, "
    "codigo_vuelo, origen, destino, fecha_salida, numero_asiento, clase, estado_reserva, "
    "estado_pago, monto) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")

ps_manifiesto = session.prepare(
    "INSERT INTO manifiesto_por_vuelo (vuelo_id, numero_asiento, pasajero_id, "
    "nombre_pasajero, documento, clase, estado_reserva, estado_pago, reserva_id) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")

ps_pendiente = session.prepare(
    "INSERT INTO reservas_pendientes_por_vuelo (vuelo_id, reserva_id, pasajero_id, "
    "numero_asiento, fecha_reserva) VALUES (?, ?, ?, ?, ?) USING TTL 86400")

ps_vuelo_ruta = session.prepare(
    "INSERT INTO vuelos_por_ruta_mes (origen, destino, anio_mes, fecha_salida, vuelo_id, "
    "codigo_vuelo, capacidad) VALUES (?, ?, ?, ?, ?, ?, ?)")

ps_cnt_clase_init = session.prepare(
    "UPDATE disponibilidad_por_clase SET asientos_disponibles = asientos_disponibles + ? "
    "WHERE vuelo_id = ? AND clase = ?")

ps_cnt_ocupar = session.prepare(
    "UPDATE disponibilidad_por_clase SET asientos_ocupados = asientos_ocupados + 1, "
    "asientos_disponibles = asientos_disponibles - 1 WHERE vuelo_id = ? AND clase = ?")

ps_cnt_ruta = session.prepare(
    "UPDATE reservas_por_ruta_mes SET reservas_confirmadas = reservas_confirmadas + 1 "
    "WHERE origen = ? AND destino = ? AND anio_mes = ? AND fecha_salida = ? AND vuelo_id = ?")

ps_cnt_ingreso = session.prepare(
    "UPDATE ingresos_por_vuelo SET monto_total = monto_total + ? "
    "WHERE anio_mes = ? AND vuelo_id = ?")

ps_top = session.prepare(
    "INSERT INTO top_ingresos_por_mes (anio_mes, monto_total, vuelo_id, codigo_vuelo, "
    "origen, destino) VALUES (?, ?, ?, ?, ?, ?)")

t_inicio = time.time()

print(f"Insertando {CANT_PASAJEROS} pasajeros...")
ex = Ejecutor(session)
pasajeros = []
for i in range(CANT_PASAJEROS):
    pid = uuid.uuid4()
    nombre = nombre_aleatorio()
    doc = f"{random.randint(1000,9999)}-{random.randint(10000,99999)}-{random.randint(1000,9999)}"
    pasajeros.append((pid, nombre, doc))
    tel = f"+502 {random.randint(3000,5999)}-{random.randint(1000,9999)}"
    ex.add(ps_pasajero, (pid, nombre, f"usuario{i}@correo.com", doc, tel,
                         random.choice(PAISES)))
ex.cerrar()
print(f"  OK ({time.time() - t_inicio:.1f}s)")

print(f"Insertando {CANT_AERONAVES} aeronaves...")
ex = Ejecutor(session)
aeronaves = []
LETRAS = "ABCDEFGHJKLMNPQRSTUVWXYZ"
for _ in range(CANT_AERONAVES):
    aid = uuid.uuid4()
    modelo = random.choice(MODELOS)
    capacidad = random.choice([180, 192, 216, 240, 264, 288, 300])
    aeronaves.append((aid, modelo, capacidad))
    matricula = "TG-" + "".join(random.choice(LETRAS) for _ in range(3))
    ex.add(ps_aeronave, (aid, modelo, random.choice(AEROLINEAS), matricula, capacidad))
ex.cerrar()
print("  OK")

print(f"Generando {CANT_VUELOS} vuelos con sus reservas...")
ex_norm = Ejecutor(session)
ex_cnt = Ejecutor(session, BatchType.COUNTER)

inicio_temporada = datetime(2026, 1, 1, 6, 0, 0)
total_reservas = 0

for i in range(CANT_VUELOS):
    aeronave_id, modelo, capacidad = random.choice(aeronaves)
    vuelo_id = uuid.uuid4()
    codigo = f"AV{random.randint(100, 999)}"
    origen, destino = random.sample(AEROPUERTOS, 2)
    fecha_salida = inicio_temporada + timedelta(
        days=random.randint(0, 364), hours=random.randint(0, 17))
    fecha_llegada = fecha_salida + timedelta(hours=random.randint(1, 9))
    anio_mes = fecha_salida.strftime("%Y-%m")
    estado_vuelo = random.choices(
        ["programado", "completado", "retrasado", "cancelado"],
        weights=[50, 40, 7, 3])[0]

    ex_norm.add(ps_vuelo, (vuelo_id, codigo, aeronave_id, modelo, origen, destino,
                           fecha_salida, fecha_llegada, estado_vuelo, capacidad))
    ex_norm.add(ps_vuelo_ruta, (origen, destino, anio_mes, fecha_salida,
                                vuelo_id, codigo, capacidad))

    asientos = generar_asientos(capacidad)
    por_clase = {}
    for _, clase in asientos:
        por_clase[clase] = por_clase.get(clase, 0) + 1

    for clase, cap_clase in por_clase.items():
        ex_norm.add(ps_capacidad, (vuelo_id, clase, cap_clase))
        ex_cnt.add(ps_cnt_clase_init, (cap_clase, vuelo_id, clase))

    n_reservas = int(capacidad * random.uniform(0.65, 0.95))
    seleccion = random.sample(asientos, n_reservas)
    ocupados = set()

    for numero_asiento, clase in seleccion:
        pid, nombre, doc = random.choice(pasajeros)
        reserva_id = uuid.uuid4()
        fecha_reserva = fecha_salida - timedelta(
            days=random.randint(2, 120), hours=random.randint(0, 23))

        if estado_vuelo == "cancelado":
            estado_reserva, estado_pago = "cancelada", "reembolsado"
        else:
            estado_reserva = random.choices(
                ["confirmada", "pendiente", "cancelada"], weights=[80, 15, 5])[0]
            estado_pago = {"confirmada": "pagado",
                           "pendiente": "pendiente",
                           "cancelada": "reembolsado"}[estado_reserva]

        lo, hi = rango_precio(clase)
        monto = Decimal(f"{random.uniform(lo, hi):.2f}")
        fecha_pago = fecha_reserva + timedelta(minutes=random.randint(1, 240))

        ex_norm.add(ps_reserva_id, (reserva_id, pid, vuelo_id, numero_asiento,
                                    clase, fecha_reserva, estado_reserva))
        ex_norm.add(ps_pago, (reserva_id, uuid.uuid4(), monto,
                              random.choice(METODOS_PAGO), fecha_pago, estado_pago))
        ex_norm.add(ps_hist, (pid, fecha_reserva, reserva_id, vuelo_id, codigo,
                              origen, destino, fecha_salida, numero_asiento, clase,
                              estado_reserva, estado_pago, monto))

        if estado_reserva in ("confirmada", "pendiente"):
            ocupados.add(numero_asiento)
            ex_norm.add(ps_manifiesto, (vuelo_id, numero_asiento, pid, nombre, doc,
                                        clase, estado_reserva, estado_pago, reserva_id))
            ex_cnt.add(ps_cnt_ocupar, (vuelo_id, clase))

        if estado_reserva == "pendiente":
            ex_norm.add(ps_pendiente, (vuelo_id, reserva_id, pid,
                                       numero_asiento, fecha_reserva))

        if estado_reserva == "confirmada":
            ex_cnt.add(ps_cnt_ruta, (origen, destino, anio_mes, fecha_salida, vuelo_id))

        if estado_pago == "pagado":
            ex_cnt.add(ps_cnt_ingreso, (int(monto * 100), anio_mes, vuelo_id))

        total_reservas += 1

    for numero_asiento, clase in asientos:
        estado = "ocupado" if numero_asiento in ocupados else "disponible"
        ex_norm.add(ps_asiento, (vuelo_id, clase, numero_asiento, estado))

    if (i + 1) % 25 == 0:
        print(f"  vuelos {i + 1}/{CANT_VUELOS} - reservas: {total_reservas} "
              f"({time.time() - t_inicio:.0f}s)")
        ex_norm.esperar()
        ex_cnt.esperar()
        time.sleep(0.5)

ex_norm.cerrar()
ex_cnt.cerrar()
print(f"Reservas insertadas: {total_reservas}")

print("Construyendo tabla de ranking de ingresos...")
ex = Ejecutor(session)
for m in range(1, 13):
    mes = f"2026-{m:02d}"
    for f in session.execute(
            "SELECT vuelo_id, monto_total FROM ingresos_por_vuelo WHERE anio_mes = %s", (mes,)):
        if not f.monto_total:
            continue
        v = session.execute(
            "SELECT codigo_vuelo, origen, destino FROM vuelos_por_id WHERE vuelo_id = %s",
            (f.vuelo_id,)).one()
        if v:
            ex.add(ps_top, (mes, int(f.monto_total), f.vuelo_id,
                            v.codigo_vuelo, v.origen, v.destino))
ex.cerrar()

print(f"\nCarga finalizada en {time.time() - t_inicio:.1f}s")
print(f"Total de reservas: {total_reservas}")
cluster.shutdown()
