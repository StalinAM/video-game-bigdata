# Video Game Big Data - Análisis con Hadoop, Spark y FastAPI

Sistema de análisis de reseñas de videojuegos utilizando tecnologías Big Data (HDFS, Spark) con una API REST para consultar los resultados.

## 📋 Requisitos Previos

- Docker Desktop instalado y ejecutándose
- Git Bash o WSL (para Windows)
- Al menos 8GB de RAM disponible
- 10GB de espacio en disco

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│              DENTRO DE DOCKER (VOLUMEN INTERNO)             │
│                                                             │
│  1. HDFS (namenode) → /videogames/Video_Games.json         │
│                           ↓                                 │
│  2. Spark procesa y escribe                                │
│     → shared-data:/data/results.csv (volumen interno)      │
│                           ↓                                 │
│  3. API lee desde shared-data:/data/results.csv            │
│     (mismo volumen, dentro de Docker)                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Solo expone puerto 8000
                            ▼
                 http://localhost:8000/stats
                     (JSON hacia fuera)
```

## 🚀 Guía de Ejecución Paso a Paso

### 1. Clonar el Repositorio

```bash
git clone https://github.com/StalinAM/video-game-bigdata.git
cd video-game-bigdata
```

### 2. Verificar la Estructura del Proyecto

```bash
ls -la
```

Deberías ver:

```
docker-compose.yml
api/
data/
  └── Video_Games.json
hadoop/
spark/
  └── spark_analysis.py
```

### 3. Levantar los Contenedores Docker

```bash
docker-compose up -d
```

Este comando creará y ejecutará:

- `namenode` - NameNode de Hadoop (puerto 9870)
- `datanode` - DataNode de Hadoop
- `spark-master` - Nodo maestro de Spark (puerto 8080)
- `spark-worker` - Nodo trabajador de Spark
- `api` - API FastAPI (puerto 8000)

**Verificar que los contenedores están corriendo:**

```bash
docker ps
```

### 4. Esperar a que HDFS Inicie

Espera aproximadamente 30 segundos para que el NameNode esté listo. Puedes verificar el estado en:

- HDFS Web UI: http://localhost:9870
- Spark Master UI: http://localhost:8080

### 5. Copiar el JSON al Contenedor NameNode

```bash
docker cp ./data/Video_Games.json namenode:/tmp/Video_Games.json
```

### 6. Subir el JSON a HDFS

```bash
docker exec -it namenode bash -c "hdfs dfs -mkdir -p /videogames && hdfs dfs -put -f /tmp/Video_Games.json /videogames/"
```

> **Nota:** Verás muchos mensajes `INFO sasl.SaslDataTransferClient` durante la carga. Esto es normal y muestra el progreso de la transferencia del archivo de 1.7GB. Espera a que termine (puede tomar 1-2 minutos).

**Verificar que el archivo está en HDFS:**

```bash
docker exec -it namenode bash -c "hdfs dfs -ls /videogames/"
```

Deberías ver algo como:

```
Found 1 items
-rw-r--r--   1 root supergroup 1702313074 2026-01-13 13:14 /videogames/Video_Games.json
```

### 7. Ejecutar el Job de Spark

```bash
docker exec spark-master /spark/bin/spark-submit /opt/spark-apps/spark_analysis.py
```

**Nota para PowerShell:**

```powershell
docker exec spark-master /spark/bin/spark-submit /opt/spark-apps/spark_analysis.py
```

El script realizará:

1. Lectura del JSON desde HDFS
2. Análisis de datos (promedio de puntuaciones por producto)
3. Generación del CSV en `/data/results.csv` (volumen interno de Docker)

**Salida esperada:**

```
only showing top 10 rows
✓ Archivo CSV generado exitosamente en /data/results.csv
```

### 8. Verificar que el CSV fue Generado

```bash
docker exec spark-master head -n 5 /data/results.csv
```

Deberías ver:

```
asin,avg_score,review_count
B00004SW06,5.0,14
B00002SVBA,5.0,17
...
```

### 9. Probar la API

**Endpoint raíz:**

```bash
curl http://localhost:8000/
```

Respuesta esperada:

```json
{ "message": "API de Análisis de Videojuegos Online" }
```

**Endpoint de estadísticas:**

```bash
curl http://localhost:8000/stats | head -c 500
```

Respuesta esperada (primeros registros):

```json
[
  {"asin":"B00004SW06","avg_score":5.0,"review_count":14},
  {"asin":"B00002SVBA","avg_score":5.0,"review_count":17},
  ...
]
```

**Abrir en el navegador:**

- API Root: http://localhost:8000
- Estadísticas: http://localhost:8000/stats
- Documentación interactiva: http://localhost:8000/docs

## 🔧 Comandos Útiles

### Ver logs de un contenedor

```bash
docker logs spark-master --follow
docker logs api --follow
```

### Reiniciar todos los servicios

```bash
docker-compose restart
```

### Detener todos los servicios

```bash
docker-compose down
```

### Eliminar volúmenes y empezar desde cero

```bash
docker-compose down -v
docker-compose up -d
```

### Acceder a un contenedor

```bash
docker exec -it spark-master bash
docker exec -it namenode bash
docker exec -it api bash
```

### Ver el estado de HDFS

```bash
docker exec -it namenode bash -c "hdfs dfsadmin -report"
```

## 📊 Endpoints de la API

| Método | Endpoint | Descripción                                                 |
| ------ | -------- | ----------------------------------------------------------- |
| GET    | `/`      | Mensaje de bienvenida                                       |
| GET    | `/stats` | Estadísticas de videojuegos (asin, avg_score, review_count) |
| GET    | `/docs`  | Documentación interactiva Swagger UI                        |
| GET    | `/redoc` | Documentación alternativa ReDoc                             |

## 🐛 Solución de Problemas

### Error: "Cannot connect to Docker daemon"

```bash
# Asegúrate de que Docker Desktop está ejecutándose
docker --version
```

### Error: "port is already allocated"

```bash
# Detener contenedores que usen los puertos
docker-compose down
# O cambiar los puertos en docker-compose.yml
```

### Error: "No such file or directory" al ejecutar spark-submit

```bash
# Usar MSYS_NO_PATHCONV=1 en Git Bash
MSYS_NO_PATHCONV=1 docker exec spark-master /spark/bin/spark-submit /opt/spark-apps/spark_analysis.py
```

### La API devuelve "Los datos aún no han sido procesados"

```bash
# Verificar que el CSV existe
MSYS_NO_PATHCONV=1 docker exec spark-master ls -la /data/

