#!/usr/bin/env python3
"""
Generador de datos CSV para el Proyecto 2 - Sistema de Recomendación de Restaurantes
Curso: Sistemas de Bases de Datos 2 (SBD2) - 2S2026
Carné: 201114493

Genera archivos CSV para carga masiva en Neo4j.
"""

import csv
import os
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('es_MX')
Faker.seed(42)
random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# ─── Constantes ───
NUM_USUARIOS = 500
NUM_RESTAURANTES = 200
NUM_CHEFS = 100
NUM_PLATILLOS = 50
NUM_TIPOS_COCINA = 15

# ─── Helpers ───
def rand_date(start_year=2018, end_year=2026):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 6, 30)
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).strftime('%Y-%m-%d')

def write_csv(filename, headers, rows):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"  ✓ {filename}: {len(rows)} registros")

# ═══════════════════════════════════════════════
# 1. NODOS
# ═══════════════════════════════════════════════

# --- Tipos de Cocina ---
tipos_cocina_nombres = [
    ("Mexicana", "Cocina tradicional mexicana con sabores intensos y variados"),
    ("Italiana", "Pastas, pizzas y platos mediterráneos clásicos"),
    ("Japonesa", "Sushi, ramen y cocina tradicional japonesa"),
    ("China", "Amplia variedad de platos de las regiones de China"),
    ("Francesa", "Alta cocina y técnicas culinarias refinadas"),
    ("Peruana", "Ceviche, lomo saltado y fusión andina"),
    ("Tailandesa", "Curry, pad thai y sabores del sudeste asiático"),
    ("India", "Especias aromáticas, curry y tandoori"),
    ("Española", "Tapas, paella y cocina mediterránea"),
    ("Colombiana", "Bandeja paisa, arepas y sabores caribeños"),
    ("Coreana", "BBQ coreano, kimchi y bibimbap"),
    ("Griega", "Gyros, moussaka y cocina del Mediterráneo oriental"),
    ("Argentina", "Asados, empanadas y cocina del Río de la Plata"),
    ("Vegana", "Cocina 100% basada en plantas"),
    ("Fusión", "Mezcla creativa de diversas tradiciones culinarias"),
]

tipos_cocina = []
for i, (nombre, desc) in enumerate(tipos_cocina_nombres, 1):
    tipos_cocina.append([i, nombre, desc])

write_csv('tipos_cocina.csv', ['tipoId', 'nombre', 'descripcion'], tipos_cocina)

# --- Usuarios ---
paises = ['México', 'Guatemala', 'Colombia', 'Argentina', 'España',
          'Perú', 'Chile', 'Ecuador', 'Costa Rica', 'Estados Unidos']
usuarios = []
emails_set = set()
for i in range(1, NUM_USUARIOS + 1):
    nombre = fake.name()
    while True:
        email = f"user{i}@{fake.free_email_domain()}"
        if email not in emails_set:
            emails_set.add(email)
            break
    edad = random.randint(18, 70)
    pais = random.choice(paises)
    usuarios.append([i, nombre, email, edad, pais])

write_csv('usuarios.csv', ['userId', 'nombre', 'email', 'edad', 'pais'], usuarios)

# --- Restaurantes ---
prefijos_rest = ['La', 'El', 'Los', 'Casa', 'Rincón', 'Sabor', 'Don', 'Doña',
                 'Chef', 'Trattoria', 'Bistro', 'Café', 'Mesón', 'Jardín', 'Villa']
sufijos_rest = ['del Mar', 'Gourmet', 'Express', 'Dorado', 'Real', 'del Chef',
                'Tropical', 'Ancestral', 'Moderno', 'Clásico', 'de la Abuela',
                'Premium', 'Artesanal', 'Imperial', 'Orgánico']
nombres_base = ['Fuego', 'Luna', 'Sol', 'Estrella', 'Montaña', 'Río', 'Bosque',
                'Cielo', 'Tierra', 'Piedra', 'Olivo', 'Roble', 'Cerezo', 'Bambú',
                'Coral', 'Jade', 'Ámbar', 'Canela', 'Azafrán', 'Romero']

