"""Rutas, archivos y constantes del laboratorio.

Las rutas se resuelven desde la ubicacion de este archivo, de modo que los
cuadernos corren igual sin importar cual sea el directorio de trabajo.
"""

from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PROCESADO = RAIZ / "processed"
FIGURAS = RAIZ / "figuras"
MODELOS = RAIZ / "modelos"

PARQUET_2025 = PROCESADO / "eneic_2025.parquet"
PARQUET_2026 = PROCESADO / "eneic_2026.parquet"
RESUMEN_FILTROS = PROCESADO / "resumen_filtros.csv"

# Un registro por archivo de Personas. El periodo se asigna desde el archivo,
# no desde la columna TRIMESTRE, que trae valores que no son el trimestre
# calendario (2 a 6, y 175 registros con 2 dentro de II de 2025).
ARCHIVOS = [
    {"archivo": "Base-de-datos-Personas-ENEIC-I-2025.xlsx", "periodo": "2025T1", "anio": 2025, "trimestre": 1},
    {"archivo": "Base-de-datos-Personas-ENEIC-II-2025.xlsx", "periodo": "2025T2", "anio": 2025, "trimestre": 2},
    {"archivo": "Base-de-datos-Personas-ENEIC-III-2025.xlsx", "periodo": "2025T3", "anio": 2025, "trimestre": 3},
    {"archivo": "Base-de-datos-Personas-ENEIC-IV-2025.xlsx", "periodo": "2025T4", "anio": 2025, "trimestre": 4},
    {"archivo": "Base-de-datos-Personas-ENEIC-I-2026.xlsx", "periodo": "2026T1", "anio": 2026, "trimestre": 1},
]

# Nombre original en el archivo -> nombre analitico. Las columnas de
# auditoria conservan su nombre original, como pide el enunciado.
COLUMNAS = {
    "P05D01": "salario_mensual",
    "P02A03": "edad",
    "P05C07A": "antiguedad_anios",
    "P05C07B": "antiguedad_meses",
    "P05H01A": "horas_semanales",
    "P03A03A": "nivel_educativo",
    "P05C16": "categoria_ocupacional",
    "DOMINIO": "dominio",
    "OCUPADOS": "ocupado",
    "NUM_HOGAR": "NUM_HOGAR",
    "NUM_PERSONA": "NUM_PERSONA",
    "FACTOR": "FACTOR",
    "ANIO": "ANIO",
    "TRIMESTRE": "TRIMESTRE",
}

NUMERICAS = ["edad", "antiguedad", "horas_semanales"]
CATEGORICAS = ["nivel_educativo", "categoria_ocupacional", "dominio"]
OBJETIVO = "salario_mensual"
DESCONOCIDO = "DESCONOCIDO"

# Codigos validos segun el diccionario de la ENEIC. En educacion el 0 es
# "ninguno", no un faltante.
ETIQUETAS = {
    "nivel_educativo": {
        "0": "Ninguno",
        "1": "Preprimaria",
        "2": "Primaria",
        "3": "Basico",
        "4": "Diversificado",
        "5": "Superior",
        "6": "Maestria",
        "7": "Doctorado",
    },
    "categoria_ocupacional": {
        "1": "Gobierno",
        "2": "Empresa privada",
        "3": "Jornalero o peon",
        "4": "Servicio domestico",
    },
    "dominio": {
        "1": "Urbano metropolitano",
        "2": "Resto urbano",
        "3": "Rural nacional",
    },
}

SEMILLA = 42

COLORES = {
    "principal": "#1f6f8b",
    "modelo": "#c1272d",
    "gris": "#444444",
    "suave": "#9bbfd0",
    "clusters": ["#1f6f8b", "#c1272d", "#2e8b57", "#e0a100", "#6a4c93"],
}


def preparar_directorios() -> None:
    """Crea las carpetas de salida que los cuadernos escriben."""
    PROCESADO.mkdir(exist_ok=True)
    FIGURAS.mkdir(exist_ok=True)
    MODELOS.mkdir(exist_ok=True)
