"""Rutas y constantes del laboratorio.

Las rutas se resuelven desde la ubicacion de este archivo, de modo que los
cuadernos corren igual sin importar cual sea el directorio de trabajo.
"""

from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PROCESADO = RAIZ / "processed"
FIGURAS = RAIZ / "figuras"

VIDEOS = RAIZ / "youtube_videos.csv"
COMENTARIOS = RAIZ / "youtube_comments.csv"

VIDEOS_LIMPIOS = PROCESADO / "videos_limpios.csv"
COMENTARIOS_LIMPIOS = PROCESADO / "comentarios_limpios.csv"
NODOS = PROCESADO / "nodos_bipartita.csv"
ARISTAS = PROCESADO / "aristas_bipartita.csv"
ARISTAS_AUTORES = PROCESADO / "aristas_autor_autor.csv"
ARISTAS_VIDEOS = PROCESADO / "aristas_video_video.csv"

# Semilla unica del laboratorio. La usan los algoritmos con aleatoriedad
# (disposiciones de red y deteccion de comunidades) para que las figuras y las
# particiones se puedan reproducir tal cual.
SEMILLA = 42

# Fecha en la que se corrio la recoleccion, deducida del video mas reciente del
# conjunto. Los tiempos relativos ("hace 2 dias") solo tienen sentido anclados
# a esta fecha, y aun asi son aproximados.
RECOLECCION = "2026-09-02"

COLORES = {
    "autor": "#4c72b0",
    "video": "#c1272d",
    "acento": "#1f6f8b",
    "gris": "#444444",
    "positivo": "#2e8b57",
    "neutro": "#999999",
    "negativo": "#c1272d",
}


def preparar_directorios() -> None:
    """Crea las carpetas de salida que los cuadernos escriben."""
    PROCESADO.mkdir(exist_ok=True)
    FIGURAS.mkdir(exist_ok=True)
