from fastapi import FastAPI
import pandas as pd
import os

app = FastAPI()

# Ruta donde Spark dejó los resultados procesados
RESULTS_PATH = "/data/results.csv"

@app.get("/")
def read_root():
    return {"message": "API de Análisis de Videojuegos Online"}

@app.get("/stats")
def get_stats():
    if os.path.exists(RESULTS_PATH):
        df = pd.read_csv(RESULTS_PATH)
        # Convertimos el DataFrame a JSON para enviarlo por la API
        return df.to_dict(orient="records")
    return {"error": "Los datos aún no han sido procesados por Spark"}