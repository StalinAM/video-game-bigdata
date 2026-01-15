from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import os
import glob
import json
from typing import Optional

app = FastAPI(
    title="Video Game Reviews Analysis API",
    description="API para análisis de reseñas de videojuegos procesados con Spark",
    version="2.0.0"
)

# Configuración de CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta base donde Spark dejó los resultados procesados
RESULTS_BASE_PATH = "/data/results"

def load_csv(filename):
    """Carga un CSV y retorna como lista de diccionarios"""
    filepath = os.path.join(RESULTS_BASE_PATH, f"{filename}.csv")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Análisis '{filename}' no encontrado. Ejecuta el job de Spark primero.")
    df = pd.read_csv(filepath)
    return df.to_dict(orient="records")

def load_csv_as_dict(filename):
    """Carga un CSV y retorna el primer registro como dict"""
    filepath = os.path.join(RESULTS_BASE_PATH, f"{filename}.csv")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Análisis '{filename}' no encontrado.")
    df = pd.read_csv(filepath)
    return df.iloc[0].to_dict() if len(df) > 0 else {}

@app.get("/", tags=["General"])
def read_root():
    """Endpoint raíz con información de la API"""
    available_analyses = []
    if os.path.exists(RESULTS_BASE_PATH):
        csv_files = glob.glob(os.path.join(RESULTS_BASE_PATH, "*.csv"))
        available_analyses = [os.path.basename(f).replace(".csv", "") for f in csv_files]
    
    return {
        "message": "API de Análisis de Videojuegos - Versión Completa",
        "version": "2.0.0",
        "documentation": "/docs",
        "available_analyses": available_analyses,
        "total_endpoints": 17
    }

# =============================================================================
# ESTADÍSTICAS GLOBALES
# =============================================================================

@app.get("/statistics/global", tags=["Statistics"])
def get_global_statistics():
    """Estadísticas descriptivas globales (media, mediana, varianza, etc.)"""
    return load_csv_as_dict("global_statistics")

@app.get("/statistics/rating-distribution", tags=["Statistics"])
def get_rating_distribution():
    """Distribución de ratings (conteo y porcentaje por rating)"""
    return load_csv("rating_distribution")

@app.get("/statistics/verified", tags=["Statistics"])
def get_verified_statistics():
    """Estadísticas comparando reseñas verificadas vs no verificadas"""
    return load_csv("verified_statistics")

# =============================================================================
# ANÁLISIS TEMPORAL
# =============================================================================

@app.get("/temporal/yearly", tags=["Temporal Analysis"])
def get_yearly_activity():
    """Actividad de reseñas por año"""
    return load_csv("yearly_activity")

@app.get("/temporal/monthly", tags=["Temporal Analysis"])
def get_monthly_activity():
    """Actividad de reseñas por mes"""
    return load_csv("monthly_activity")

@app.get("/temporal/day-of-week", tags=["Temporal Analysis"])
def get_day_of_week_activity():
    """Actividad de reseñas por día de la semana"""
    return load_csv("day_of_week_analysis")

# =============================================================================
# ANÁLISIS POR JUEGO
# =============================================================================

@app.get("/games/top-reviewed", tags=["Game Analysis"])
def get_top_reviewed_games(limit: int = 100):
    """Top juegos con más reseñas"""
    data = load_csv("top_reviewed_games")
    return data[:limit]

@app.get("/games/top-rated", tags=["Game Analysis"])
def get_top_rated_games(limit: int = 100):
    """Top juegos mejor valorados (mínimo 10 reseñas)"""
    data = load_csv("top_rated_games")
    return data[:limit]

@app.get("/games/worst-rated", tags=["Game Analysis"])
def get_worst_rated_games(limit: int = 100):
    """Juegos peor valorados (mínimo 10 reseñas)"""
    data = load_csv("worst_rated_games")
    return data[:limit]

# =============================================================================
# ANÁLISIS POR PLATAFORMA
# =============================================================================

@app.get("/platforms/statistics", tags=["Platform Analysis"])
def get_platform_statistics():
    """Estadísticas por plataforma (rating promedio, conteo, cuartiles)"""
    try:
        return load_csv("platform_statistics")
    except HTTPException:
        # Si no existe el archivo, retornar mensaje informativo
        return {"message": "Análisis de plataformas no disponible en la versión actual"}

# =============================================================================
# ANÁLISIS DE TEXTO
# =============================================================================

@app.get("/text/length-vs-rating", tags=["Text Analysis"])
def get_length_vs_rating():
    """Relación entre longitud de reseña y rating"""
    return load_csv("length_vs_rating")

@app.get("/text/positive-words", tags=["Text Analysis"])
def get_positive_words(limit: int = 100):
    """Palabras más frecuentes en reseñas positivas"""
    data = load_csv("positive_words_frequency")
    return data[:limit]

@app.get("/text/negative-words", tags=["Text Analysis"])
def get_negative_words(limit: int = 100):
    """Palabras más frecuentes en reseñas negativas"""
    data = load_csv("negative_words_frequency")
    return data[:limit]

@app.get("/text/helpful-votes", tags=["Text Analysis"])
def get_helpful_votes(limit: int = 100):
    """Reseñas con más votos de utilidad"""
    data = load_csv("helpful_votes_analysis")
    return data[:limit]

