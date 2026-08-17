"""Indices espectrales del Laboratorio 4.

El nucleo de este modulo es la traduccion a Python del script oficial
"CyanoLakes Chlorophyll-a" (Jeremy Kravitz y Mark Matthews, 2020) publicado en
https://custom-scripts.sentinel-hub.com/custom-scripts/sentinel-2/cyanobacteria_chla_ndci_l1c/

El script original es JavaScript y corre dentro de Sentinel Hub sobre un pixel a
la vez. Aqui se reescribe de forma vectorizada sobre arreglos de numpy, sin
cambiar ninguna formula ni ningun umbral, para poder aplicarlo a las bandas que
se descargan con openEO y conservar el valor numerico del indice (el script
original solo devuelve un color).

Dos notas sobre la fidelidad de la traduccion:

1. El script publicado calcula dentro de `wbi` seis indices adicionales (wii,
   wri, puwi, uwi, usi) que nunca aparecen en ninguna condicion. Son codigo
   muerto y no se replican, porque no alteran el resultado.
2. El script se publico para L1C. Aqui se aplica sobre L2A, que es el producto
   que entrega la coleccion SENTINEL2_L2A de openEO y el que usa el cuaderno de
   ejemplo del curso. L2A ya viene corregido atmosfericamente, que es la entrada
   preferible para indices de calidad de agua.
"""

from __future__ import annotations

import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap

from .config import ESCALA_REFLECTANCIA, IDX_BANDA, SIN_DATO

# --- Umbrales del script original -----------------------------------------

MNDWI_THRESHOLD = 0.42
NDWI_THRESHOLD = 0.4
FILTER_UABS = True
FAI_THRESHOLD = 0.08

# --- Umbrales de control de calidad (no son del script) --------------------
# L1C no trae capa de clasificacion de escena, asi que la nube se descarta con
# dos pruebas sencillas sobre la propia reflectancia.

# Cirrus: B10 solo recibe luz dispersada por nube alta, porque el vapor de agua
# absorbe esa longitud de onda a nivel del suelo. Cualquier valor apreciable
# delata cirrus.
CIRRUS_THRESHOLD = 0.01

# Nube densa: brillante en el azul y en el verde a la vez.
BRILLO_THRESHOLD = 0.28

# Reflectancia minima en las dos bandas del NDCI para que el cociente signifique
# algo. Por debajo de esto se esta dividiendo ruido entre ruido.
REFLECTANCIA_MINIMA = 0.005


