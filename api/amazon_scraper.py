#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easyparser Product Name Fetcher
Obtiene los nombres de productos de Amazon usando Easyparser API
"""

import requests
import pandas as pd
import json
import os
from typing import List, Dict

# Configuración de Easyparser
EASYPARSER_API_KEY = 'API DE EASYPARSER'
EASYPARSER_ENDPOINT = 'https://realtime.easyparser.com/v1/request'


def get_product_name_from_easyparser(asin: str) -> Dict[str, str]:
    """
    Obtiene el nombre de un producto usando Easyparser API
    
    Args:
        asin: Amazon Standard Identification Number
        
    Returns:
        Diccionario con asin, product_name, url y status
    """
    try:
        print(f"🔍 Consultando Easyparser para ASIN: {asin}")
        
        response = requests.get(
            url=EASYPARSER_ENDPOINT,
            params={
                'api_key': EASYPARSER_API_KEY,
                'platform': 'AMZ',
                'operation': 'DETAIL',
                'domain': '.com',
                'asin': asin,
                'a_plus_content': 'false'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # La respuesta de Easyparser tiene la estructura: data.result.detail
            detail = data.get('result', {}).get('detail', {})
            
            if not detail:
                print(f"  ❌ No se encontraron detalles del producto")
                return {
                    'asin': asin,
                    'product_name': 'N/A - Detalles no encontrados',
                    'url': f"https://www.amazon.com/dp/{asin}",
                    'status': 'no_details'
                }
            
            # Obtener el título (con fallbacks)
            product_name = (
                detail.get('title') or 
                detail.get('title_excluding_variant_name') or 
                'N/A - Título no encontrado'
            )
            
            print(f"  ✅ Encontrado: {product_name[:60]}...")
            return {
                'asin': asin,
                'product_name': product_name,
                'url': f"https://www.amazon.com/dp/{asin}",
                'status': 'success'
            }
        else:
            print(f"  ❌ Error HTTP {response.status_code}")
            return {
                'asin': asin,
                'product_name': f'N/A - Error {response.status_code}',
                'url': f"https://www.amazon.com/dp/{asin}",
                'status': f'http_error_{response.status_code}'
            }
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Error de conexión: {str(e)}")
        return {
            'asin': asin,
            'product_name': 'N/A - Error de conexión',
            'url': f"https://www.amazon.com/dp/{asin}",
            'status': 'connection_error'
        }
    except Exception as e:
        print(f"  ❌ Error inesperado: {str(e)}")
        return {
            'asin': asin,
            'product_name': 'N/A - Error inesperado',
            'url': f"https://www.amazon.com/dp/{asin}",
            'status': 'unexpected_error'
        }


def fetch_multiple_products(asins: List[str]) -> List[Dict]:
    """
    Obtiene nombres de múltiples productos
    
    Args:
        asins: Lista de ASINs a consultar
        
    Returns:
        Lista de diccionarios con información de cada producto
    """
    results = []
    
    for i, asin in enumerate(asins, 1):
        print(f"\n[{i}/{len(asins)}]")
        result = get_product_name_from_easyparser(asin)
        results.append(result)
    
    return results


def load_top_asins_from_csv(csv_path: str, limit: int = 5) -> List[str]:
    """
    Carga los ASINs desde un archivo CSV generado por Spark
    
    Args:
        csv_path: Ruta al archivo CSV
        limit: Número máximo de ASINs a retornar
        
    Returns:
        Lista de ASINs
    """
    try:
        df = pd.read_csv(csv_path)
        asins = df['asin'].head(limit).tolist()
        return asins
    except Exception as e:
        print(f"❌ Error al leer CSV: {str(e)}")
        return []


def get_or_create_product_names(csv_path: str, cache_file: str, limit: int = 5) -> List[Dict]:
    """
    Obtiene nombres de productos desde caché o los genera si no existe
    
    Args:
        csv_path: Ruta al CSV con ASINs
        cache_file: Ruta al archivo JSON de caché
        limit: Número de productos a obtener
        
    Returns:
        Lista de diccionarios con información de productos
    """
    # Si existe el caché, usarlo
    if os.path.exists(cache_file):
        print(f"✅ Usando caché existente: {cache_file}")
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Si no existe, obtener de Easyparser y guardar
    print(f"📥 Caché no encontrado, obteniendo datos de Easyparser...")
    
    if not os.path.exists(csv_path):
        print(f"❌ Archivo CSV no encontrado: {csv_path}")
        return []
    
    asins = load_top_asins_from_csv(csv_path, limit=limit)
    
    if not asins:
        print("⚠️ No se pudieron cargar ASINs del CSV")
        return []
    
    results = fetch_multiple_products(asins)
    
    # Guardar caché
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Resultados guardados en caché: {cache_file}")
    
    return results
