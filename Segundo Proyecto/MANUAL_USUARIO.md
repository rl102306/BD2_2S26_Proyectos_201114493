# Manual de Usuario - Proyecto 2
## Sistema de Recomendación de Restaurantes con Neo4j
**Curso:** SBD2 - 2S2026 | **Carné:** 201114493

---

## Diagrama Conceptual del Modelo

![Diagrama Conceptual del Modelo de Grafos](imagenes/diagrama_modelo.png)

---

## 1. Requisitos Previos

- **Neo4j Desktop 5.x** o **Neo4j Community Edition 5.x** instalado
- **Python 3.8+** con pip (para generar los datos)
- **Librería Faker:** `pip install faker`

## 2. Instalación y Configuración

### 2.1 Crear la Base de Datos

1. Abrir Neo4j Desktop y crear un nuevo proyecto.
2. Agregar una base de datos local (DBMS) con versión 5.x.
3. Iniciar la base de datos.

### 2.2 Generar los Datos CSV

```bash
# Instalar dependencia
pip install faker

# Ejecutar el generador
python generate_data.py
```

Esto creará 13 archivos CSV en la carpeta `data/`.

### 2.3 Copiar CSVs a Neo4j

Copiar todos los archivos de `data/` a la carpeta `import/` de Neo4j:

- **Neo4j Desktop:** Click en los tres puntos del DBMS → Open folder → Import
- **Linux:** `cp data/*.csv /var/lib/neo4j/import/`
- **macOS/Windows:** La ruta se muestra en la configuración del DBMS

### 2.4 Ejecutar los Scripts

Abrir Neo4j Browser (http://localhost:7474) y ejecutar en orden:

1. **Crear esquema:** Copiar y ejecutar `scripts/01_schema.cypher`
2. **Cargar nodos:** Copiar y ejecutar `scripts/02_load_nodes.cypher`
3. **Cargar relaciones:** Copiar y ejecutar `scripts/03_load_relationships.cypher`

> **Nota:** Ejecutar cada bloque LOAD CSV por separado si Neo4j Browser muestra errores. El prefijo `:auto` funciona en Neo4j Browser; si usa cypher-shell, omítalo y use `CALL { WITH row ... } IN TRANSACTIONS`.

## 3. Ejecución de Consultas

### 3.1 Consultas de Negocio

Abrir `scripts/04_consultas_negocio.cypher` y ejecutar cada consulta individualmente en Neo4j Browser.

**Consulta 1 - Recomendación por amigos:**
- Cambiar `targetUserId` por el ID del usuario deseado (1 a 500).
- Devuelve los 10 restaurantes más recomendados.

**Consulta 2 - Chefs de alto impacto:**
- No requiere parámetros. Muestra chefs con influencia en la plataforma.

**Consulta 3 - Restaurantes subvalorados:**
- No requiere parámetros. Identifica oportunidades de mejora.

**Consulta 4 - Discrepancia precios:**
- No requiere parámetros. Muestra inconsistencias entre precio declarado y real.

**Consulta 5 - Preferencia vs comportamiento:**
- No requiere parámetros. Revela diferencias entre gustos declarados y hábitos reales.

### 3.2 Análisis de Redes

Abrir `scripts/05_analisis_redes.cypher` y ejecutar cada bloque por separado.

**Análisis 1 - Grados de separación:**
- Cambiar los `userId` en las consultas para explorar diferentes pares.
- El resultado muestra la ruta completa entre dos usuarios.

**Análisis 2 - Restaurantes conectados:**
- No requiere parámetros. Presenta un ranking de conectividad.

## 4. Verificación de Datos

Para verificar que los datos se cargaron correctamente:

```cypher
// Contar nodos por tipo
MATCH (n) RETURN labels(n)[0] AS tipo, COUNT(n) AS cantidad ORDER BY tipo;

// Contar relaciones por tipo
MATCH ()-[r]->() RETURN type(r) AS tipo, COUNT(r) AS cantidad ORDER BY tipo;
```

Resultados esperados:
- Usuario: 500, Restaurante: 200, Chef: 100, Platillo: 50, TipoCocina: 15
- Relaciones: totales ~21,000+

## 5. Solución de Problemas

| Problema | Solución |
|----------|----------|
| "File not found" en LOAD CSV | Verificar que los CSV estén en la carpeta `import/` de Neo4j |
| Error de memoria | Aumentar heap en neo4j.conf: `server.memory.heap.max_size=2g` |
| `:auto` no reconocido | Usar Neo4j Browser 5.x o quitar `:auto` en cypher-shell |
| Duplicados al re-ejecutar | Los scripts usan MERGE, que evita duplicados en nodos; para relaciones con CREATE, borrar antes: `MATCH ()-[r:VISITO]->() DELETE r` |
