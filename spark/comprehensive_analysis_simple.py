#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análisis Completo de Reseñas de Videojuegos - Versión Simplificada
Sin dependencias de ML libraries (no requiere numpy)
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, avg, sum as spark_sum, min as spark_min, max as spark_max,
    stddev, variance, year, month, length, when, desc, asc, round as spark_round,
    lower, split, explode, regexp_replace, trim, countDistinct
)
from pyspark.sql.window import Window
import os
import glob
import shutil

# Función helper para guardar resultados (basada en spark_analysis.py)
def save_result(df, name):
    """Guarda un DataFrame en CSV con manejo de archivos part-*"""
    temp_dir_spark = f"file:///data/results/{name}_temp"
    temp_dir_local = f"/data/results/{name}_temp"
    final_file = f"/data/results/{name}.csv"
    
    # Escribir con una sola partición a carpeta temporal
    df.coalesce(1).write.mode("overwrite").option("header", "true").csv(temp_dir_spark)
    
    # Buscar el archivo part-*.csv generado y moverlo al nombre final
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
        print(f"✓ {name}.csv guardado exitosamente")
    
    # Limpiar directorio temporal
    shutil.rmtree(temp_dir_local, ignore_errors=True)

# Crear sesión de Spark
spark = SparkSession.builder \
    .appName("Comprehensive Video Game Analysis - Simple") \
    .getOrCreate()

# Leer datos desde HDFS
print("📊 Leyendo datos desde HDFS...")
df = spark.read.json("hdfs://namenode:9000/videogames/Video_Games.json")

# Limpieza básica
df = df.filter(col("asin").isNotNull() & col("overall").isNotNull())
df = df.withColumn("reviewTime_unix", col("unixReviewTime").cast("timestamp"))
df = df.withColumn("reviewText_length", length(col("reviewText")))
df = df.withColumn("year", year(col("reviewTime_unix")))
df = df.withColumn("month", month(col("reviewTime_unix")))

print(f"✓ Datos cargados: {df.count()} reseñas")

# 1. ESTADÍSTICAS DESCRIPTIVAS GLOBALES
print("1️⃣ Calculando estadísticas descriptivas globales...")
global_stats = df.agg(
    spark_round(avg("overall"), 4).alias("mean_rating"),
    spark_round(stddev("overall"), 4).alias("std_rating"),
    spark_round(variance("overall"), 4).alias("variance_rating"),
    spark_min("overall").alias("min_rating"),
    spark_max("overall").alias("max_rating"),
    count("overall").alias("total_reviews"),
    countDistinct("asin").alias("unique_products"),
    countDistinct("reviewerID").alias("unique_reviewers")
)
save_result(global_stats, "global_statistics")

# 2. DISTRIBUCIÓN DE RATINGS
print("2️⃣ Analizando distribución de ratings...")
rating_dist = df.groupBy("overall") \
    .agg(count("*").alias("count")) \
    .withColumn("percentage", spark_round((col("count") / df.count()) * 100, 2)) \
    .orderBy("overall")
save_result(rating_dist, "rating_distribution")

# 3. ANÁLISIS TEMPORAL - POR AÑO
print("3️⃣ Análisis temporal por año...")
yearly = df.groupBy("year") \
    .agg(
        count("*").alias("review_count"),
        spark_round(avg("overall"), 2).alias("avg_rating")
    ) \
    .filter(col("year").isNotNull()) \
    .orderBy("year")
save_result(yearly, "yearly_activity")

# 4. ANÁLISIS TEMPORAL - POR MES
print("4️⃣ Análisis temporal por mes...")
monthly = df.groupBy("month") \
    .agg(
        count("*").alias("review_count"),
        spark_round(avg("overall"), 2).alias("avg_rating")
    ) \
    .filter(col("month").isNotNull()) \
    .orderBy("month")
save_result(monthly, "monthly_activity")

# 5. TOP JUEGOS MÁS RESEÑADOS
print("5️⃣ Top 1000 juegos más reseñados...")
top_reviewed = df.groupBy("asin") \
    .agg(
        count("*").alias("review_count"),
        spark_round(avg("overall"), 2).alias("avg_rating")
    ) \
    .orderBy(desc("review_count")) \
    .limit(1000)
save_result(top_reviewed, "top_reviewed_games")

# 6. TOP JUEGOS MEJOR VALORADOS (mínimo 10 reseñas)
print("6️⃣ Top 1000 juegos mejor valorados...")
top_rated = df.groupBy("asin") \
    .agg(
        count("*").alias("review_count"),
        spark_round(avg("overall"), 2).alias("avg_rating")
    ) \
    .filter(col("review_count") >= 10) \
    .orderBy(desc("avg_rating"), desc("review_count")) \
    .limit(1000)
save_result(top_rated, "top_rated_games")

# 7. PEOR VALORADOS (mínimo 10 reseñas)
print("7️⃣ Top 1000 juegos peor valorados...")
worst_rated = df.groupBy("asin") \
    .agg(
        count("*").alias("review_count"),
        spark_round(avg("overall"), 2).alias("avg_rating")
    ) \
    .filter(col("review_count") >= 10) \
    .orderBy(asc("avg_rating"), desc("review_count")) \
    .limit(1000)
save_result(worst_rated, "worst_rated_games")

