// ═══════════════════════════════════════════════════════════════
// Proyecto 2 - Sistema de Recomendación de Restaurantes
// Script 03: Carga de Relaciones con LOAD CSV
// Curso: SBD2 - 2S2026 | Carné: 201114493
// ═══════════════════════════════════════════════════════════════

// --- CALIFICÓ: (Usuario)-[:CALIFICÓ]->(Restaurante) ---
:auto LOAD CSV WITH HEADERS FROM 'file:///calificaciones.csv' AS row
CALL {
  WITH row
  MATCH (u:Usuario {userId: toInteger(row.userId)})
  MATCH (r:Restaurante {restId: toInteger(row.restId)})
  MERGE (u)-[c:CALIFICO {fecha: row.fecha}]->(r)
  SET c.puntuacion = toInteger(row.puntuacion),
      c.comentario = row.comentario
} IN TRANSACTIONS OF 1000 ROWS;

// --- VISITÓ: (Usuario)-[:VISITÓ]->(Restaurante) ---
:auto LOAD CSV WITH HEADERS FROM 'file:///visitas.csv' AS row
CALL {
  WITH row
  MATCH (u:Usuario {userId: toInteger(row.userId)})
  MATCH (r:Restaurante {restId: toInteger(row.restId)})
  CREATE (u)-[v:VISITO]->(r)
  SET v.fecha_visita = row.fecha_visita,
      v.consumo = toFloat(row.consumo),
      v.con_reserva = CASE row.con_reserva WHEN 'true' THEN true ELSE false END
} IN TRANSACTIONS OF 1000 ROWS;

// --- ES_AMIGO_DE: (Usuario)-[:ES_AMIGO_DE]->(Usuario) ---
// Relación bidireccional: se crean ambas direcciones
:auto LOAD CSV WITH HEADERS FROM 'file:///amistades.csv' AS row
CALL {
  WITH row
  MATCH (u1:Usuario {userId: toInteger(row.userId1)})
  MATCH (u2:Usuario {userId: toInteger(row.userId2)})
  MERGE (u1)-[a:ES_AMIGO_DE]->(u2)
  SET a.fecha_amistad = row.fecha_amistad
  MERGE (u2)-[b:ES_AMIGO_DE]->(u1)
  SET b.fecha_amistad = row.fecha_amistad
} IN TRANSACTIONS OF 1000 ROWS;

// --- PERTENECE_A: (Restaurante)-[:PERTENECE_A]->(TipoCocina) ---
LOAD CSV WITH HEADERS FROM 'file:///pertenece_a.csv' AS row
MATCH (r:Restaurante {restId: toInteger(row.restId)})
MATCH (t:TipoCocina {tipoId: toInteger(row.tipoId)})
MERGE (r)-[:PERTENECE_A]->(t);

// --- OFRECE: (Restaurante)-[:OFRECE]->(Platillo) ---
:auto LOAD CSV WITH HEADERS FROM 'file:///ofrece.csv' AS row
CALL {
  WITH row
  MATCH (r:Restaurante {restId: toInteger(row.restId)})
  MATCH (p:Platillo {platilloId: toInteger(row.platilloId)})
  MERGE (r)-[o:OFRECE]->(p)
  SET o.precio = toFloat(row.precio),
      o.disponible = CASE row.disponible WHEN 'true' THEN true ELSE false END
} IN TRANSACTIONS OF 1000 ROWS;

// --- PREPARA: (Chef)-[:PREPARA]->(Platillo) ---
LOAD CSV WITH HEADERS FROM 'file:///prepara.csv' AS row
MATCH (c:Chef {chefId: toInteger(row.chefId)})
MATCH (p:Platillo {platilloId: toInteger(row.platilloId)})
MERGE (c)-[pr:PREPARA]->(p)
SET pr.estilo = row.estilo,
    pr.especialidad = CASE row.especialidad WHEN 'true' THEN true ELSE false END;

// --- TRABAJA_EN: (Chef)-[:TRABAJA_EN]->(Restaurante) ---
LOAD CSV WITH HEADERS FROM 'file:///trabaja_en.csv' AS row
MATCH (c:Chef {chefId: toInteger(row.chefId)})
MATCH (r:Restaurante {restId: toInteger(row.restId)})
MERGE (c)-[t:TRABAJA_EN]->(r)
SET t.fecha_inicio = row.fecha_inicio,
    t.puesto = row.puesto;

// --- LE_GUSTA: (Usuario)-[:LE_GUSTA]->(TipoCocina) ---
:auto LOAD CSV WITH HEADERS FROM 'file:///le_gusta.csv' AS row
CALL {
  WITH row
  MATCH (u:Usuario {userId: toInteger(row.userId)})
  MATCH (t:TipoCocina {tipoId: toInteger(row.tipoId)})
  MERGE (u)-[lg:LE_GUSTA]->(t)
  SET lg.nivel_interes = toInteger(row.nivel_interes)
} IN TRANSACTIONS OF 1000 ROWS;
