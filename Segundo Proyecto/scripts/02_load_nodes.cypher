// ═══════════════════════════════════════════════════════════════
// Proyecto 2 - Sistema de Recomendación de Restaurantes
// Script 02: Carga de Nodos con LOAD CSV
// Curso: SBD2 - 2S2026 | Carné: 201114493
// ═══════════════════════════════════════════════════════════════
// NOTA: Antes de ejecutar, copiar los archivos CSV a la carpeta
// import/ de Neo4j, o usar file:/// con la ruta absoluta.
// Ajustar las rutas según la instalación.
// ═══════════════════════════════════════════════════════════════

// --- Cargar TipoCocina ---
LOAD CSV WITH HEADERS FROM 'file:///tipos_cocina.csv' AS row
MERGE (t:TipoCocina {tipoId: toInteger(row.tipoId)})
SET t.nombre = row.nombre,
    t.descripcion = row.descripcion;

// --- Cargar Usuarios ---
:auto LOAD CSV WITH HEADERS FROM 'file:///usuarios.csv' AS row
CALL {
  WITH row
  MERGE (u:Usuario {userId: toInteger(row.userId)})
  SET u.nombre = row.nombre,
      u.email = row.email,
      u.edad = toInteger(row.edad),
      u.pais = row.pais
} IN TRANSACTIONS OF 500 ROWS;

// --- Cargar Restaurantes ---
LOAD CSV WITH HEADERS FROM 'file:///restaurantes.csv' AS row
MERGE (r:Restaurante {restId: toInteger(row.restId)})
SET r.nombre = row.nombre,
    r.anio_apertura = toInteger(row.anio_apertura),
    r.rango_precios = row.rango_precios,
    r.descripcion = row.descripcion;

// --- Cargar Chefs ---
LOAD CSV WITH HEADERS FROM 'file:///chefs.csv' AS row
MERGE (c:Chef {chefId: toInteger(row.chefId)})
SET c.nombre = row.nombre,
    c.fecha_nacimiento = row.fecha_nacimiento,
    c.nacionalidad = row.nacionalidad;

// --- Cargar Platillos ---
LOAD CSV WITH HEADERS FROM 'file:///platillos.csv' AS row
MERGE (p:Platillo {platilloId: toInteger(row.platilloId)})
SET p.nombre = row.nombre,
    p.precio = toFloat(row.precio),
    p.descripcion = row.descripcion;
