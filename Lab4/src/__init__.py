"""Codigo compartido del Laboratorio 4: analisis de datos geoespaciales.

Modulos:
    config    areas de interes, fechas oficiales y rutas
    descarga  obtencion de las escenas Sentinel-2 con openEO
    indices   script CyanoLakes traducido a Python, NDVI y NDWI
    datos     lectura de escenas y tablas de analisis
    graficos  rampa de color oficial y ayudas de visualizacion
"""

from . import config, datos, graficos, indices

__all__ = ["config", "datos", "graficos", "indices"]