rangos_precios = ['$', '$$', '$$$', '$$$$']
restaurantes = []
nombres_rest_set = set()
for i in range(1, NUM_RESTAURANTES + 1):
    while True:
        nombre = f"{random.choice(prefijos_rest)} {random.choice(nombres_base)} {random.choice(sufijos_rest)}"
        if nombre not in nombres_rest_set:
            nombres_rest_set.add(nombre)
            break
    anio = random.randint(1990, 2025)
    rango = random.choice(rangos_precios)
    desc = fake.sentence(nb_words=8)
    restaurantes.append([i, nombre, anio, rango, desc])

write_csv('restaurantes.csv',
          ['restId', 'nombre', 'anio_apertura', 'rango_precios', 'descripcion'],
          restaurantes)

# --- Chefs ---
nacionalidades = ['Mexicana', 'Guatemalteca', 'Colombiana', 'Argentina', 'Española',
                  'Peruana', 'Italiana', 'Francesa', 'Japonesa', 'Estadounidense']
chefs = []
for i in range(1, NUM_CHEFS + 1):
    nombre = fake.name()
    fn = fake.date_of_birth(minimum_age=25, maximum_age=65).strftime('%Y-%m-%d')
    nac = random.choice(nacionalidades)
    chefs.append([i, nombre, fn, nac])

write_csv('chefs.csv', ['chefId', 'nombre', 'fecha_nacimiento', 'nacionalidad'], chefs)

# --- Platillos ---
platillos_nombres = [
    "Tacos al Pastor", "Pizza Margherita", "Sushi Roll Especial", "Pad Thai",
    "Ramen Tonkotsu", "Ceviche Clásico", "Paella Valenciana", "Risotto de Hongos",
    "Hamburguesa Gourmet", "Ensalada César", "Lomo Saltado", "Pollo Tikka Masala",
    "Bibimbap", "Gyros de Cordero", "Empanadas Argentinas", "Fettuccine Alfredo",
    "Tom Yum Kung", "Pho Vietnamita", "Fish and Chips", "Mole Poblano",
    "Lasaña Bolognesa", "Enchiladas Suizas", "Curry Verde", "Sashimi Variado",
    "Causa Limeña", "Churrasco", "Falafel", "Moussaka", "Ravioles de Ricota",
    "Dim Sum Variado", "Pozole Rojo", "Crème Brûlée", "Tiramisu",
    "Brownie con Helado", "Churros con Chocolate", "Tres Leches",
    "Carpaccio de Res", "Bruschetta", "Guacamole Artesanal", "Hummus",
    "Tostadas de Atún", "Pulpo a la Gallega", "Cochinita Pibil",
    "Arepa Reina Pepiada", "Bandeja Paisa", "Gnocchi al Pesto",
    "Tempura Mixta", "Shakshuka", "Bowl de Açaí", "Wrap Mediterráneo"
]

platillos = []
for i in range(1, NUM_PLATILLOS + 1):
    nombre = platillos_nombres[i - 1]
    precio = round(random.uniform(45, 350), 2)
    desc = fake.sentence(nb_words=6)
    platillos.append([i, nombre, precio, desc])

write_csv('platillos.csv', ['platilloId', 'nombre', 'precio', 'descripcion'], platillos)

# ═══════════════════════════════════════════════
# 2. RELACIONES
# ═══════════════════════════════════════════════

# --- CALIFICÓ (Usuario)-[CALIFICÓ]->(Restaurante) ---
# Cada usuario califica entre 3 y 15 restaurantes
calificaciones = []
cal_set = set()
for uid in range(1, NUM_USUARIOS + 1):
    num_cal = random.randint(3, 15)
    rests = random.sample(range(1, NUM_RESTAURANTES + 1), min(num_cal, NUM_RESTAURANTES))
    for rid in rests:
        if (uid, rid) not in cal_set:
            cal_set.add((uid, rid))
            punt = random.randint(1, 5)
            fecha = rand_date(2020, 2026)
            comentario = fake.sentence(nb_words=random.randint(4, 10))
            calificaciones.append([uid, rid, punt, fecha, comentario])

