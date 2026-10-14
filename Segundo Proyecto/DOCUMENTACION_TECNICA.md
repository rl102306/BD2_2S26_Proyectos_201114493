# Documentación Técnica - Proyecto 2
## Sistema de Recomendación de Restaurantes con Neo4j
**Curso:** Sistemas de Bases de Datos 2 (SBD2) - Sección N - 2S2026  
**Carné:** 201114493  
**Universidad de San Carlos de Guatemala - Facultad de Ingeniería**

---

## 1. Modelo de Grafos

### 1.1 Nodos (Etiquetas)

| Etiqueta | Propiedades | Descripción |
|----------|------------|-------------|
| **Usuario** | userId (INT), nombre (STRING), email (STRING), edad (INT), pais (STRING) | Usuarios de la plataforma que visitan y califican restaurantes |
| **Restaurante** | restId (INT), nombre (STRING), anio_apertura (INT), rango_precios (STRING: $-$$$$), descripcion (STRING) | Establecimientos gastronómicos registrados |
| **TipoCocina** | tipoId (INT), nombre (STRING), descripcion (STRING) | Categorías culinarias (Mexicana, Italiana, etc.) |
| **Chef** | chefId (INT), nombre (STRING), fecha_nacimiento (STRING), nacionalidad (STRING) | Profesionales culinarios que trabajan en restaurantes |
| **Platillo** | platilloId (INT), nombre (STRING), precio (FLOAT), descripcion (STRING) | Platos específicos ofrecidos en los restaurantes |

### 1.2 Relaciones

| Relación | Origen | Destino | Propiedades | Descripción |
|----------|--------|---------|-------------|-------------|
| **CALIFICO** | Usuario | Restaurante | puntuacion (INT 1-5), fecha (STRING), comentario (STRING) | Calificación de un usuario a un restaurante |
| **VISITO** | Usuario | Restaurante | fecha_visita (STRING), consumo (FLOAT), con_reserva (BOOLEAN) | Registro de visita con monto consumido |
| **ES_AMIGO_DE** | Usuario | Usuario | fecha_amistad (STRING) | Relación de amistad bidireccional |
| **PERTENECE_A** | Restaurante | TipoCocina | — | Clasificación del restaurante por tipo de cocina |
| **OFRECE** | Restaurante | Platillo | precio (FLOAT), disponible (BOOLEAN) | Platillo disponible en el menú del restaurante |
| **PREPARA** | Chef | Platillo | estilo (STRING), especialidad (BOOLEAN) | Chef que sabe preparar un platillo |
| **TRABAJA_EN** | Chef | Restaurante | fecha_inicio (STRING), puesto (STRING) | Empleo actual del chef en un restaurante |
| **LE_GUSTA** | Usuario | TipoCocina | nivel_interes (INT 1-5) | Preferencia declarada del usuario |

### 1.3 Diagrama Conceptual del Modelo

![Diagrama Conceptual del Modelo de Grafos](imagenes/diagrama_modelo.png)

### 1.4 Reglas de Negocio

1. Un usuario puede calificar y visitar múltiples restaurantes; cada calificación tiene puntuación entre 1 y 5 estrellas.
2. Los restaurantes pueden pertenecer a múltiples tipos de cocina y ofrecer múltiples platillos.
3. Un restaurante NO puede ofrecer el mismo platillo más de una vez (constraint de unicidad en OFRECE por par restaurante-platillo).
4. Los chefs pueden trabajar en múltiples restaurantes a lo largo del tiempo y preparar múltiples platillos.
5. Las relaciones ES_AMIGO_DE son bidireccionales y se utilizan para recomendaciones hasta 3 grados de separación.
6. El sistema recomienda restaurantes basándose en calificaciones altas (≥4) de amigos, excluyendo restaurantes ya visitados.

## 2. Implementación y Carga de Datos

### 2.1 Tecnologías Utilizadas

- **Base de datos:** Neo4j Community/Desktop 5.x+
- **Lenguaje de consultas:** Cypher
- **Generación de datos:** Python 3.x con librería Faker
- **Carga masiva:** LOAD CSV con CALL IN TRANSACTIONS

### 2.2 Estructura de Archivos