# =============================================================================
# ANÁLISIS DE USUARIOS
# =============================================================================

@app.get("/users/top-reviewers", tags=["User Analysis"])
def get_top_reviewers(limit: int = 100):
    """Top reviewers más activos"""
    data = load_csv("top_reviewers")
    return data[:limit]

# =============================================================================
# DETECCIÓN DE ANOMALÍAS
# =============================================================================

@app.get("/outliers/ratings", tags=["Outliers"])
def get_rating_outliers(limit: int = 100):
    """Reseñas con ratings muy alejados del promedio del juego"""
    data = load_csv("rating_outliers")
    return data[:limit]

# =============================================================================
# ENDPOINT LEGACY (Compatibilidad)
# =============================================================================

@app.get("/stats", tags=["Legacy"])
def get_stats_legacy():
    """[LEGACY] Endpoint antiguo - usa /games/top-reviewed en su lugar"""
    # Si existe el archivo legacy, usarlo
    if os.path.exists("/data/results.csv"):
        df = pd.read_csv("/data/results.csv")
        return df.to_dict(orient="records")
    # Si no, usar el nuevo análisis
    return get_top_reviewed_games(limit=1000)

# =============================================================================
# PRODUCTOS - NOMBRES DESDE EASYPARSER API
# =============================================================================

@app.get("/products/top-reviewed-names", tags=["Products"])
def get_top_reviewed_product_names(limit: int = 5):
    """
    Obtiene los nombres de los Top 5 productos más reseñados
    
    Solo consulta Easyparser API si el archivo JSON no existe.
    Si ya existe, devuelve el caché.
    
    Args:
        limit: Número de productos (default: 5)
    """
    from amazon_scraper import get_or_create_product_names
    
    csv_path = os.path.join(RESULTS_BASE_PATH, "top_reviewed_games.csv")
    cache_file = os.path.join(RESULTS_BASE_PATH, "top_reviewed_with_names.json")
    
    if not os.path.exists(csv_path):
        raise HTTPException(
            status_code=404, 
            detail="Archivo top_reviewed_games.csv no encontrado. Ejecuta el análisis de Spark primero."
        )
    
    results = get_or_create_product_names(csv_path, cache_file, limit=limit)
    
    if not results:
        raise HTTPException(
            status_code=500,
            detail="No se pudieron obtener los nombres de productos"
        )
    
    return {
        "total": len(results),
        "products": results,
        "cached": os.path.exists(cache_file),
        "note": "Los nombres se obtienen de Easyparser API solo si no existe el caché"
    }


@app.get("/products/top-rated-names", tags=["Products"])
def get_top_rated_product_names(limit: int = 5):
    """
    Obtiene los nombres de los Top 5 productos mejor valorados
    
    Solo consulta Easyparser API si el archivo JSON no existe.
    Si ya existe, devuelve el caché.
    
    Args:
        limit: Número de productos (default: 5)
    """
    from amazon_scraper import get_or_create_product_names
    
    csv_path = os.path.join(RESULTS_BASE_PATH, "top_rated_games.csv")
    cache_file = os.path.join(RESULTS_BASE_PATH, "top_rated_with_names.json")
    
    if not os.path.exists(csv_path):
        raise HTTPException(
            status_code=404,
            detail="Archivo top_rated_games.csv no encontrado. Ejecuta el análisis de Spark primero."
        )
    
    results = get_or_create_product_names(csv_path, cache_file, limit=limit)
    
    if not results:
        raise HTTPException(
            status_code=500,
            detail="No se pudieron obtener los nombres de productos"
        )
    
    return {
        "total": len(results),
        "products": results,
        "cached": os.path.exists(cache_file),
        "note": "Los nombres se obtienen de Easyparser API solo si no existe el caché"
    }


@app.get("/products/all-with-names", tags=["Products"])
def get_all_products_with_names():
    """
    Obtiene ambos: Top 5 más reseñados y Top 5 mejor valorados
    
    Solo consulta Easyparser API si los archivos JSON no existen.
    """
    from amazon_scraper import get_or_create_product_names
    
    # Top Reviewed
    top_reviewed_csv = os.path.join(RESULTS_BASE_PATH, "top_reviewed_games.csv")
    top_reviewed_cache = os.path.join(RESULTS_BASE_PATH, "top_reviewed_with_names.json")
    
    # Top Rated
    top_rated_csv = os.path.join(RESULTS_BASE_PATH, "top_rated_games.csv")
    top_rated_cache = os.path.join(RESULTS_BASE_PATH, "top_rated_with_names.json")
    
    top_reviewed = []
    top_rated = []
    
    if os.path.exists(top_reviewed_csv):
        top_reviewed = get_or_create_product_names(top_reviewed_csv, top_reviewed_cache, limit=5)
    
    if os.path.exists(top_rated_csv):
        top_rated = get_or_create_product_names(top_rated_csv, top_rated_cache, limit=5)
    
    return {
        "top_reviewed": {
            "total": len(top_reviewed),
            "products": top_reviewed,
            "cached": os.path.exists(top_reviewed_cache)
        },
        "top_rated": {
            "total": len(top_rated),
            "products": top_rated,
            "cached": os.path.exists(top_rated_cache)
        },
        "note": "Los nombres se obtienen de ScrapingBee API solo si no existe el caché"
    }