write_csv('calificaciones.csv',
          ['userId', 'restId', 'puntuacion', 'fecha', 'comentario'],
          calificaciones)

# --- VISITÓ (Usuario)-[VISITÓ]->(Restaurante) ---
# Cada usuario visita entre 5 y 20 restaurantes (puede ser múltiples visitas)
visitas = []
for uid in range(1, NUM_USUARIOS + 1):
    num_vis = random.randint(5, 20)
    rests = random.choices(range(1, NUM_RESTAURANTES + 1), k=num_vis)
    for rid in rests:
        fecha = rand_date(2020, 2026)
        consumo = round(random.uniform(80, 800), 2)
        reserva = random.choice(['true', 'false'])
        visitas.append([uid, rid, fecha, consumo, reserva])

write_csv('visitas.csv',
          ['userId', 'restId', 'fecha_visita', 'consumo', 'con_reserva'],
          visitas)

# --- ES_AMIGO_DE (Usuario)-[ES_AMIGO_DE]->(Usuario) ---
# Red de amistades: cada usuario tiene entre 3 y 20 amigos
amistades = []
ami_set = set()
for uid in range(1, NUM_USUARIOS + 1):
    num_amigos = random.randint(3, 20)
    amigos = random.sample([x for x in range(1, NUM_USUARIOS + 1) if x != uid], num_amigos)
    for aid in amigos:
        pair = tuple(sorted([uid, aid]))
        if pair not in ami_set:
            ami_set.add(pair)
            fecha = rand_date(2018, 2026)
            amistades.append([uid, aid, fecha])

write_csv('amistades.csv',
          ['userId1', 'userId2', 'fecha_amistad'],
          amistades)

# --- PERTENECE_A (Restaurante)-[PERTENECE_A]->(TipoCocina) ---
# Cada restaurante pertenece a 1-3 tipos de cocina
pertenece = []
pert_set = set()
for rid in range(1, NUM_RESTAURANTES + 1):
    num_tipos = random.randint(1, 3)
    tipos = random.sample(range(1, NUM_TIPOS_COCINA + 1), num_tipos)
    for tid in tipos:
        if (rid, tid) not in pert_set:
            pert_set.add((rid, tid))
            pertenece.append([rid, tid])

write_csv('pertenece_a.csv', ['restId', 'tipoId'], pertenece)

# --- OFRECE (Restaurante)-[OFRECE]->(Platillo) ---
# Cada restaurante ofrece entre 3 y 10 platillos (un platillo no se repite en el mismo restaurante)
ofrece = []
ofr_set = set()
# Asegurar que cada platillo sea ofrecido por al menos 1 restaurante
platillos_asignados = set()
for rid in range(1, NUM_RESTAURANTES + 1):
    num_plat = random.randint(3, 10)
    plats = random.sample(range(1, NUM_PLATILLOS + 1), min(num_plat, NUM_PLATILLOS))
    for pid in plats:
        if (rid, pid) not in ofr_set:
            ofr_set.add((rid, pid))
            platillos_asignados.add(pid)
            precio = round(random.uniform(50, 400), 2)
            disponible = random.choice(['true', 'false'])
            ofrece.append([rid, pid, precio, disponible])

# Asegurar cobertura de todos los platillos
for pid in range(1, NUM_PLATILLOS + 1):
    if pid not in platillos_asignados:
        rid = random.randint(1, NUM_RESTAURANTES)
        if (rid, pid) not in ofr_set:
            ofr_set.add((rid, pid))
            precio = round(random.uniform(50, 400), 2)
            ofrece.append([rid, pid, precio, random.choice(['true', 'false'])])

# Para Consulta 2: asegurar que varios platillos se ofrezcan en ≥3 restaurantes distintos
for pid in random.sample(range(1, NUM_PLATILLOS + 1), 20):
    rests_needed = random.randint(3, 6)
    available_rests = [r for r in range(1, NUM_RESTAURANTES + 1) if (r, pid) not in ofr_set]
    for rid in random.sample(available_rests, min(rests_needed, len(available_rests))):
        ofr_set.add((rid, pid))
        precio = round(random.uniform(50, 400), 2)
        ofrece.append([rid, pid, precio, random.choice(['true', 'false'])])

