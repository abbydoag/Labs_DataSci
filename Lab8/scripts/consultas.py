"""Conexion a DuckDB y ejecucion de los archivos de sql/.

Las consultas viven en sql/, un archivo por consulta, y los cuadernos las
corren por nombre. Asi la consulta documentada y la ejecutada son la misma.
"""

import time
from pathlib import Path

import duckdb
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DIR_SQL = RAIZ / "sql"
DIR_RAW = RAIZ / "data" / "raw"
VISTAS = "00_vistas.sql"


def conectar(base: str = ":memory:", vistas: bool = True) -> duckdb.DuckDBPyConnection:
    """Abre DuckDB con las rutas relativas resueltas desde la raiz del laboratorio.

    Con `base` por defecto la conexion vive en memoria y no guarda nada: las
    vistas leen los Parquet en cada consulta. `vistas=False` deja la conexion
    vacia, para consultar los archivos sin ninguna capa intermedia.
    """
    con = duckdb.connect(base)
    con.execute(f"set file_search_path = '{RAIZ}'")
    if vistas:
        con.execute(leer_sql(VISTAS))
    return con


def leer_sql(nombre: str) -> str:
    """Texto de un archivo de sql/."""
    return (DIR_SQL / nombre).read_text(encoding="utf-8")


def correr(con: duckdb.DuckDBPyConnection, nombre: str) -> pd.DataFrame:
    """Ejecuta un archivo de sql/ y devuelve el resultado como DataFrame."""
    return con.sql(leer_sql(nombre)).df()


def correr_medido(con: duckdb.DuckDBPyConnection, nombre: str) -> tuple[pd.DataFrame, float]:
    """Como `correr`, pero ademas devuelve los segundos que tardo."""
    inicio = time.perf_counter()
    resultado = correr(con, nombre)
    return resultado, time.perf_counter() - inicio
