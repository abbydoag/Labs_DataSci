"""Lectura de las escenas y construccion de las tablas de analisis.

Los seis cuadernos leen de aqui para no repetir el mismo codigo de carga ni
recalcular los indices en cada uno.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd
import rasterio

from . import indices as ix
from .config import DERIVADO, FECHAS, RESOLUCION_M, catalogo, ruta_tif

# Area de un pixel a 20 m, en kilometros cuadrados.
AREA_PIXEL_KM2 = RESOLUCION_M**2 / 1e6


def escenas_disponibles() -> list[tuple[str, str]]:
    """Escenas oficiales que si estan descargadas, en orden cronologico."""
    return [
        (lago, fecha)
        for lago, fechas in FECHAS.items()
        for fecha in fechas
        if ruta_tif(lago, fecha).exists()
    ]


def leer_cubo(lago: str, fecha: str) -> tuple[np.ndarray, dict]:
    """Lee el GeoTIFF de una escena y devuelve el arreglo y sus metadatos."""
    with rasterio.open(ruta_tif(lago, fecha)) as src:
        cubo = src.read()
        meta = {
            "transform": src.transform,
            "crs": src.crs,
            "bounds": src.bounds,
            "shape": (src.height, src.width),
            "descripciones": src.descriptions,
        }
    return cubo, meta


@lru_cache(maxsize=8)
def indices_escena(lago: str, fecha: str) -> tuple[dict[str, np.ndarray], dict]:
    """Indices completos de una escena. Se cachean las ultimas 8 consultadas."""
    cubo, meta = leer_cubo(lago, fecha)
    return ix.calcular(cubo), meta


def resumen_escena(lago: str, fecha: str) -> dict:
    """Estadisticas de una escena, restringidas al agua valida."""
    capas, meta = indices_escena(lago, fecha)

    agua = capas["agua"]
    agua_valida = capas["agua_valida"]
    chl = capas["chl_agua"]

    n_agua = int(agua.sum())
    n_valida = int(agua_valida.sum())
    valores = chl[agua_valida]

    fila = {
        "lago": lago,
        "fecha": pd.Timestamp(fecha),
        "pixeles_agua": n_agua,
        "pixeles_agua_validos": n_valida,
        "area_agua_km2": n_valida * AREA_PIXEL_KM2,
        # Que porcentaje del espejo de agua sobrevivio al filtro de nubes.
        "cobertura_valida_pct": 100 * n_valida / n_agua if n_agua else np.nan,
    }

    if n_valida == 0:
        fila.update(
            {
                k: np.nan
                for k in (
                    "chl_media",
                    "chl_mediana",
                    "chl_p90",
                    "chl_p99",
                    "chl_max",
                    "chl_std",
                    "pct_alto",
                    "pct_flotante",
                    "ndci_media",
                    "ndvi_media",
                    "ndwi_media",
                )
            }
        )
        return fila

    fila.update(
        {
            "chl_media": float(np.mean(valores)),
            "chl_mediana": float(np.median(valores)),
            "chl_p90": float(np.percentile(valores, 90)),
            "chl_p99": float(np.percentile(valores, 99)),
            "chl_max": float(np.max(valores)),
            "chl_std": float(np.std(valores)),
            # Extension de la floracion: fraccion del espejo de agua por encima
            # del nivel de alerta.
            "pct_alto": float(100 * np.mean(valores > ix.UMBRAL_ALTO_CHL)),
            "pct_flotante": float(100 * (capas["flotante"] & agua_valida).sum() / n_valida),
            "ndci_media": float(np.mean(capas["ndci"][agua_valida])),
            "ndvi_media": float(np.mean(capas["ndvi"][agua_valida])),
            "ndwi_media": float(np.mean(capas["ndwi"][agua_valida])),
        }
    )
    return fila


def tabla_resumen(recalcular: bool = False) -> pd.DataFrame:
    """Tabla con una fila por escena. Se guarda en data/derived/."""
    destino = DERIVADO / "resumen_escenas.csv"
    if destino.exists() and not recalcular:
        tabla = pd.read_csv(destino, parse_dates=["fecha"])
    else:
        filas = [resumen_escena(lago, fecha) for lago, fecha in escenas_disponibles()]
        if not filas:
            raise RuntimeError(
                "No hay escenas descargadas. Corre primero: .venv/bin/python -m src.descarga"
            )
        tabla = pd.DataFrame(filas)
        tabla.to_csv(destino, index=False)

    # Se anexan nubosidad y satelite que vienen del enunciado.
    meta = catalogo()[["lago", "fecha", "nubosidad_pct", "satelite", "cobertura_parcial_pct"]]
    tabla = tabla.merge(meta, on=["lago", "fecha"], how="left")
    return tabla.sort_values(["lago", "fecha"]).reset_index(drop=True)


def pila_chl(lago: str) -> tuple[np.ndarray, list[str], dict]:
    """Apila la clorofila de todas las fechas de un lago en un cubo 3D.

    Devuelve (pila, fechas, meta). La pila tiene forma (fecha, alto, ancho) y
    NaN donde no hay agua valida. Sirve para los mapas de persistencia y de
    diferencia entre fechas.
    """
    fechas = [f for f in FECHAS[lago] if ruta_tif(lago, f).exists()]
    if not fechas:
        raise RuntimeError(f"No hay escenas descargadas para {lago}")

    capas, meta = indices_escena(lago, fechas[0])
    forma = capas["chl_agua"].shape
    pila = np.full((len(fechas), *forma), np.nan, dtype=np.float32)

    for i, fecha in enumerate(fechas):
        capas_i, _ = indices_escena(lago, fecha)
        if capas_i["chl_agua"].shape != forma:
            raise RuntimeError(
                f"{lago} {fecha} tiene forma {capas_i['chl_agua'].shape}, "
                f"se esperaba {forma}. Las escenas deben compartir la rejilla."
            )
        pila[i] = capas_i["chl_agua"]

    return pila, fechas, meta


def muestra_pixeles(lago: str, fecha: str, n: int = 20000, semilla: int = 0) -> pd.DataFrame:
    """Muestra aleatoria de pixeles de agua con sus indices, para correlaciones.

    Se submuestrea porque un lago puede tener cientos de miles de pixeles y para
    estimar una correlacion no hacen falta todos.
    """
    capas, _ = indices_escena(lago, fecha)
    mascara = capas["agua_valida"]
    total = int(mascara.sum())
    if total == 0:
        return pd.DataFrame(columns=["lago", "fecha", "chl", "ndci", "ndvi", "ndwi", "fai"])

    datos = {
        "chl": capas["chl_agua"][mascara],
        "ndci": capas["ndci"][mascara],
        "ndvi": capas["ndvi"][mascara],
        "ndwi": capas["ndwi"][mascara],
        "fai": capas["fai"][mascara],
    }
    tabla = pd.DataFrame(datos)

    if total > n:
        tabla = tabla.sample(n=n, random_state=semilla)

    tabla.insert(0, "fecha", pd.Timestamp(fecha))
    tabla.insert(0, "lago", lago)
    return tabla.reset_index(drop=True)


def tabla_pixeles(recalcular: bool = False, n: int = 20000) -> pd.DataFrame:
    """Muestra de pixeles de todas las escenas, cacheada en disco."""
    destino = DERIVADO / "muestra_pixeles.csv"
    if destino.exists() and not recalcular:
        return pd.read_csv(destino, parse_dates=["fecha"])

    partes = [muestra_pixeles(lago, fecha, n=n) for lago, fecha in escenas_disponibles()]
    tabla = pd.concat(partes, ignore_index=True)
    tabla.to_csv(destino, index=False)
    return tabla


def distancia_orilla(agua: np.ndarray) -> np.ndarray:
    """Distancia de cada pixel al borde del espejo de agua, en metros.

    Las floraciones no se reparten de forma uniforme: se acumulan en bahias
    someras, en ensenadas resguardadas del viento y frente a las
    desembocaduras, todas ellas cerca de la orilla. Un pixel en el centro del
    lago y uno pegado a la costa son situaciones distintas aunque su firma
    espectral se parezca, y el modelo no tiene forma de distinguirlas si no se
    le dice.

    Se calcula con la transformada de distancia euclidiana sobre la mascara de
    agua, que devuelve para cada pixel de agua la distancia al pixel de tierra
    mas cercano. La mascara se rodea antes de un marco de tierra para que el
    agua que toca el borde del recorte no quede con una distancia inventada.
    """
    from scipy import ndimage

    con_marco = np.pad(agua, 1, mode="constant", constant_values=False)
    distancia = ndimage.distance_transform_edt(con_marco)[1:-1, 1:-1]
    return (distancia * RESOLUCION_M).astype(np.float32)


def construir_dataset_ml(recalcular: bool = False) -> pd.DataFrame:
    """Construye el dataset completo para ML.

    Cada fila es un pixel de agua valida dentro de alguno de los lagos.
    Columnas:
        - x, y: coordenadas en el sistema de referencia del raster (UTM 15N)
        - fila, columna: posicion del pixel dentro de la rejilla del raster
        - dist_orilla_m: distancia al borde del espejo de agua, en metros
        - lago: "Atitlan" o "Amatitlan"
        - fecha: fecha de adquisicion
        - B02, B03, B04, B05, B07, B08, B8A, B11, B12, B10: reflectancia
        - ndvi, ndwi, ndci, fai: indices espectrales
        - chl: clorofila-a en ug/L

    `fila` y `columna` se guardan porque el ejercicio 9 necesita devolver las
    predicciones a la rejilla del raster para dibujar el mapa de probabilidad,
    y reconstruirlas desde x e y obliga a invertir la transformacion afin.

    Se guardan en data/derived/dataset_ml.parquet.
    """
    destino = DERIVADO / "dataset_ml.parquet"
    if destino.exists() and not recalcular:
        return pd.read_parquet(destino)

    partes = []
    for lago, fecha in escenas_disponibles():
        cubo, meta = leer_cubo(lago, fecha)
        capas = ix.calcular(cubo)

        mascara = capas["agua_valida"]
        if not mascara.any():
            continue

        rows, cols = np.where(mascara)
        xs, ys = rasterio.transform.xy(meta["transform"], rows, cols)

        b = ix.reflectancia(cubo)

        datos_pixel = {
            "x": np.array(xs, dtype=np.float64),
            "y": np.array(ys, dtype=np.float64),
            "fila": rows.astype(np.int32),
            "columna": cols.astype(np.int32),
            "dist_orilla_m": distancia_orilla(capas["agua"])[mascara],
            "lago": lago,
            "fecha": pd.Timestamp(fecha),
        }

        for nombre_banda in ["B02", "B03", "B04", "B05", "B07", "B08", "B8A", "B11", "B12", "B10"]:
            datos_pixel[nombre_banda] = b[nombre_banda][mascara]

        datos_pixel["ndvi"] = capas["ndvi"][mascara]
        datos_pixel["ndwi"] = capas["ndwi"][mascara]
        datos_pixel["ndci"] = capas["ndci"][mascara]
        datos_pixel["fai"] = capas["fai"][mascara]
        datos_pixel["chl"] = capas["chl_agua"][mascara]

        partes.append(pd.DataFrame(datos_pixel))

    if not partes:
        raise RuntimeError("No hay escenas con pixeles de agua valida")

    tabla = pd.concat(partes, ignore_index=True)
    destino.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_parquet(destino, index=False)
    return tabla
