// ═══════════════════════════════════════════════════════════════
// Proyecto 2 - Sistema de Recomendación de Restaurantes
// Script 04: Consultas de Negocio Obligatorias (5 consultas)
// Curso: SBD2 - 2S2026 | Carné: 201114493
// ═══════════════════════════════════════════════════════════════

// ─────────────────────────────────────────────────────────────
// CONSULTA 1: Recomendación de Restaurantes por Amigos
// ─────────────────────────────────────────────────────────────
// Recomienda restaurantes basándose en calificaciones ≥4 de amigos
// hasta 3 grados de separación, excluyendo restaurantes ya visitados.
// Prioriza por: cantidad de amigos coincidentes y promedio de calificación.
// Parámetro: cambiar el userId para el usuario deseado.

WITH 1 AS targetUserId
MATCH (yo:Usuario {userId: targetUserId})

// Encontrar amigos hasta 3 grados de separación
MATCH (yo)-[:ES_AMIGO_DE*1..3]-(amigo:Usuario)
WHERE amigo <> yo

// Amigos que calificaron restaurantes con ≥4 estrellas
MATCH (amigo)-[cal:CALIFICO]->(rest:Restaurante)
WHERE cal.puntuacion >= 4

// Excluir restaurantes que el usuario ya visitó
WITH yo, rest, amigo, cal
WHERE NOT EXISTS {
  MATCH (yo)-[:VISITO]->(rest)
}

// Agregar métricas de recomendación
WITH rest,
     COUNT(DISTINCT amigo) AS amigos_coincidentes,
     AVG(cal.puntuacion) AS promedio_calificacion,
     COLLECT(DISTINCT amigo.nombre)[..3] AS nombres_amigos

RETURN rest.nombre AS restaurante,
       rest.rango_precios AS rango_precios,
       amigos_coincidentes,
       ROUND(promedio_calificacion, 2) AS promedio_calificacion,
       nombres_amigos AS recomendado_por
ORDER BY amigos_coincidentes DESC, promedio_calificacion DESC
LIMIT 10;


// ─────────────────────────────────────────────────────────────
// CONSULTA 2: Chefs de Alto Impacto
// ─────────────────────────────────────────────────────────────
// Chefs que trabajan en restaurantes con calificación promedio >4
// Y cuyos platillos se ofrecen en ≥3 restaurantes distintos.

MATCH (chef:Chef)-[:TRABAJA_EN]->(rest:Restaurante)<-[cal:CALIFICO]-(:Usuario)
WITH chef, rest, AVG(cal.puntuacion) AS avg_rating
WHERE avg_rating > 4

WITH chef, COLLECT(DISTINCT rest.nombre) AS restaurantes_top

// Verificar que sus platillos estén en ≥3 restaurantes
MATCH (chef)-[:PREPARA]->(plat:Platillo)<-[:OFRECE]-(r2:Restaurante)
WITH chef, restaurantes_top,
     plat, COUNT(DISTINCT r2) AS num_restaurantes_plato
WHERE num_restaurantes_plato >= 3

RETURN chef.nombre AS chef,
       chef.nacionalidad AS nacionalidad,
       restaurantes_top AS restaurantes_con_rating_alto,
       COLLECT(plat.nombre) AS platillos_en_multiples_restaurantes,
       COLLECT(num_restaurantes_plato) AS restaurantes_por_platillo
ORDER BY SIZE(restaurantes_top) DESC, SIZE(COLLECT(plat.nombre)) DESC
LIMIT 15;


// ─────────────────────────────────────────────────────────────
// CONSULTA 3: Restaurantes Subvalorados
// ─────────────────────────────────────────────────────────────
// Restaurantes con tasa de reserva superior al promedio de la
// plataforma pero calificación inferior al promedio general.

// Calcular promedios de la plataforma
MATCH (:Usuario)-[v:VISITO]->(:Restaurante)
WITH AVG(CASE WHEN v.con_reserva THEN 1.0 ELSE 0.0 END) AS avg_reserva_plataforma

MATCH (:Usuario)-[c:CALIFICO]->(:Restaurante)
WITH avg_reserva_plataforma,
     AVG(c.puntuacion) AS avg_rating_plataforma

// Evaluar cada restaurante
MATCH (r:Restaurante)<-[v:VISITO]-(:Usuario)
WITH r, avg_reserva_plataforma, avg_rating_plataforma,
     AVG(CASE WHEN v.con_reserva THEN 1.0 ELSE 0.0 END) AS tasa_reserva_rest,
     COUNT(v) AS total_visitas

MATCH (r)<-[c:CALIFICO]-(:Usuario)
WITH r, avg_reserva_plataforma, avg_rating_plataforma,
     tasa_reserva_rest, total_visitas,
     AVG(c.puntuacion) AS avg_rating_rest,
     COUNT(c) AS total_calificaciones

