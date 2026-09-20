-- Keyspace del sistema de reservas aéreas.
-- NetworkTopologyStrategy: aunque el despliegue actual es de un solo
-- datacenter (dc1), permite agregar DCs sin recrear el keyspace y es la
-- estrategia recomendada para cualquier entorno distinto a pruebas locales.
-- RF=3 sobre 3 nodos: cada nodo mantiene una copia completa, lo que permite
-- que QUORUM (2 de 3) siga operando con un nodo caído.

DROP KEYSPACE IF EXISTS aerolinea;

CREATE KEYSPACE aerolinea
WITH replication = {
  'class': 'NetworkTopologyStrategy',
  'dc1': 3
};
