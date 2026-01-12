from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count

spark = SparkSession.builder \
    .appName("VideoGameReviewsAnalysis") \
    .getOrCreate()

# Leer JSON desde HDFS
df = spark.read.json("hdfs://namenode:9000/videogames/Video_Games.json")

# Mostrar esquema
df.printSchema()

# Eliminar valores nulos
df_clean = df.dropna()

# Análisis 1: promedio de puntuación por juego
avg_score = df_clean.groupBy("game_title") \
    .agg(avg("review_score").alias("avg_score")) \
    .orderBy(col("avg_score").desc())

avg_score.show(10)

# Análisis 2: número de reseñas por plataforma
reviews_platform = df_clean.groupBy("platform") \
    .agg(count("*").alias("total_reviews")) \
    .orderBy(col("total_reviews").desc())

reviews_platform.show()

# Guardar resultados en CSV para que la API los pueda leer
avg_score.coalesce(1).write.mode("overwrite").option("header", "true").csv("/data/results_temp")

# Leer el CSV generado y guardarlo en el formato final
results_df = spark.read.option("header", "true").csv("/data/results_temp")
results_df.write.mode("overwrite").option("header", "true").csv("/data/results.csv")

# Limpiar archivo temporal
import subprocess
subprocess.run(["rm", "-rf", "/data/results_temp"], check=False)

spark.stop()