```
proyecto2_neo4j/
├── generate_data.py              # Script Python para generar CSVs
├── data/                         # Archivos CSV generados
│   ├── usuarios.csv              (500 registros)
│   ├── restaurantes.csv          (200 registros)
│   ├── chefs.csv                 (100 registros)
│   ├── platillos.csv             (50 registros)
│   ├── tipos_cocina.csv          (15 registros)
│   ├── calificaciones.csv        (~4,500 relaciones)
│   ├── visitas.csv               (~6,300 relaciones)
│   ├── amistades.csv             (~5,600 relaciones)
│   ├── pertenece_a.csv           (~400 relaciones)
│   ├── ofrece.csv                (~1,400 relaciones)
│   ├── prepara.csv               (~520 relaciones)
│   ├── trabaja_en.csv            (~200 relaciones)
│   └── le_gusta.csv              (~2,000 relaciones)
├── scripts/
│   ├── 01_schema.cypher          # Constraints e índices
│   ├── 02_load_nodes.cypher      # Carga de nodos
│   ├── 03_load_relationships.cypher  # Carga de relaciones
│   ├── 04_consultas_negocio.cypher   # 5 consultas obligatorias
│   └── 05_analisis_redes.cypher      # 2 análisis de redes
├── DOCUMENTACION_TECNICA.md      # Este documento
└── MANUAL_USUARIO.md             # Manual de usuario
```

### 2.3 Volumen de Datos

| Entidad | Cantidad Mínima Requerida | Cantidad Generada |
|---------|--------------------------|-------------------|
| Usuarios | 500 | 500 |
| Restaurantes | 200 | 200 |
| Chefs | 100 | 100 |
| Platillos | 50 | 50 |
| Tipos de Cocina | 15 | 15 |

### 2.4 Constraints e Índices

Se crearon constraints de unicidad para los IDs de cada tipo de nodo, que a su vez generan índices automáticos. Se añadieron índices adicionales sobre campos de búsqueda frecuente (nombre, email).

### 2.5 Proceso de Carga

1. Se ejecuta primero `01_schema.cypher` para crear constraints e índices.
2. `02_load_nodes.cypher` carga todos los nodos usando MERGE para evitar duplicados.
3. `03_load_relationships.cypher` carga todas las relaciones usando MATCH + MERGE/CREATE.
4. Se utiliza `CALL { ... } IN TRANSACTIONS OF N ROWS` para carga eficiente en lotes.

## 3. Consultas de Negocio

### Consulta 1: Recomendación por Amigos
Utiliza traversal de grafos hasta 3 grados de separación (`[:ES_AMIGO_DE*1..3]`) para encontrar restaurantes bien calificados (≥4 estrellas) por amigos, excluyendo restaurantes ya visitados. Prioriza por cantidad de amigos coincidentes y promedio de calificación.

### Consulta 2: Chefs de Alto Impacto
Identifica chefs que trabajan en restaurantes con rating promedio >4 y cuyos platillos se ofrecen en ≥3 restaurantes distintos, demostrando tanto calidad como alcance.

### Consulta 3: Restaurantes Subvalorados
Encuentra restaurantes cuya tasa de reservación supera el promedio de la plataforma pero su calificación está por debajo del promedio, indicando popularidad práctica no reflejada en ratings.

### Consulta 4: Discrepancia Precios vs Consumo
Compara el rango de precios declarado ($, $$, $$$, $$$$) con el consumo promedio real de los visitantes, asignando rangos numéricos esperados y calculando la discrepancia.

### Consulta 5: Preferencia Declarada vs Comportamiento
Contrasta el tipo de cocina con mayor nivel de interés (LE_GUSTA) contra el tipo de cocina más visitado (VISITÓ→PERTENECE_A), revelando diferencias entre lo que los usuarios dicen preferir y lo que realmente consumen.

## 4. Análisis de Redes

### Análisis 1: Grados de Separación
Usa el algoritmo `shortestPath` de Neo4j para encontrar la ruta más corta entre pares de usuarios a través de relaciones ES_AMIGO_DE. Incluye variantes para múltiples pares y distribución estadística de distancias.

### Análisis 2: Restaurantes Altamente Conectados
Calcula un score de conectividad ponderado considerando: número de chefs (×3), platillos ofrecidos (×2), tipos de cocina, visitantes únicos y calificaciones. Incluye identificación de platillos notables presentes en múltiples restaurantes.