# Re-ejecutar el job de Spark
MSYS_NO_PATHCONV=1 docker exec spark-master /spark/bin/spark-submit /opt/spark-apps/spark_analysis.py
```

### HDFS está en modo seguro

```bash
docker exec -it namenode bash -c "hdfs dfsadmin -safemode leave"
```

## 📁 Estructura del Proyecto

```
video-game-bigdata/
├── docker-compose.yml          # Configuración de servicios Docker
├── README.md                   # Esta guía
├── api/
│   ├── dockerfile             # Imagen Docker de la API
│   ├── main.py                # Código de la API FastAPI
│   └── requirements.txt       # Dependencias Python
├── data/
│   └── Video_Games.json       # Dataset de reseñas (origen)
├── hadoop/
│   ├── core-site.xml          # Configuración de Hadoop Core
│   └── hdfs-site.xml          # Configuración de HDFS
└── spark/
    └── spark_analysis.py      # Script de análisis con PySpark
```

## 🔍 Detalles Técnicos

### Procesamiento de Datos con Spark

El script `spark_analysis.py` realiza:

1. **Lectura**: Lee el JSON desde HDFS (`hdfs://namenode:9000/videogames/Video_Games.json`)
2. **Limpieza**: Filtra registros con valores nulos en `asin` y `overall`
3. **Agregación**: Calcula el promedio de puntuación (`avg_score`) y cuenta de reseñas (`review_count`) por producto (`asin`)
4. **Ordenamiento**: Ordena por puntuación descendente
5. **Escritura**: Genera un único CSV en el volumen compartido interno

### Volúmenes de Docker

- `namenode`: Volumen persistente para metadatos de HDFS
- `datanode`: Volumen persistente para datos de HDFS
- `shared-data`: **Volumen compartido interno** entre `spark-master`, `spark-worker` y `api`
  - **No está montado en el host**
  - Solo los contenedores pueden acceder a él
  - Permite compartir `results.csv` entre Spark y la API

## 📈 Próximos Pasos

- Agregar más análisis (por plataforma, tendencias temporales)
- Implementar caché en la API
- Añadir tests automatizados
- Configurar CI/CD
- Agregar autenticación a la API

## 👤 Autor

**Stalin Andrade**

- GitHub: [@StalinAM](https://github.com/StalinAM)

## 📝 Licencia

Este proyecto es de código abierto y está disponible bajo la Licencia MIT.

---

**¿Preguntas o problemas?** Abre un issue en GitHub.
