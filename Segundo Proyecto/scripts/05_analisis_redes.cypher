// ═══════════════════════════════════════════════════════════════
// Proyecto 2 - Sistema de Recomendación de Restaurantes
// Script 05: Análisis de Redes (2 consultas)
// Curso: SBD2 - 2S2026 | Carné: 201114493
// ═══════════════════════════════════════════════════════════════

// ─────────────────────────────────────────────────────────────
// ANÁLISIS 1: Grados de Separación entre Usuarios
// ─────────────────────────────────────────────────────────────
// Encuentra la ruta más corta entre dos usuarios usando
// el algoritmo shortestPath sobre relaciones ES_AMIGO_DE.
// Muestra los nodos intermedios y la distancia.

// Ejemplo: Ruta más corta entre usuario 1 y usuario 100
MATCH (u1:Usuario {userId: 1}),
      (u2:Usuario {userId: 100}),
      path = shortestPath((u1)-[:ES_AMIGO_DE*]-(u2))
RETURN u1.nombre AS usuario_origen,
       u2.nombre AS usuario_destino,
       length(path) AS grados_separacion,
       [n IN nodes(path) | n.nombre] AS camino,
       [n IN nodes(path) | n.userId] AS ids_camino;

// ─── Variante: Múltiples pares de usuarios ───
// Calcula grados de separación entre varios pares representativos
UNWIND [[1,50], [10,200], [25,300], [5,450], [100,400]] AS par
MATCH (u1:Usuario {userId: par[0]}),
      (u2:Usuario {userId: par[1]}),
      path = shortestPath((u1)-[:ES_AMIGO_DE*]-(u2))
RETURN u1.nombre AS origen,
       u2.nombre AS destino,
       length(path) AS grados_separacion,
       [n IN nodes(path) | n.nombre] AS camino;

// ─── Variante: Distribución general de grados de separación ───
// Muestra la distribución de distancias entre una muestra de pares
MATCH (u1:Usuario), (u2:Usuario)
WHERE u1.userId < u2.userId
  AND u1.userId IN [1, 5, 10, 20, 50]
  AND u2.userId IN [100, 200, 300, 400, 500]
MATCH path = shortestPath((u1)-[:ES_AMIGO_DE*]-(u2))
WITH length(path) AS distancia, COUNT(*) AS cantidad
RETURN distancia AS grados_separacion,
       cantidad AS pares_con_esta_distancia
ORDER BY distancia;


// ─────────────────────────────────────────────────────────────
// ANÁLISIS 2: Restaurantes Altamente Conectados
// ─────────────────────────────────────────────────────────────
// Identifica restaurantes con mayor conectividad en la red:
// más chefs trabajando, más platillos notables ofrecidos,
// más tipos de cocina, y mayor actividad de usuarios.

// Vista completa de conectividad de restaurantes
MATCH (r:Restaurante)

// Contar chefs
OPTIONAL MATCH (chef:Chef)-[:TRABAJA_EN]->(r)
WITH r, COUNT(DISTINCT chef) AS num_chefs

// Contar platillos ofrecidos
OPTIONAL MATCH (r)-[:OFRECE]->(plat:Platillo)
WITH r, num_chefs, COUNT(DISTINCT plat) AS num_platillos

// Contar tipos de cocina
OPTIONAL MATCH (r)-[:PERTENECE_A]->(tc:TipoCocina)
WITH r, num_chefs, num_platillos, COUNT(DISTINCT tc) AS num_tipos_cocina

// Contar usuarios que visitaron
OPTIONAL MATCH (u:Usuario)-[:VISITO]->(r)
WITH r, num_chefs, num_platillos, num_tipos_cocina,
     COUNT(DISTINCT u) AS num_visitantes

// Contar calificaciones
OPTIONAL MATCH (:Usuario)-[cal:CALIFICO]->(r)
WITH r, num_chefs, num_platillos, num_tipos_cocina, num_visitantes,
     COUNT(cal) AS num_calificaciones,
     AVG(cal.puntuacion) AS promedio_rating

// Calcular score de conectividad
WITH r, num_chefs, num_platillos, num_tipos_cocina,
     num_visitantes, num_calificaciones, promedio_rating,
     (num_chefs * 3 + num_platillos * 2 + num_tipos_cocina +
      num_visitantes + num_calificaciones) AS score_conectividad

RETURN r.nombre AS restaurante,
       r.rango_precios AS rango_precios,
       r.anio_apertura AS anio_apertura,
       num_chefs AS chefs,
       num_platillos AS platillos,
       num_tipos_cocina AS tipos_cocina,
       num_visitantes AS visitantes_unicos,
       num_calificaciones AS total_calificaciones,
       ROUND(COALESCE(promedio_rating, 0), 2) AS promedio_rating,
       score_conectividad
ORDER BY score_conectividad DESC
LIMIT 15;

// ─── Variante: Platillos notables (ofrecidos en más restaurantes) ───
MATCH (p:Platillo)<-[:OFRECE]-(r:Restaurante)
WITH p, COUNT(DISTINCT r) AS restaurantes_que_lo_ofrecen,
     COLLECT(r.nombre)[..5] AS ejemplo_restaurantes
WHERE restaurantes_que_lo_ofrecen >= 3

// Chefs que preparan estos platillos notables
OPTIONAL MATCH (chef:Chef)-[:PREPARA]->(p)
WITH p, restaurantes_que_lo_ofrecen, ejemplo_restaurantes,
     COLLECT(chef.nombre) AS chefs_que_lo_preparan

RETURN p.nombre AS platillo_notable,
       restaurantes_que_lo_ofrecen,
       ejemplo_restaurantes,
       chefs_que_lo_preparan
ORDER BY restaurantes_que_lo_ofrecen DESC
LIMIT 10;