def _div(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Division elemento a elemento que devuelve 0 donde el denominador es 0."""
    return np.divide(a, b, out=np.zeros_like(a, dtype=np.float32), where=(b != 0))


def reflectancia(cubo: np.ndarray) -> dict[str, np.ndarray]:
    """Convierte el GeoTIFF crudo en un diccionario de bandas en reflectancia.

    Sentinel-2 entrega enteros escalados por 10000. El script de Sentinel Hub
    espera reflectancia en el rango 0-1, asi que se divide antes de aplicarlo.
    Los pixeles de relleno se marcan como NaN para que no contaminen ningun
    indice.
    """
    bandas = {}
    for nombre, i in IDX_BANDA.items():
        banda = cubo[i].astype(np.float32)
        banda[cubo[i] == SIN_DATO] = np.nan
        bandas[nombre] = banda / ESCALA_REFLECTANCIA
    return bandas


# --- Deteccion de cuerpo de agua (funcion wbi del script) ------------------


def mascara_agua(b: dict[str, np.ndarray]) -> np.ndarray:
    """Traduccion de la funcion `wbi` del script CyanoLakes.

    Combina seis criterios de agua y luego descarta zonas urbanas y suelo
    desnudo. Devuelve un booleano: True donde el pixel es superficie de agua.
    """
    r, g, azul = b["B04"], b["B03"], b["B02"]
    nir, swir1, swir2 = b["B08"], b["B11"], b["B12"]

    ndvi_v = _div(nir - r, nir + r)
    mndwi = _div(g - swir1, g + swir1)
    ndwi_v = _div(g - nir, g + nir)
    ndwi_leaves = _div(nir - swir1, nir + swir1)
    aweish = azul + 2.5 * g - 1.5 * (nir + swir1) - 0.25 * swir2
    aweinsh = 4 * (g - swir1) - (0.25 * nir + 2.75 * swir1)
    dbsi = _div(swir1 - g, swir1 + g) - ndvi_v

    agua = (
        (mndwi > MNDWI_THRESHOLD)
        | (ndwi_v > NDWI_THRESHOLD)
        | (aweinsh > 0.1879)
        | (aweish > 0.1112)
        | (ndvi_v < -0.2)
        | (ndwi_leaves > 1)
    )

    if FILTER_UABS:
        urbano_o_suelo = (aweinsh <= -0.03) | (dbsi > 0)
        agua = agua & ~urbano_o_suelo

    return agua


# --- Vegetacion flotante, clorofila e indices clasicos ---------------------


def fai(b: dict[str, np.ndarray]) -> np.ndarray:
    """Floating Algae Index. `FAI(B04, B07, B8A)` del script original.

    Linea base entre 665 nm y 865 nm evaluada en 783 nm. Valores altos delatan
    material flotante: natas de cianobacteria, lirio acuatico o basura.
    """
    a, bb, c = b["B04"], b["B07"], b["B8A"]
    return bb - a - (c - a) * (783 - 665) / (865 - 665)


def ndci(b: dict[str, np.ndarray]) -> np.ndarray:
    """Normalized Difference Chlorophyll Index: (B05 - B04) / (B05 + B04).

    Aprovecha que la clorofila-a absorbe en el rojo (665 nm, B04) y refleja en el
    borde rojo (705 nm, B05). Es el nucleo del indice de cianobacteria.

    Por definicion el NDCI vive en [-1, 1]. Se recorta a ese rango como red de
    seguridad: si alguna banda llegara con valor negativo o casi nulo el cociente
    podria salirse, y un valor fuera de rango no significa nada fisicamente.
    """
    return np.clip(_div(b["B05"] - b["B04"], b["B05"] + b["B04"]), -1.0, 1.0)


def clorofila(ndci_v: np.ndarray) -> np.ndarray:
    """Clorofila-a en microgramos por litro a partir del NDCI.

    Polinomio cubico calibrado con datos simulados, exactamente como aparece en
    el script: 826.57*NDCI^3 - 176.43*NDCI^2 + 19*NDCI + 4.071
    """
    return 826.57 * ndci_v**3 - 176.43 * ndci_v**2 + 19 * ndci_v + 4.071


def ndvi(b: dict[str, np.ndarray]) -> np.ndarray:
    """NDVI = (B08 - B04) / (B08 + B04)."""
    return _div(b["B08"] - b["B04"], b["B08"] + b["B04"])


def ndwi(b: dict[str, np.ndarray]) -> np.ndarray:
    """NDWI = (B03 - B08) / (B03 + B08)."""
    return _div(b["B03"] - b["B08"], b["B03"] + b["B08"])


def mascara_nubes(b: dict[str, np.ndarray]) -> np.ndarray:
    """True donde el pixel no parece nube.

    L1C no trae capa de clasificacion de escena, asi que se combinan dos pruebas:
    cirrus en B10 y brillo conjunto en el visible. La nube densa ademas casi
    nunca sobrevive a la mascara de agua, porque una nube no cumple ningun
    criterio de agua.
    """
    cirrus = b["B10"] > CIRRUS_THRESHOLD
    brillante = (b["B02"] > BRILLO_THRESHOLD) & (b["B03"] > BRILLO_THRESHOLD)
    return ~(cirrus | brillante)


def mascara_senal(b: dict[str, np.ndarray]) -> np.ndarray:
    """True donde las bandas del NDCI traen senal suficiente para ser creibles.

    Si el rojo y el borde rojo estan practicamente en cero, su cociente
    normalizado es ruido dividido entre ruido. Marcar esos pixeles como no
    validos es mas honesto que reportar un numero inventado.
    """
    return (b["B04"] > REFLECTANCIA_MINIMA) & (b["B05"] > REFLECTANCIA_MINIMA)


# --- Producto completo -----------------------------------------------------


def calcular(cubo: np.ndarray) -> dict[str, np.ndarray]:
    """Aplica todo el encadenamiento a un GeoTIFF ya leido.

    Devuelve las capas de interes. `chl_agua` es la clorofila restringida a los
    pixeles de agua validos, que es la capa que alimenta todos los analisis
    posteriores; fuera del agua queda como NaN.
    """
    b = reflectancia(cubo)

    # Los pixeles de relleno son NaN y cualquier comparacion contra NaN devuelve
    # False, que es justo lo que se quiere (no son agua, no son validos). Se
    # silencian los avisos que numpy emite al comparar con NaN.
    with np.errstate(invalid="ignore"):
        agua = mascara_agua(b)
        sin_nube = mascara_nubes(b)
        con_senal = mascara_senal(b)
        valido = sin_nube & con_senal

        fai_v = fai(b)
        ndci_v = ndci(b)
        chl = clorofila(ndci_v)

    # El script pinta la vegetacion flotante con un color propio antes de
    # evaluar la clorofila, porque una nata flotante satura el modelo.
    flotante = agua & (fai_v > FAI_THRESHOLD)

    # El polinomio cruza cero en NDCI = -0.0951 y por debajo devuelve valores
    # negativos, hasta -325 ug/L sobre el agua limpisima de Atitlan. Una
    # concentracion negativa no existe: ahi el modelo simplemente esta fuera de
    # su rango de calibracion y lo unico que se puede afirmar es que la
    # clorofila esta en el piso de deteccion. Se lleva a cero.
    #
    # El script original no necesita esta correccion porque solo pinta colores y
    # su rampa mete todo lo que baje de 0.5 en el mismo azul; el problema
    # aparece al promediar los valores, que es lo que si hace este laboratorio.
    chl = np.maximum(chl, 0.0)

    agua_valida = agua & valido
    chl_agua = np.where(agua_valida, chl, np.nan).astype(np.float32)

    return {
        "agua": agua,
        "sin_nube": sin_nube,
        "con_senal": con_senal,
        "valido": valido,
        "agua_valida": agua_valida,
        "flotante": flotante,
        "fai": fai_v,
        "ndci": ndci_v,
        "chl": chl.astype(np.float32),
        "chl_agua": chl_agua,
        "ndvi": ndvi(b),
        "ndwi": ndwi(b),
        "rgb": np.dstack([b["B04"], b["B03"], b["B02"]]),
    }


# --- Rampa de color oficial ------------------------------------------------
# Reproduce el mapa de color del script para que los mapas de este laboratorio
# se vean igual que en Copernicus Browser.

_RAMPA = [
    (0.5, (0, 0, 1.0)),
    (1, (0, 0, 1.0)),
    (2.5, (0, 59 / 255, 1)),
    (3.5, (0, 98 / 255, 1)),
    (5, (15 / 255, 113 / 255, 141 / 255)),
    (7, (14 / 255, 141 / 255, 120 / 255)),
    (8, (13 / 255, 141 / 255, 103 / 255)),
    (10, (30 / 255, 226 / 255, 28 / 255)),
    (14, (42 / 255, 226 / 255, 28 / 255)),
    (18, (68 / 255, 226 / 255, 28 / 255)),
    (20, (68 / 255, 226 / 255, 28 / 255)),
    (24, (134 / 255, 247 / 255, 0)),
    (28, (140 / 255, 247 / 255, 0)),
    (30, (205 / 255, 237 / 255, 0)),
    (38, (208 / 255, 240 / 255, 0)),
    (45, (208 / 255, 240 / 255, 0)),
    (50, (251 / 255, 210 / 255, 3 / 255)),
    (75, (248 / 255, 207 / 255, 2 / 255)),
    (90, (134 / 255, 247 / 255, 0)),
    (100, (245 / 255, 164 / 255, 9 / 255)),
    (150, (240 / 255, 159 / 255, 8 / 255)),
    (250, (237 / 255, 157 / 255, 7 / 255)),
    (300, (239 / 255, 118 / 255, 15 / 255)),
    (350, (239 / 255, 101 / 255, 15 / 255)),
    (450, (239 / 255, 100 / 255, 14 / 255)),
    (500, (233 / 255, 72 / 255, 21 / 255)),
]

# Color de la vegetacion flotante y del tope superior de la rampa.
COLOR_FLOTANTE = (233 / 255, 72 / 255, 21 / 255)

LIMITES_CHL = [0.0] + [u for u, _ in _RAMPA] + [1000.0]
_COLORES = [c for _, c in _RAMPA] + [COLOR_FLOTANTE]


def rampa_cyanolakes():
    """Devuelve (cmap, norm) con la escala de color exacta del script."""
    cmap = ListedColormap(_COLORES)
    cmap.set_bad((0, 0, 0, 0))  # fuera del agua: transparente
    norm = BoundaryNorm(LIMITES_CHL, cmap.N)
    return cmap, norm


# Umbral de "valor alto" para el analisis de extension de floracion.
#
# La OMS define dos niveles para aguas recreativas: vigilancia a partir de
# 10 ug/L de clorofila-a con dominancia de cianobacteria, y alerta a partir de
# 50 ug/L. Se toma el de 10 como umbral principal porque es el que discrimina
# en estos dos lagos: con 50 ug/L la superficie afectada da 0.00% en Atitlan y
# 0.15% en Amatitlan, y el analisis de extension se vuelve una tabla de ceros.
# Con 10 ug/L la diferencia entre lagos aparece con claridad (0.04% frente a
# 10.74% de la superficie).
UMBRAL_ALTO_CHL = 10.0
UMBRAL_ALERTA_CHL = 50.0

# Fronteras de estado trofico segun la OCDE, en ug/L de clorofila-a media.
# Sirven para traducir un numero a una categoria que un gestor ambiental
# reconoce.
ESTADO_TROFICO = [
    (2.6, "Oligotrófico", "agua limpia, poca productividad"),
    (7.3, "Mesotrófico", "productividad moderada"),
    (56.0, "Eutrófico", "floraciones frecuentes"),
    (float("inf"), "Hipereutrófico", "floración severa y persistente"),
]


def clasificar_trofico(valor: float) -> str:
    """Categoria trofica de una concentracion media de clorofila-a."""
    for corte, nombre, _ in ESTADO_TROFICO:
        if valor < corte:
            return nombre
    return ESTADO_TROFICO[-1][1]
