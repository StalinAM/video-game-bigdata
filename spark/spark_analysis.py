from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count
import os
import glob
import shutil

spark = SparkSession.builder \
    .appName("VideoGameReviewsAnalysis") \
    .getOrCreate()

# Leer JSON desde HDFS
df = spark.read.json("hdfs://namenode:9000/videogames/Video_Games.json")

# Mostrar esquema
df.printSchema()

# Eliminar valores nulos en campos críticos
df_clean = df.filter(col("asin").isNotNull() & col("overall").isNotNull())

# Análisis 1: promedio de puntuación por producto/juego
avg_score = df_clean.groupBy("asin") \
    .agg(
        avg("overall").alias("avg_score"),
        count("*").alias("review_count")
    ) \
    .orderBy(col("avg_score").desc())

avg_score.show(10)

# Guardar resultados en CSV para que la API los pueda leer
# Escribimos a una carpeta temporal con 1 partición y luego movemos el part-*.csv
# a un archivo único /data/results.csv para que la API (pandas) lo pueda leer directamente.
temp_dir_spark = "file:///data/results_temp"
temp_dir_local = "/data/results_temp"
final_file = "/data/results.csv"

# Escribir con una sola partición a carpeta temporal (en file system local, no HDFS)
avg_score.coalesce(1).write.mode("overwrite").option("header", "true").csv(temp_dir_spark)

# Buscar el archivo part-*.csv generado y moverlo a /data/results.csv
part_files = glob.glob(os.path.join(temp_dir_local, "part-*.csv"))
if part_files:
    part_file = part_files[0]
    # Eliminar archivo final si existe
    if os.path.exists(final_file):
        if os.path.isdir(final_file):
            shutil.rmtree(final_file)
        else:
            os.remove(final_file)
    # Mover el part-*.csv al archivo final
    shutil.move(part_file, final_file)
    print(f"✓ Archivo CSV generado exitosamente en {final_file}")

# Limpiar directorio temporal
shutil.rmtree(temp_dir_local, ignore_errors=True)

spark.stop()