write_csv('ofrece.csv',
          ['restId', 'platilloId', 'precio', 'disponible'],
          ofrece)

# --- PREPARA (Chef)-[PREPARA]->(Platillo) ---
# Cada chef prepara entre 2 y 8 platillos
prepara = []
prep_set = set()
for cid in range(1, NUM_CHEFS + 1):
    num_plat = random.randint(2, 8)
    plats = random.sample(range(1, NUM_PLATILLOS + 1), min(num_plat, NUM_PLATILLOS))
    for pid in plats:
        if (cid, pid) not in prep_set:
            prep_set.add((cid, pid))
            estilo = random.choice(['Clásico', 'Moderno', 'Fusión', 'Tradicional',
                                    'Vanguardia', 'Rústico', 'Molecular'])
            esp = random.choice(['true', 'false'])
            prepara.append([cid, pid, estilo, esp])

write_csv('prepara.csv',
          ['chefId', 'platilloId', 'estilo', 'especialidad'],
          prepara)

# --- TRABAJA_EN (Chef)-[TRABAJA_EN]->(Restaurante) ---
# Cada chef trabaja en 1-3 restaurantes
trabaja = []
trab_set = set()
for cid in range(1, NUM_CHEFS + 1):
    num_rest = random.randint(1, 3)
    rests = random.sample(range(1, NUM_RESTAURANTES + 1), num_rest)
    for rid in rests:
        if (cid, rid) not in trab_set:
            trab_set.add((cid, rid))
            fecha_inicio = rand_date(2015, 2024)
            puesto = random.choice(['Chef Ejecutivo', 'Sous Chef', 'Chef de Partida',
                                    'Chef Pastelero', 'Chef de Línea', 'Chef Principal'])
            trabaja.append([cid, rid, fecha_inicio, puesto])

write_csv('trabaja_en.csv',
          ['chefId', 'restId', 'fecha_inicio', 'puesto'],
          trabaja)

# --- LE_GUSTA (Usuario)-[LE_GUSTA]->(TipoCocina) ---
# Cada usuario tiene entre 2 y 6 tipos de cocina que le gustan
le_gusta = []
lg_set = set()
for uid in range(1, NUM_USUARIOS + 1):
    num_tipos = random.randint(2, 6)
    tipos = random.sample(range(1, NUM_TIPOS_COCINA + 1), num_tipos)
    for tid in tipos:
        if (uid, tid) not in lg_set:
            lg_set.add((uid, tid))
            nivel = random.randint(1, 5)
            le_gusta.append([uid, tid, nivel])

write_csv('le_gusta.csv',
          ['userId', 'tipoId', 'nivel_interes'],
          le_gusta)

# ═══════════════════════════════════════════════
# Resumen
# ═══════════════════════════════════════════════
print("\n═══ Resumen de generación ═══")
print(f"  Nodos:")
print(f"    Usuarios:      {NUM_USUARIOS}")
print(f"    Restaurantes:  {NUM_RESTAURANTES}")
print(f"    Chefs:         {NUM_CHEFS}")
print(f"    Platillos:     {NUM_PLATILLOS}")
print(f"    TiposCocina:   {NUM_TIPOS_COCINA}")
print(f"  Relaciones:")
print(f"    CALIFICÓ:      {len(calificaciones)}")
print(f"    VISITÓ:        {len(visitas)}")
print(f"    ES_AMIGO_DE:   {len(amistades)}")
print(f"    PERTENECE_A:   {len(pertenece)}")
print(f"    OFRECE:        {len(ofrece)}")
print(f"    PREPARA:       {len(prepara)}")
print(f"    TRABAJA_EN:    {len(trabaja)}")
print(f"    LE_GUSTA:      {len(le_gusta)}")
print(f"\nArchivos generados en: {DATA_DIR}")