# 8. ANÁLISIS POR LONGITUD DE TEXTO
print("8️⃣ Correlación longitud de texto vs rating...")
length_analysis = df.filter(col("reviewText").isNotNull()) \
    .withColumn("text_length_bin", 
        when(col("reviewText_length") < 50, "Muy corta (<50)")
        .when(col("reviewText_length") < 200, "Corta (50-200)")
        .when(col("reviewText_length") < 500, "Media (200-500)")
        .otherwise("Larga (>500)")
    ) \
    .groupBy("text_length_bin") \
    .agg(
        count("*").alias("review_count"),
        spark_round(avg("overall"), 2).alias("avg_rating"),
        spark_round(avg("reviewText_length"), 0).alias("avg_length")
    ) \
    .orderBy("avg_rating")
save_result(length_analysis, "length_vs_rating")

# 9. ANÁLISIS DE PALABRAS FRECUENTES - POSITIVAS (rating >= 4)
print("9️⃣ Palabras más frecuentes en reseñas positivas...")
positive_reviews = df.filter((col("overall") >= 4) & col("reviewText").isNotNull())

# Limpiar y separar palabras
positive_words = positive_reviews.select(
    explode(
        split(
            regexp_replace(lower(col("reviewText")), "[^a-z\\s]", ""), 
            "\\s+"
        )
    ).alias("word")
) \
.filter(length(col("word")) > 3) \
.groupBy("word") \
.agg(count("*").alias("frequency")) \
.orderBy(desc("frequency")) \
.limit(100)

save_result(positive_words, "positive_words_frequency")

# 10. ANÁLISIS DE PALABRAS FRECUENTES - NEGATIVAS (rating <= 2)
print("🔟 Palabras más frecuentes en reseñas negativas...")
negative_reviews = df.filter((col("overall") <= 2) & col("reviewText").isNotNull())

negative_words = negative_reviews.select(
    explode(
        split(
            regexp_replace(lower(col("reviewText")), "[^a-z\\s]", ""), 
            "\\s+"
        )
    ).alias("word")
) \
.filter(length(col("word")) > 3) \
.groupBy("word") \
.agg(count("*").alias("frequency")) \
.orderBy(desc("frequency")) \
.limit(100)

save_result(negative_words, "negative_words_frequency")

# 11. DETECCIÓN DE OUTLIERS EN RATINGS
print("1️⃣1️⃣ Detección de outliers en ratings...")

# Calcular promedio por juego
game_avg = df.groupBy("asin") \
    .agg(avg("overall").alias("game_avg_rating"))

# Unir con reseñas originales
df_with_avg = df.join(game_avg, "asin")

# Identificar outliers (diferencia > 2 puntos del promedio del juego)
outliers = df_with_avg \
    .withColumn("diff_from_avg", 
        spark_round(col("overall") - col("game_avg_rating"), 2)
    ) \
    .filter((col("diff_from_avg") > 2) | (col("diff_from_avg") < -2)) \
    .select("asin", "overall", "game_avg_rating", "diff_from_avg", "reviewerID") \
    .orderBy(desc("diff_from_avg")) \
    .limit(1000)

save_result(outliers, "rating_outliers")

# 12. COMPARACIÓN: RESEÑAS VERIFICADAS VS NO VERIFICADAS
print("1️⃣2️⃣ Comparación: Reseñas verificadas vs no verificadas...")
verified_stats = df.groupBy("verified") \
    .agg(
        count("*").alias("review_count"),
        spark_round(avg("overall"), 2).alias("avg_rating"),
        spark_round(stddev("overall"), 2).alias("std_rating")
    )
save_result(verified_stats, "verified_statistics")

# 13. ANÁLISIS POR DÍA DE LA SEMANA
print("1️⃣3️⃣ Análisis por día de la semana...")
from pyspark.sql.functions import dayofweek

dow_analysis = df.withColumn("day_of_week", dayofweek("reviewTime_unix")) \
    .groupBy("day_of_week") \
    .agg(
        count("*").alias("review_count"),
        spark_round(avg("overall"), 2).alias("avg_rating")
    ) \
    .orderBy("day_of_week")
save_result(dow_analysis, "day_of_week_analysis")

# 14. ANÁLISIS DE VOTOS DE UTILIDAD (usando campo 'vote')
print("1️⃣4️⃣ Análisis de votos de utilidad...")
vote_analysis = df.filter(col("vote").isNotNull()) \
    .select(
        col("asin"),
        col("overall"),
        col("vote").cast("int").alias("vote_count")
    ) \
    .filter(col("vote_count") >= 5) \
    .orderBy(desc("vote_count")) \
    .limit(1000)
save_result(vote_analysis, "helpful_votes_analysis")

# 15. TOP REVIEWERS MÁS ACTIVOS
print("1️⃣5️⃣ Top 1000 reviewers más activos...")
top_reviewers = df.groupBy("reviewerID") \
    .agg(
        count("*").alias("review_count"),
        spark_round(avg("overall"), 2).alias("avg_rating_given")
    ) \
    .orderBy(desc("review_count")) \
    .limit(1000)
save_result(top_reviewers, "top_reviewers")

print("\n" + "="*60)
print("✅ Análisis completo finalizado!")
print(f"📁 15 archivos generados en /data/results/")
print("="*60)

spark.stop()
