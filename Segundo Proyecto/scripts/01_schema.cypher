// ═══════════════════════════════════════════════════════════════
// Proyecto 2 - Sistema de Recomendación de Restaurantes
// Script 01: Esquema - Constraints e Índices
// Curso: SBD2 - 2S2026 | Carné: 201114493
// ═══════════════════════════════════════════════════════════════

// --- Constraints de unicidad (actúan también como índices) ---

CREATE CONSTRAINT usuario_id IF NOT EXISTS
FOR (u:Usuario) REQUIRE u.userId IS UNIQUE;

CREATE CONSTRAINT restaurante_id IF NOT EXISTS
FOR (r:Restaurante) REQUIRE r.restId IS UNIQUE;

CREATE CONSTRAINT chef_id IF NOT EXISTS
FOR (c:Chef) REQUIRE c.chefId IS UNIQUE;

CREATE CONSTRAINT platillo_id IF NOT EXISTS
FOR (p:Platillo) REQUIRE p.platilloId IS UNIQUE;

CREATE CONSTRAINT tipo_cocina_id IF NOT EXISTS
FOR (t:TipoCocina) REQUIRE t.tipoId IS UNIQUE;

// --- Índices adicionales para optimizar consultas ---

CREATE INDEX usuario_email IF NOT EXISTS
FOR (u:Usuario) ON (u.email);

CREATE INDEX usuario_nombre IF NOT EXISTS
FOR (u:Usuario) ON (u.nombre);

CREATE INDEX restaurante_nombre IF NOT EXISTS
FOR (r:Restaurante) ON (r.nombre);

CREATE INDEX chef_nombre IF NOT EXISTS
FOR (c:Chef) ON (c.nombre);

CREATE INDEX tipo_cocina_nombre IF NOT EXISTS
FOR (t:TipoCocina) ON (t.nombre);
