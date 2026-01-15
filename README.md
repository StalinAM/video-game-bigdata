# 🎮 Video Game Big Data - Análisis con Hadoop, Spark y FastAPI

Sistema completo de análisis de reseñas de videojuegos utilizando tecnologías Big Data (HDFS, Spark) con una API REST para consultar los resultados. Incluye integración con **Easyparser API** para obtener nombres de productos de Amazon en tiempo real.

## 📋 Requisitos Previos

- Docker Desktop instalado y ejecutándose
- Git Bash o WSL (para Windows)
- Al menos 8GB de RAM disponible
- 10GB de espacio en disco
- **API Key de Easyparser** (para endpoints de productos con nombres)

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                   DENTRO DE DOCKER (VOLUMEN INTERNO)                │
│                                                                     │
│  1. HDFS (namenode) → /videogames/Video_Games.json                  │
│                           ↓                                         │
│  2. Spark procesa y genera 15 análisis                              │
│     → shared-data:/data/results/*.csv (volumen interno)             │
│                           ↓                                         │
│  3. API lee CSVs y consulta Easyparser API                          │
│     → shared-data:/data/results/*.csv + Easyparser                  │
│     → Caché de productos: /data/results/*.json                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            │ Expone puerto 8000
                            ▼
                 http://localhost:8000/docs
                     (17 endpoints JSON)
```

### Componentes del Sistema

- **HDFS**: Sistema de archivos distribuido para almacenar el dataset (1.7GB)
- **Spark**: Motor de procesamiento Big Data para análisis masivo de datos
- **FastAPI**: API REST con 17 endpoints para consultar resultados
- **Easyparser API**: Servicio externo para obtener nombres de productos de Amazon
- **Volumen Compartido**: Permite compartir datos entre Spark y la API

## 🚀 Guía de Ejecución Paso a Paso

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/StalinAM/video-game-bigdata.git
cd video-game-bigdata
```

### Paso 2: Configurar la API Key de Easyparser

**⚠️ IMPORTANTE**: Antes de levantar los contenedores, debes configurar tu API Key de Easyparser.

**Ubicación**: `api/amazon_scraper.py` (línea 15)

```python
# Configuración de Easyparser
EASYPARSER_API_KEY = 'TU_API_KEY_AQUI'  # ← Reemplaza con tu API key
EASYPARSER_ENDPOINT = 'https://realtime.easyparser.com/v1/request'
```

**¿Dónde obtener la API Key?**

- Regístrate en [Easyparser](https://easyparser.com/)
- Crea una cuenta gratuita
- Copia tu API Key desde el dashboard
- Pégala en el archivo `amazon_scraper.py`

**Nota**: Si no configuras la API Key, los endpoints de productos (`/products/*`) devolverán errores de autenticación.

### Paso 3: Verificar la Estructura del Proyecto

```bash
ls -la
```

Deberías ver:

```
docker-compose.yml
README.md
api/
  ├── amazon_scraper.py    # ← Configura tu API key aquí
  ├── dockerfile
  ├── main.py
  └── requirements.txt
data/
  └── Video_Games.json
hadoop/
  ├── core-site.xml
  └── hdfs-site.xml
spark/
  ├── comprehensive_analysis_simple.py
  └── spark_analysis.py
```

### Paso 4: Levantar los Contenedores Docker

```bash
docker-compose up -d
```

Este comando creará y ejecutará **5 contenedores**:

| Contenedor     | Servicio      | Puerto     | Descripción                    |
| -------------- | ------------- | ---------- | ------------------------------ |
| `namenode`     | HDFS NameNode | 9870, 9000 | Nodo maestro de HDFS           |
| `datanode`     | HDFS DataNode | -          | Nodo de almacenamiento de HDFS |
| `spark-master` | Spark Master  | 8080, 7077 | Nodo maestro de Spark          |
| `spark-worker` | Spark Worker  | -          | Nodo trabajador de Spark       |
| `api`          | FastAPI       | 8000       | API REST                       |

**Verificar que los contenedores están corriendo:**

```bash
docker ps
```

Deberías ver los 5 contenedores con estado `Up`.

### Paso 5: Verificar que los Servicios están Listos

Espera aproximadamente **30-60 segundos** para que todos los servicios inicien correctamente.

**Interfaces Web Disponibles:**

- 🌐 **HDFS NameNode**: http://localhost:9870
- 🌐 **Spark Master**: http://localhost:8080
- 🌐 **API Documentation**: http://localhost:8000/docs

**Verificar estado de HDFS:**

```bash
docker exec namenode hdfs dfsadmin -report
```

Deberías ver información sobre el cluster y los datanodes conectados.

### Paso 6: Copiar el Dataset al Contenedor

```bash
docker cp ./data/Video_Games.json namenode:/tmp/Video_Games.json
```

Este comando copia el archivo JSON (1.7GB) al contenedor del namenode.

### Paso 7: Subir el Dataset a HDFS

```bash
docker exec -it namenode bash -c "hdfs dfs -mkdir -p /videogames && hdfs dfs -put -f /tmp/Video_Games.json /videogames/"
```

> **⏳ Nota**: Este proceso puede tomar **1-3 minutos** dependiendo de tu hardware. Verás mensajes `INFO sasl.SaslDataTransferClient` que indican el progreso de la transferencia.

**Verificar que el archivo está en HDFS:**

```bash
docker exec namenode hdfs dfs -ls /videogames/
```

Salida esperada:

```
Found 1 items
-rw-r--r--   1 root supergroup 1702313074 2026-01-15 10:30 /videogames/Video_Games.json
```

### Paso 8: Ejecutar el Análisis de Spark

Tienes dos opciones de análisis:

#### Opción A: Análisis Básico ⚡ (Rápido - ~1 minuto)

```bash
docker exec spark-master /spark/bin/spark-submit /opt/spark-apps/spark_analysis.py
```

Genera un único archivo CSV con estadísticas básicas por juego.

#### Opción B: Análisis Completo 🌟 **RECOMENDADO** (~5-10 minutos)

```bash
# Git Bash / WSL
MSYS_NO_PATHCONV=1 docker exec spark-master /spark/bin/spark-submit /opt/spark-apps/comprehensive_analysis_simple.py

# PowerShell
docker exec spark-master /spark/bin/spark-submit /opt/spark-apps/comprehensive_analysis_simple.py
```

El análisis completo generará **15 archivos CSV** con análisis detallados:

| #   | Análisis                              | Archivo CSV                    |
| --- | ------------------------------------- | ------------------------------ |
| 1   | Estadísticas globales                 | `global_statistics.csv`        |
| 2   | Distribución de ratings               | `rating_distribution.csv`      |
| 3   | Actividad por año                     | `yearly_activity.csv`          |
| 4   | Actividad por mes                     | `monthly_activity.csv`         |
| 5   | Actividad por día de semana           | `day_of_week_analysis.csv`     |
| 6   | Top 1000 juegos más reseñados         | `top_reviewed_games.csv`       |
| 7   | Top 1000 juegos mejor valorados       | `top_rated_games.csv`          |
| 8   | Top 1000 juegos peor valorados        | `worst_rated_games.csv`        |
| 9   | Longitud de texto vs rating           | `length_vs_rating.csv`         |
| 10  | Palabras frecuentes positivas         | `positive_words_frequency.csv` |
| 11  | Palabras frecuentes negativas         | `negative_words_frequency.csv` |
| 12  | Detección de outliers                 | `rating_outliers.csv`          |
| 13  | Reseñas verificadas vs no verificadas | `verified_statistics.csv`      |
| 14  | Reseñas más útiles (helpful votes)    | `helpful_votes_analysis.csv`   |
| 15  | Top 1000 reviewers más activos        | `top_reviewers.csv`            |

**Salida esperada del análisis completo:**

```
📊 Leyendo datos desde HDFS...
✓ Datos cargados: 2565349 reseñas
1️⃣ Calculando estadísticas descriptivas globales...
✓ global_statistics.csv guardado exitosamente
2️⃣ Analizando distribución de ratings...
✓ rating_distribution.csv guardado exitosamente
3️⃣ Análisis temporal por año...
✓ yearly_activity.csv guardado exitosamente
4️⃣ Análisis temporal por mes...
✓ monthly_activity.csv guardado exitosamente
5️⃣ Top 1000 juegos más reseñados...
✓ top_reviewed_games.csv guardado exitosamente
6️⃣ Top 1000 juegos mejor valorados...
✓ top_rated_games.csv guardado exitosamente
7️⃣ Top 1000 juegos peor valorados...
✓ worst_rated_games.csv guardado exitosamente
8️⃣ Correlación longitud de texto vs rating...
✓ length_vs_rating.csv guardado exitosamente
9️⃣ Palabras más frecuentes en reseñas positivas...
✓ positive_words_frequency.csv guardado exitosamente
🔟 Palabras más frecuentes en reseñas negativas...
✓ negative_words_frequency.csv guardado exitosamente
1️⃣1️⃣ Detección de outliers en ratings...
✓ rating_outliers.csv guardado exitosamente
1️⃣2️⃣ Comparación: Reseñas verificadas vs no verificadas...
✓ verified_statistics.csv guardado exitosamente
1️⃣3️⃣ Análisis por día de la semana...
✓ day_of_week_analysis.csv guardado exitosamente
1️⃣4️⃣ Análisis de helpful votes...
✓ helpful_votes_analysis.csv guardado exitosamente
1️⃣5️⃣ Top 1000 reviewers más activos...
✓ top_reviewers.csv guardado exitosamente

============================================================
✅ Análisis completo finalizado!
📁 15 archivos generados en /data/results/
============================================================
```

### Paso 9: Verificar los Resultados Generados

**Listar archivos generados:**

```bash
docker exec spark-master ls -lh /data/results/
```

**Ver contenido de un archivo específico:**

```bash
# Estadísticas globales
docker exec spark-master head -n 10 /data/results/global_statistics.csv

# Top 10 juegos más reseñados
docker exec spark-master head -n 11 /data/results/top_reviewed_games.csv
```

### Paso 10: Probar la API

La API está disponible en **http://localhost:8000** con 17 endpoints organizados en 8 categorías.

**Documentación Interactiva:**

- 📚 **Swagger UI**: http://localhost:8000/docs
- 📖 **ReDoc**: http://localhost:8000/redoc

**Pruebas rápidas:**

```bash
# Información general de la API
curl http://localhost:8000/

# Estadísticas globales
curl http://localhost:8000/statistics/global

# Top 10 juegos más reseñados
curl "http://localhost:8000/games/top-reviewed?limit=10"
```

---

## 📡 Endpoints de la API

### 1️⃣ General

| Método | Endpoint | Descripción                                          |
| ------ | -------- | ---------------------------------------------------- |
| GET    | `/`      | Información general de la API y análisis disponibles |
| GET    | `/docs`  | Documentación interactiva (Swagger UI)               |
| GET    | `/redoc` | Documentación alternativa (ReDoc)                    |

### 2️⃣ Estadísticas (`/statistics`)

| Método | Endpoint                          | Descripción                                                                       | Ejemplo                                                     |
| ------ | --------------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| GET    | `/statistics/global`              | Estadísticas descriptivas globales (media, mediana, varianza, skewness, kurtosis) | `curl http://localhost:8000/statistics/global`              |
| GET    | `/statistics/rating-distribution` | Distribución de ratings (conteo y porcentaje por rating 1-5)                      | `curl http://localhost:8000/statistics/rating-distribution` |
| GET    | `/statistics/verified`            | Comparación entre reseñas verificadas vs no verificadas                           | `curl http://localhost:8000/statistics/verified`            |

### 3️⃣ Análisis Temporal (`/temporal`)

| Método | Endpoint                | Descripción                               | Ejemplo                                           |
| ------ | ----------------------- | ----------------------------------------- | ------------------------------------------------- |
| GET    | `/temporal/yearly`      | Actividad de reseñas por año              | `curl http://localhost:8000/temporal/yearly`      |
| GET    | `/temporal/monthly`     | Actividad de reseñas por mes              | `curl http://localhost:8000/temporal/monthly`     |
| GET    | `/temporal/day-of-week` | Actividad de reseñas por día de la semana | `curl http://localhost:8000/temporal/day-of-week` |

### 4️⃣ Análisis por Juego (`/games`)

| Método | Endpoint              | Parámetros             | Descripción                                  | Ejemplo                                                    |
| ------ | --------------------- | ---------------------- | -------------------------------------------- | ---------------------------------------------------------- |
| GET    | `/games/top-reviewed` | `limit` (default: 100) | Top juegos con más reseñas                   | `curl "http://localhost:8000/games/top-reviewed?limit=10"` |
| GET    | `/games/top-rated`    | `limit` (default: 100) | Top juegos mejor valorados (mín. 10 reseñas) | `curl "http://localhost:8000/games/top-rated?limit=10"`    |
| GET    | `/games/worst-rated`  | `limit` (default: 100) | Juegos peor valorados (mín. 10 reseñas)      | `curl "http://localhost:8000/games/worst-rated?limit=10"`  |

### 5️⃣ Análisis de Texto (`/text`)

| Método | Endpoint                 | Parámetros             | Descripción                                               | Ejemplo                                                     |
| ------ | ------------------------ | ---------------------- | --------------------------------------------------------- | ----------------------------------------------------------- |
| GET    | `/text/length-vs-rating` | -                      | Relación entre longitud de reseña y rating                | `curl http://localhost:8000/text/length-vs-rating`          |
| GET    | `/text/positive-words`   | `limit` (default: 100) | Palabras más frecuentes en reseñas positivas (rating ≥ 4) | `curl "http://localhost:8000/text/positive-words?limit=20"` |
| GET    | `/text/negative-words`   | `limit` (default: 100) | Palabras más frecuentes en reseñas negativas (rating ≤ 2) | `curl "http://localhost:8000/text/negative-words?limit=20"` |
| GET    | `/text/helpful-votes`    | `limit` (default: 100) | Reseñas con más votos de utilidad                         | `curl "http://localhost:8000/text/helpful-votes?limit=10"`  |

### 6️⃣ Análisis de Usuarios (`/users`)

| Método | Endpoint               | Parámetros             | Descripción                                 | Ejemplo                                                     |
| ------ | ---------------------- | ---------------------- | ------------------------------------------- | ----------------------------------------------------------- |
| GET    | `/users/top-reviewers` | `limit` (default: 100) | Usuarios más activos (más reseñas escritas) | `curl "http://localhost:8000/users/top-reviewers?limit=10"` |

### 7️⃣ Detección de Anomalías (`/outliers`)

| Método | Endpoint            | Parámetros             | Descripción                                             | Ejemplo                                                  |
| ------ | ------------------- | ---------------------- | ------------------------------------------------------- | -------------------------------------------------------- |
| GET    | `/outliers/ratings` | `limit` (default: 100) | Reseñas con ratings muy alejados del promedio del juego | `curl "http://localhost:8000/outliers/ratings?limit=50"` |

### 8️⃣ Productos con Nombres (`/products`) 🆕

**Requiere configuración de API Key de Easyparser** (ver [Paso 2](#paso-2-configurar-la-api-key-de-easyparser))

| Método | Endpoint                       | Parámetros           | Descripción                                           | Ejemplo                                                            |
| ------ | ------------------------------ | -------------------- | ----------------------------------------------------- | ------------------------------------------------------------------ |
| GET    | `/products/top-reviewed-names` | `limit` (default: 5) | Top 5 productos más reseñados con nombres de Amazon   | `curl "http://localhost:8000/products/top-reviewed-names?limit=5"` |
| GET    | `/products/top-rated-names`    | `limit` (default: 5) | Top 5 productos mejor valorados con nombres de Amazon | `curl "http://localhost:8000/products/top-rated-names?limit=5"`    |
| GET    | `/products/all-with-names`     | -                    | Ambos: Top reviewed y top rated con nombres           | `curl http://localhost:8000/products/all-with-names`               |

**Características de los endpoints de productos:**

- ✅ **Caché Inteligente**: Solo consulta Easyparser API si el JSON no existe
- ✅ **Sin límite de consultas**: Reutiliza datos cacheados
- ✅ **Información completa**: ASIN, nombre, URL, estado
- 📁 **Archivos de caché**: `/data/results/top_reviewed_with_names.json`, `/data/results/top_rated_with_names.json`

**Ejemplo de respuesta:**

```json
{
  "total": 5,
  "products": [
    {
      "asin": "B00JJNQG98",
      "product_name": "HyperX Cloud Gaming Headset",
      "url": "https://www.amazon.com/dp/B00JJNQG98",
      "status": "success"
    }
  ],
  "cached": true,
  "note": "Los nombres se obtienen de Easyparser API solo si no existe el caché"
}
```

### 9️⃣ Legacy (`/stats`)

| Método | Endpoint | Descripción                                                           | Ejemplo                            |
| ------ | -------- | --------------------------------------------------------------------- | ---------------------------------- |
| GET    | `/stats` | **[LEGACY]** Endpoint antiguo - usa `/games/top-reviewed` en su lugar | `curl http://localhost:8000/stats` |

---

## 📋 Ejemplos de Uso de la API

### Ejemplo 1: Obtener Estadísticas Globales

```bash
curl http://localhost:8000/statistics/global
```

**Respuesta:**

```json
{
  "mean_rating": 4.156,
  "stddev_rating": 1.234,
  "variance_rating": 1.523,
  "median_rating": 5.0,
  "total_reviews": 2565349,
  "avg_review_length": 287.5,
  "avg_word_count": 52.3
}
```

### Ejemplo 2: Top 5 Juegos Más Reseñados

```bash
curl "http://localhost:8000/games/top-reviewed?limit=5"
```

**Respuesta:**

```json
[
  {
    "asin": "B00178630A",
    "review_count": 15683,
    "avg_rating": 4.2
  },
  ...
]
```

### Ejemplo 3: Obtener Nombres de Productos desde Amazon

```bash
curl "http://localhost:8000/products/top-reviewed-names?limit=3"
```

**Respuesta:**

```json
{
  "total": 3,
  "products": [
    {
      "asin": "B00JJNQG98",
      "product_name": "HyperX Cloud Gaming Headset for PC & PS4",
      "url": "https://www.amazon.com/dp/B00JJNQG98",
      "status": "success"
    }
  ],
  "cached": true
}
```

### Ejemplo 4: Análisis Temporal por Año

```bash
curl http://localhost:8000/temporal/yearly
```

### Ejemplo 5: Palabras Positivas Más Frecuentes

```bash
curl "http://localhost:8000/text/positive-words?limit=10"
```

---

## 🔧 Comandos Útiles para Administración

### Gestión de Contenedores

```bash
# Ver logs de un contenedor específico
docker logs spark-master --follow
docker logs api --follow
docker logs namenode --tail 50

# Reiniciar un servicio específico
docker-compose restart api
docker-compose restart spark-master

# Reiniciar todos los servicios
docker-compose restart

# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (⚠️ elimina todos los datos)
docker-compose down -v

# Reconstruir y reiniciar la API (después de cambios en código)
docker-compose build api && docker-compose up -d api
```

### Acceso a Contenedores

```bash
# Acceder al shell de un contenedor
docker exec -it spark-master bash
docker exec -it namenode bash
docker exec -it api bash

# Ejecutar comando en contenedor
docker exec spark-master ls -la /data/results/
docker exec api cat /app/amazon_scraper.py
```

### Gestión de HDFS

```bash
# Ver estado del cluster HDFS
docker exec namenode hdfs dfsadmin -report

# Listar archivos en HDFS
docker exec namenode hdfs dfs -ls /videogames/

# Salir del modo seguro (si es necesario)
docker exec namenode hdfs dfsadmin -safemode leave

# Ver espacio usado en HDFS
docker exec namenode hdfs dfs -df -h

# Eliminar archivos de HDFS
docker exec namenode hdfs dfs -rm /videogames/Video_Games.json
```

### Gestión de Caché de Productos

```bash
# Listar archivos de caché
docker exec api ls -lh /data/results/*.json

# Eliminar caché para regenerar (fuerza nueva consulta a Easyparser)
docker exec api rm /data/results/top_reviewed_with_names.json
docker exec api rm /data/results/top_rated_with_names.json

# Ver contenido del caché
docker exec api cat /data/results/top_reviewed_with_names.json
```

### Monitoreo y Debugging

```bash
# Ver uso de recursos de contenedores
docker stats

# Inspeccionar un contenedor
docker inspect api

# Ver puertos expuestos
docker port api

# Verificar conectividad entre contenedores
docker exec api ping spark-master
docker exec spark-master ping namenode
```

---

### Productos devuelven "N/A - Título no encontrado"

**Problema**: Algunos ASINs son antiguos o no están disponibles en Amazon.

**Explicación**: Esto es **normal**. Algunos productos del dataset son de 2014-2018 y pueden:

- Ya no estar disponibles en Amazon
- Tener páginas desactivadas
- Ser regionales (solo disponibles en ciertos países)

**Solución**: Los productos con `"status": "success"` tienen información válida. Usa esos para tus análisis.

---

### Contenedores se reinician constantemente

**Problema**: Falta de recursos (RAM/CPU).

```bash
# Ver uso de recursos
docker stats

# Verificar logs de error
docker logs namenode
docker logs spark-master
```

**Solución**:

- Asigna más recursos a Docker Desktop (mínimo 8GB RAM)
- Cierra aplicaciones que consuman mucha memoria
- En `docker-compose.yml` reduce workers de Spark

---

## 📁 Estructura del Proyecto

```
video-game-bigdata/
├── docker-compose.yml              # Configuración de servicios Docker
├── README.md                       # Esta guía completa
│
├── api/                            # API REST (FastAPI)
│   ├── dockerfile                  # Imagen Docker de la API
│   ├── main.py                     # Código principal de la API (17 endpoints)
│   ├── amazon_scraper.py           # ⭐ Integración con Easyparser API
│   ├── requirements.txt            # Dependencias Python (fastapi, pandas, requests)
│   └── DOCUMENTACION_PRODUCTOS.md  # Documentación de endpoints de productos
│
├── data/                           # Datos de origen
│   └── Video_Games.json            # Dataset de reseñas (1.7GB, 2.5M reseñas)
│
├── hadoop/                         # Configuración de Hadoop/HDFS
│   ├── core-site.xml               # Configuración de Hadoop Core
│   └── hdfs-site.xml               # Configuración de HDFS
│
└── spark/                          # Scripts de análisis con PySpark
    ├── comprehensive_analysis_simple.py  # Análisis completo (15 CSV)
    └── spark_analysis.py                 # Análisis básico (1 CSV)
```

### Archivos Generados (dentro del volumen Docker)

```
/data/results/                      # Resultados del análisis de Spark
├── global_statistics.csv           # Estadísticas globales
├── rating_distribution.csv         # Distribución de ratings
├── yearly_activity.csv             # Actividad por año
├── monthly_activity.csv            # Actividad por mes
├── day_of_week_analysis.csv        # Actividad por día
├── top_reviewed_games.csv          # Top juegos más reseñados
├── top_rated_games.csv             # Top juegos mejor valorados
├── worst_rated_games.csv           # Juegos peor valorados
├── length_vs_rating.csv            # Longitud vs rating
├── positive_words_frequency.csv    # Palabras positivas
├── negative_words_frequency.csv    # Palabras negativas
├── rating_outliers.csv             # Outliers detectados
├── verified_statistics.csv         # Reseñas verificadas
├── helpful_votes_analysis.csv      # Reseñas más útiles
├── top_reviewers.csv               # Usuarios más activos
├── top_reviewed_with_names.json    # 🔄 Caché de productos (top reviewed)
└── top_rated_with_names.json       # 🔄 Caché de productos (top rated)
```

## 🔍 Detalles Técnicos

### Procesamiento de Datos con Spark

**Script**: `comprehensive_analysis_simple.py`

**Pipeline de procesamiento**:

1. **Lectura**: Lee el JSON desde HDFS (`hdfs://namenode:9000/videogames/Video_Games.json`)
2. **Limpieza**: Filtra registros con valores nulos, calcula métricas derivadas
3. **Transformaciones**:
   - Extrae año, mes, día de semana de las fechas
   - Calcula longitud de texto y conteo de palabras
   - Tokeniza y analiza texto con ML
4. **Agregaciones**: Calcula promedios, conteos, distribuciones por múltiples dimensiones
5. **Escritura**: Genera 15 archivos CSV en el volumen compartido

**Técnicas avanzadas utilizadas**:

- Window Functions para análisis de outliers
- TF-IDF para análisis de palabras frecuentes
- Percentiles y cuartiles para distribuciones
- Detección de anomalías con desviación estándar

### Arquitectura de la API

**Framework**: FastAPI 0.104.1

**Características**:

- 17 endpoints REST organizados en 8 categorías
- Validación automática de parámetros con Pydantic
- Documentación interactiva con Swagger UI y ReDoc
- CORS habilitado para uso desde frontends
- Caché inteligente para consultas a APIs externas
- Manejo robusto de errores con códigos HTTP apropiados

**Integración con Easyparser**:

- Sistema de caché basado en archivos JSON
- Consulta bajo demanda (solo si no existe caché)
- Manejo de errores HTTP, timeouts y productos no encontrados
- Estructura de respuesta enriquecida con metadatos

### Volúmenes de Docker

| Volumen       | Tipo         | Uso                         | Persistencia   |
| ------------- | ------------ | --------------------------- | -------------- |
| `namenode`    | Named volume | Metadatos de HDFS           | ✅ Persistente |
| `datanode`    | Named volume | Datos de HDFS (1.7GB)       | ✅ Persistente |
| `shared-data` | Named volume | Resultados CSV y caché JSON | ✅ Persistente |

**Ventajas del volumen compartido**:

- ✅ Los datos sobreviven a reinicios de contenedores
- ✅ Permite compartir resultados entre Spark y API
- ✅ No requiere acceso desde el host
- ✅ Mejor rendimiento que bind mounts

### Red de Docker

**Tipo**: Bridge network (`hadoop`)

**Comunicación entre contenedores**:

- `spark-master` → `namenode:9000` (lectura HDFS)
- `api` → `shared-data:/data/results` (lectura CSV)
- `api` → `https://realtime.easyparser.com` (consulta externa)

### Dataset

**Fuente**: Amazon Customer Reviews (Video Games)  
**Tamaño**: 1.7GB comprimido  
**Registros**: 2,565,349 reseñas  
**Periodo**: 1996-2018  
**Campos principales**:

- `asin`: Identificador único del producto
- `reviewerID`: ID del usuario que escribió la reseña
- `overall`: Rating (1-5 estrellas)
- `reviewText`: Texto de la reseña
- `summary`: Resumen de la reseña
- `unixReviewTime`: Timestamp Unix
- `verified`: Si la compra fue verificada
- `helpful`: Votos de utilidad [útiles, totales]

### Documentación Oficial

- [Apache Spark](https://spark.apache.org/docs/latest/)
- [Apache Hadoop](https://hadoop.apache.org/docs/stable/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Docker](https://docs.docker.com/)
- [Easyparser API](https://easyparser.com/docs)

### Dataset Original

- [Amazon Customer Reviews Dataset](https://nijianmo.github.io/amazon/index.html)