WHERE tasa_reserva_rest > avg_reserva_plataforma
  AND avg_rating_rest < avg_rating_plataforma

RETURN r.nombre AS restaurante,
       r.rango_precios AS rango_precios,
       ROUND(tasa_reserva_rest * 100, 1) AS porcentaje_reservas,
       ROUND(avg_reserva_plataforma * 100, 1) AS promedio_reservas_plataforma,
       ROUND(avg_rating_rest, 2) AS rating_restaurante,
       ROUND(avg_rating_plataforma, 2) AS rating_promedio_plataforma,
       total_visitas,
       total_calificaciones
ORDER BY (tasa_reserva_rest - avg_reserva_plataforma) DESC
LIMIT 15;


// ─────────────────────────────────────────────────────────────
// CONSULTA 4: Discrepancia Rango de Precios vs Consumo Real
// ─────────────────────────────────────────────────────────────
// Compara el rango de precios declarado del restaurante con el
// consumo promedio real de los visitantes e identifica las
// mayores discrepancias.

// Definir rangos de precios esperados
MATCH (r:Restaurante)<-[v:VISITO]-(:Usuario)
WITH r,
     AVG(v.consumo) AS consumo_promedio,
     COUNT(v) AS total_visitas,
     r.rango_precios AS rango_declarado,
     CASE r.rango_precios
       WHEN '$'    THEN 150.0
       WHEN '$$'   THEN 300.0
       WHEN '$$$'  THEN 500.0
       WHEN '$$$$' THEN 750.0
     END AS consumo_esperado_max,
     CASE r.rango_precios
       WHEN '$'    THEN 50.0
       WHEN '$$'   THEN 150.0
       WHEN '$$$'  THEN 300.0
       WHEN '$$$$' THEN 500.0
     END AS consumo_esperado_min

WITH r, consumo_promedio, total_visitas, rango_declarado,
     consumo_esperado_max, consumo_esperado_min,
     CASE
       WHEN consumo_promedio > consumo_esperado_max THEN 'Más caro de lo declarado'
       WHEN consumo_promedio < consumo_esperado_min THEN 'Más barato de lo declarado'
       ELSE 'Consistente'
     END AS clasificacion,
     ABS(consumo_promedio - (consumo_esperado_min + consumo_esperado_max) / 2)
       AS discrepancia_absoluta

WHERE clasificacion <> 'Consistente'

RETURN r.nombre AS restaurante,
       rango_declarado,
       ROUND(consumo_promedio, 2) AS consumo_promedio_real,
       ROUND(consumo_esperado_min, 2) AS rango_min_esperado,
       ROUND(consumo_esperado_max, 2) AS rango_max_esperado,
       clasificacion,
       ROUND(discrepancia_absoluta, 2) AS discrepancia,
       total_visitas
ORDER BY discrepancia_absoluta DESC
LIMIT 20;


// ─────────────────────────────────────────────────────────────
// CONSULTA 5: Discrepancia Cocina Favorita Declarada vs Visitada
// ─────────────────────────────────────────────────────────────
// Compara el tipo de cocina favorita declarada (LE_GUSTA con
// mayor nivel_interes) con el tipo de cocina más visitada
// (a través de VISITÓ→PERTENECE_A). Muestra usuarios con
// discrepancia entre preferencia y comportamiento.

// Cocina favorita declarada (mayor nivel_interes)
MATCH (u:Usuario)-[lg:LE_GUSTA]->(tc_fav:TipoCocina)
WITH u, tc_fav, lg.nivel_interes AS interes
ORDER BY u.userId, interes DESC
WITH u, COLLECT(tc_fav)[0] AS cocina_favorita_declarada,
        COLLECT(interes)[0] AS max_interes

// Cocina más visitada
MATCH (u)-[:VISITO]->(r:Restaurante)-[:PERTENECE_A]->(tc_vis:TipoCocina)
WITH u, cocina_favorita_declarada, max_interes,
     tc_vis, COUNT(*) AS visitas_por_tipo
ORDER BY u.userId, visitas_por_tipo DESC
WITH u, cocina_favorita_declarada, max_interes,
     COLLECT(tc_vis)[0] AS cocina_mas_visitada,
     COLLECT(visitas_por_tipo)[0] AS max_visitas

// Filtrar solo discrepancias
WHERE cocina_favorita_declarada <> cocina_mas_visitada

RETURN u.nombre AS usuario,
       u.pais AS pais,
       cocina_favorita_declarada.nombre AS cocina_favorita_declarada,
       max_interes AS nivel_interes_declarado,
       cocina_mas_visitada.nombre AS cocina_mas_visitada,
       max_visitas AS visitas_a_cocina_mas_visitada
ORDER BY max_visitas DESC
LIMIT 20;
