"""Rutas y constantes del laboratorio.

Las rutas se resuelven desde la ubicacion de este archivo, de modo que los
cuadernos corren igual sin importar cual sea el directorio de trabajo.
"""

from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "data"
PROCESADO = RAIZ / "processed"
FIGURAS = RAIZ / "figuras"

TRAIN = DATOS / "train.csv"
TEST = DATOS / "test.csv"
TRAIN_PROCESADO = PROCESADO / "train_preprocessed.csv"
TEST_PROCESADO = PROCESADO / "test_preprocessed.csv"

# La misma semilla que usa el ejercicio 6 en `Lab5.ipynb`, para que las
# particiones de este modulo sean comparables con las de aquel.
SEMILLA = 42

ETIQUETAS = {0: "No desastre", 1: "Desastre"}


def preparar_directorios() -> None:
    """Crea las carpetas de salida que los cuadernos escriben."""
    FIGURAS.mkdir(exist_ok=True)
    PROCESADO.mkdir(exist_ok=True)
