"""Configuracion compartida del Laboratorio 4.

Areas de interes, fechas oficiales y rutas de trabajo. Todo el laboratorio lee
sus constantes desde aqui para que los seis cuadernos trabajen sobre la misma
base de imagenes.
"""

from pathlib import Path

import pandas as pd

# --- Rutas -----------------------------------------------------------------

BASE = Path(__file__).resolve().parents[1]
GEOJSON = BASE / "geojson"
DATOS = BASE / "data"
CRUDO = DATOS / "raw"
DERIVADO = DATOS / "derived"
FIGURAS = DATOS / "figuras"

for _carpeta in (CRUDO, DERIVADO, FIGURAS):
    _carpeta.mkdir(parents=True, exist_ok=True)

# --- Areas de interes ------------------------------------------------------
# Coordenadas tal como las entrega el enunciado del laboratorio. Coinciden con
# la envolvente de los geojson provistos en Lab4/geojson/.

LAGO_ATITLAN = {
    "west": -91.326256,
    "east": -91.07151,
    "south": 14.5948,
    "north": 14.750979,
}

LAGO_AMATITLAN = {
    "west": -90.638065,
    "east": -90.512924,
    "south": 14.412347,
    "north": 14.493799,
}

AREAS = {
    "Atitlan": LAGO_ATITLAN,
    "Amatitlan": LAGO_AMATITLAN,
}

# Nombre con tilde para titulos y textos dirigidos al lector final.
NOMBRE_LARGO = {
    "Atitlan": "Lago de Atitlán",
    "Amatitlan": "Lago de Amatitlán",
}

# --- Bandas ----------------------------------------------------------------
# El script CyanoLakes necesita B02, B03, B04, B05, B07, B08, B8A, B11 y B12.
# NDVI agrega B04/B08 y NDWI B03/B08, que ya estan incluidas. B10 es la banda de
# cirrus, existe solo en L1C, y se usa para descartar nube alta.

BANDAS = ["B02", "B03", "B04", "B05", "B07", "B08", "B8A", "B11", "B12", "B10"]

# Indice de cada banda dentro del GeoTIFF descargado (base 0).
IDX_BANDA = {nombre: i for i, nombre in enumerate(BANDAS)}

# Sentinel-2 entrega reflectancia escalada por 10000 en entero de 16 bits.
ESCALA_REFLECTANCIA = 10000.0

# Valor de relleno que openEO escribe donde no hay dato.
SIN_DATO = -32768

# Resolucion de trabajo en metros. B05, B07, B8A, B11 y B12 son nativas de 20 m
# y son justo las que alimentan el indice de cianobacteria, asi que bajar a 10 m
# no agregaria informacion real y cuadruplicaria el peso de la descarga.
RESOLUCION_M = 20

# Se usa L1C y no L2A. El script CyanoLakes se publico para L1C —lo dice su
# propio nombre, `cyanobacteria_chla_ndci_l1c`— y su polinomio de clorofila esta
# calibrado sobre reflectancia de tope de atmosfera.
#
# La diferencia no es cosmetica. Se probo primero con L2A y el indice se rompe
# sobre agua muy clara: en Atitlan la mediana de reflectancia en el rojo (B04)
# quedaba en 0.0001 y la del borde rojo (B05) en valores negativos, porque la
# correccion atmosferica sobrecorrige donde el agua casi no refleja. El NDCI
# divide esas dos cantidades, asi que el denominador caia a cero y el indice se
# disparaba fuera de su rango teorico [-1, 1]. En L1C la reflectancia incluye la
# dispersion atmosferica, se mantiene holgadamente positiva y el cociente vuelve
# a tener sentido. El detalle esta documentado en 02_Indices.ipynb.
COLECCION = "SENTINEL2_L1C"
URL_OPENEO = "https://openeo.dataspace.copernicus.eu"

# --- Fechas oficiales ------------------------------------------------------
# Transcritas del enunciado. Se usan exclusivamente estas fechas para que todos
# los grupos trabajen sobre la misma base de imagenes.

_FECHAS_ATITLAN = [
    ("2025-01-18", 0.02, "Sentinel-2B"),
    ("2025-04-13", 0.54, "Sentinel-2C"),
    ("2025-05-13", 4.37, "Sentinel-2C"),
    ("2025-07-17", 3.57, "Sentinel-2A"),
    ("2025-11-21", 3.15, "Sentinel-2A"),
    ("2025-12-29", 3.17, "Sentinel-2C"),
    ("2026-02-12", 0.04, "Sentinel-2B"),
    ("2026-03-24", 3.17, "Sentinel-2B"),
    ("2026-04-13", 0.01, "Sentinel-2B"),
    ("2026-04-28", 4.96, "Sentinel-2C"),
    ("2026-07-22", 4.02, "Sentinel-2B"),
]

_FECHAS_AMATITLAN = [
    ("2025-01-28", 0.06, "Sentinel-2B"),
    ("2025-04-15", 0.09, "Sentinel-2A"),
    ("2025-04-28", 1.03, "Sentinel-2B"),
    ("2025-11-24", 0.50, "Sentinel-2B"),
    ("2026-01-08", 0.77, "Sentinel-2C"),
    ("2026-02-02", 0.39, "Sentinel-2B"),
    ("2026-02-07", 0.02, "Sentinel-2C"),
    ("2026-03-29", 0.01, "Sentinel-2C"),
    ("2026-04-13", 0.09, "Sentinel-2B"),
    ("2026-04-28", 4.96, "Sentinel-2C"),
    ("2026-06-19", 13.00, "Sentinel-2A"),
]

FECHAS = {
    "Atitlan": [f for f, _, _ in _FECHAS_ATITLAN],
    "Amatitlan": [f for f, _, _ in _FECHAS_AMATITLAN],
}

# El enunciado advierte que esta escena de Amatitlan cubre solo ~57.1% del area.
COBERTURA_PARCIAL = {("Amatitlan", "2026-02-07"): 57.1}


def catalogo() -> pd.DataFrame:
    """Tabla con las 22 escenas oficiales y sus metadatos."""
    filas = []
    for lago, entradas in (("Atitlan", _FECHAS_ATITLAN), ("Amatitlan", _FECHAS_AMATITLAN)):
        for fecha, nubosidad, satelite in entradas:
            filas.append(
                {
                    "lago": lago,
                    "fecha": pd.Timestamp(fecha),
                    "nubosidad_pct": nubosidad,
                    "satelite": satelite,
                    "cobertura_parcial_pct": COBERTURA_PARCIAL.get((lago, fecha)),
                }
            )
    return pd.DataFrame(filas).sort_values(["lago", "fecha"]).reset_index(drop=True)


def ruta_tif(lago: str, fecha: str) -> Path:
    """Ruta del GeoTIFF de una escena."""
    return CRUDO / lago / f"{lago}_{fecha}.tif"
