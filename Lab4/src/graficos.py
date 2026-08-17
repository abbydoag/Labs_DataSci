"""Utilidades de visualizacion compartidas por los cuadernos.

Concentra la rampa de color oficial del script CyanoLakes, el realce en color
verdadero y la reproyeccion a coordenadas geograficas que necesita folium.
"""

from __future__ import annotations

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.cm import ScalarMappable
from rasterio.crs import CRS
from rasterio.warp import Resampling, calculate_default_transform, reproject, transform_bounds

from . import indices as ix
from .config import NOMBRE_LARGO

WGS84 = CRS.from_epsg(4326)

# Etiquetas que se muestran en la barra de color. Poner las 27 fronteras de la
# rampa la volveria ilegible, asi que se rotulan los cortes con sentido
# ecologico: oligotrofico, mesotrofico, eutrofico y los niveles de alerta.
ETIQUETAS_CHL = [0.5, 2.5, 5, 10, 20, 30, 50, 100, 250, 500]


def color_verdadero(capas: dict[str, np.ndarray], ganancia: float = 3.0) -> np.ndarray:
    """Composicion en color verdadero, con la misma ganancia del script."""
    # matplotlib rechaza NaN en una imagen RGB, asi que los pixeles de relleno
    # se llevan a negro.
    return np.nan_to_num(np.clip(capas["rgb"] * ganancia, 0, 1), nan=0.0)


def color_verdadero_realzado(capas: dict[str, np.ndarray]) -> np.ndarray:
    """Color verdadero con estiramiento por percentiles, mas legible en pantalla."""
    rgb = capas["rgb"]
    salida = np.zeros_like(rgb)
    for i in range(3):
        banda = rgb[:, :, i]
        finitos = banda[np.isfinite(banda) & (banda > 0)]
        if finitos.size == 0:
            continue
        lo, hi = np.percentile(finitos, (2, 98))
        if hi > lo:
            salida[:, :, i] = np.clip((banda - lo) / (hi - lo), 0, 1)
    return np.nan_to_num(salida, nan=0.0)


def dibujar_mapa_chl(
    ax: plt.Axes,
    capas: dict[str, np.ndarray],
    titulo: str = "",
    fondo: bool = True,
    marcar_flotante: bool = True,
) -> None:
    """Pinta la clorofila sobre el color verdadero, con la rampa oficial.

    Fuera del agua se ve la imagen real del satelite; dentro del agua se ve el
    indice. Es la misma logica del script original, que devuelve color verdadero
    cuando el pixel no es agua.
    """
    cmap, norm = ix.rampa_cyanolakes()

    if fondo:
        ax.imshow(color_verdadero_realzado(capas))

    ax.imshow(np.ma.masked_invalid(capas["chl_agua"]), cmap=cmap, norm=norm, interpolation="nearest")

    if marcar_flotante:
        flotante = capas["flotante"] & capas["agua_valida"]
        if flotante.any():
            capa = np.zeros((*flotante.shape, 4), dtype=np.float32)
            capa[flotante] = (*ix.COLOR_FLOTANTE, 1.0)
            ax.imshow(capa, interpolation="nearest")

    ax.set_title(titulo)
    ax.set_xticks([])
    ax.set_yticks([])


def barra_color_chl(fig, ejes, orientacion: str = "vertical", etiqueta: str | None = None):
    """Barra de color de la rampa CyanoLakes, con espaciado uniforme.

    Las fronteras de la rampa van de 0.5 a 500 y no son uniformes; se dibujan
    con ancho igual para que los tramos bajos no desaparezcan.
    """
    cmap, norm = ix.rampa_cyanolakes()
    barra = fig.colorbar(
        ScalarMappable(norm=norm, cmap=cmap),
        ax=ejes,
        orientation=orientacion,
        spacing="uniform",
        ticks=ETIQUETAS_CHL,
        fraction=0.046,
        pad=0.04,
    )
    barra.set_label(etiqueta or "Clorofila-a (µg/L)")
    barra.ax.tick_params(labelsize=8)
    return barra


def titulo_escena(lago: str, fecha: str, extra: str = "") -> str:
    base = f"{NOMBRE_LARGO[lago]} — {fecha}"
    return f"{base}\n{extra}" if extra else base


# --- Reproyeccion para folium ---------------------------------------------


def reproyectar_wgs84(arreglo: np.ndarray, meta: dict) -> tuple[np.ndarray, list[list[float]]]:
    """Lleva un arreglo de la rejilla UTM a coordenadas geograficas.

    folium dibuja sobre un mapa en latitud/longitud, asi que la imagen se tiene
    que reproyectar antes de superponerla; si no, queda corrida respecto al mapa
    base. Devuelve el arreglo reproyectado y los limites [[sur, oeste],
    [norte, este]] que espera ImageOverlay.
    """
    alto, ancho = arreglo.shape
    origen = meta["crs"]
    limites = meta["bounds"]

    transformacion, ancho_d, alto_d = calculate_default_transform(
        origen, WGS84, ancho, alto, *limites
    )
    destino = np.full((alto_d, ancho_d), np.nan, dtype=np.float32)

    reproject(
        source=arreglo.astype(np.float32),
        destination=destino,
        src_transform=meta["transform"],
        src_crs=origen,
        dst_transform=transformacion,
        dst_crs=WGS84,
        src_nodata=np.nan,
        dst_nodata=np.nan,
        resampling=Resampling.nearest,
    )

    oeste, sur, este, norte = transform_bounds(origen, WGS84, *limites)
    return destino, [[sur, oeste], [norte, este]]


def rgba_chl(chl: np.ndarray) -> np.ndarray:
    """Convierte clorofila en una imagen RGBA uint8 con la rampa oficial.

    Los pixeles sin agua valida quedan transparentes para que se vea el mapa
    base de folium por debajo.
    """
    cmap, norm = ix.rampa_cyanolakes()
    enmascarado = np.ma.masked_invalid(chl)
    rgba = cmap(norm(enmascarado))
    rgba[..., 3] = np.where(np.isfinite(chl), 1.0, 0.0)
    return (rgba * 255).astype(np.uint8)


def centro(meta: dict) -> list[float]:
    """Centro del area en latitud/longitud, para inicializar el mapa folium."""
    oeste, sur, este, norte = transform_bounds(meta["crs"], WGS84, *meta["bounds"])
    return [(sur + norte) / 2, (oeste + este) / 2]
