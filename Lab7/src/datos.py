"""Carga, armonizacion y filtrado de las bases de Personas de la ENEIC.

Cada Excel se lee con pandas por separado, solo con las columnas necesarias y
todo como texto. Despues se pasa a Spark con un esquema explicito y desde ahi
todo el trabajo se hace en Spark. Se puede reconstruir con:

    .venv/bin/python -m src.datos
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pandas as pd
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

from src import config

TIPOS_NUMERICOS = {
    "salario_mensual": "double",
    "edad": "double",
    "antiguedad_anios": "double",
    "antiguedad_meses": "double",
    "horas_semanales": "double",
    "ocupado": "int",
    "NUM_HOGAR": "bigint",
    "NUM_PERSONA": "bigint",
    "FACTOR": "double",
    "ANIO": "int",
    "TRIMESTRE": "int",
}


def iniciar_spark() -> SparkSession:
    """Sesion local de Spark con registros de error solamente."""
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    log4j = Path(__file__).resolve().parent / "log4j2.properties"
    spark = (
        SparkSession.builder.appName("ENEIC_Lab7")
        .master("local[*]")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.extraJavaOptions", f"-Dlog4j.configurationFile={log4j.as_uri()}")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.driver.memory", "4g")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.sql.session.timeZone", "UTC")
        # Arrow en Spark 3.5 con Java 21 reporta fugas de memoria al pasar a pandas
        .config("spark.sql.execution.arrow.pyspark.enabled", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def normalizar_codigo(valor):
    """Deja un codigo como texto limpio: 1, 1.0 y ' 1 ' pasan a '1'."""
    if valor is None or pd.isna(valor):
        return None
    texto = str(valor).strip()
    if texto in ("", ".", "nan", "NaN", "None"):
        return None
    if re.fullmatch(r"-?\d+\.0+", texto):
        texto = texto.split(".")[0]
    return texto


def leer_excel(meta: dict) -> pd.DataFrame:
    """Lee un archivo de Personas con las columnas requeridas, todo como texto."""
    ruta = config.RAIZ / meta["archivo"]
    pdf = pd.read_excel(ruta, dtype=str, engine="openpyxl",
                        usecols=lambda c: str(c).strip() in config.COLUMNAS)
    pdf.columns = [str(c).strip() for c in pdf.columns]
    faltan = set(config.COLUMNAS) - set(pdf.columns)
    if faltan:
        raise ValueError(f"{meta['archivo']} no trae las columnas {sorted(faltan)}")
    pdf = pdf.rename(columns=config.COLUMNAS)[list(config.COLUMNAS.values())]
    for col in pdf.columns:
        pdf[col] = pdf[col].map(normalizar_codigo).astype(object)
    return pdf


def a_spark(spark: SparkSession, pdf: pd.DataFrame, meta: dict) -> DataFrame:
    """Pasa el archivo a Spark con tipos explicitos y columnas de procedencia."""
    esquema = T.StructType([T.StructField(c, T.StringType(), True) for c in pdf.columns])
    df = spark.createDataFrame(pdf.where(pdf.notna(), None), schema=esquema)
    for col, tipo in TIPOS_NUMERICOS.items():
        df = df.withColumn(col, F.expr(f"try_cast(`{col}` as {tipo})"))
    return (df
            .withColumn("periodo_archivo", F.lit(meta["periodo"]))
            .withColumn("anio_archivo", F.lit(meta["anio"]).cast("int"))
            .withColumn("trimestre_calendario", F.lit(meta["trimestre"]).cast("int"))
            .withColumn("archivo_origen", F.lit(meta["archivo"])))


def es_finito(col: str):
    """Condicion de valor numerico presente, no NaN y no infinito."""
    c = F.col(col)
    return c.isNotNull() & ~F.isnan(c) & (F.abs(c) < float("inf"))


def armonizar_categoricas(df: DataFrame) -> DataFrame:
    """Codigos fuera del diccionario o ausentes pasan a DESCONOCIDO."""
    for col in config.CATEGORICAS:
        validos = list(config.ETIQUETAS[col])
        df = df.withColumn(
            col,
            F.when(F.col(col).isin(validos), F.col(col)).otherwise(F.lit(config.DESCONOCIDO)),
        )
    return df


def agregar_antiguedad(df: DataFrame) -> DataFrame:
    """Antiguedad en anios = anios + meses / 12."""
    return df.withColumn(
        "antiguedad", F.col("antiguedad_anios") + F.col("antiguedad_meses") / F.lit(12.0)
    )


# Pasos de filtrado, siempre en este orden: primero la poblacion de interes y
# el objetivo, despues la calidad de las variables numericas.
PASOS = [
    ("edad finita y >= 15", lambda: es_finito("edad") & (F.col("edad") >= 15)),
    ("ocupado = 1", lambda: F.col("ocupado") == 1),
    ("asalariado (P05C16 1-4)", lambda: F.col("categoria_ocupacional").isin("1", "2", "3", "4")),
    ("salario finito y > 0", lambda: es_finito("salario_mensual") & (F.col("salario_mensual") > 0)),
    ("antiguedad en anios >= 0", lambda: es_finito("antiguedad_anios") & (F.col("antiguedad_anios") >= 0)),
    ("meses entero entre 0 y 11", lambda: es_finito("antiguedad_meses")
        & (F.col("antiguedad_meses") == F.floor("antiguedad_meses"))
        & F.col("antiguedad_meses").between(0, 11)),
    ("antiguedad <= edad", lambda: F.col("antiguedad") <= F.col("edad")),
    ("horas en (0, 168]", lambda: es_finito("horas_semanales")
        & (F.col("horas_semanales") > 0) & (F.col("horas_semanales") <= 168)),
]


def filtrar(df: DataFrame, etiqueta: str) -> tuple[DataFrame, list[dict]]:
    """Aplica los pasos en orden y cuenta los registros excluidos en cada uno.

    Una condicion que no se puede evaluar (valor nulo) cuenta como excluida.
    """
    filas = [{"conjunto": etiqueta, "paso": "inicio", "restantes": df.count(), "excluidos": 0}]
    for nombre, condicion in PASOS:
        df = df.filter(F.coalesce(condicion(), F.lit(False)))
        restantes = df.count()
        filas.append({"conjunto": etiqueta, "paso": nombre, "restantes": restantes,
                      "excluidos": filas[-1]["restantes"] - restantes})
    return df, filas


def preparar_archivo(spark: SparkSession, meta: dict) -> tuple[DataFrame, list[dict]]:
    """Lee, tipifica, armoniza y filtra un archivo de Personas."""
    df = a_spark(spark, leer_excel(meta), meta)
    df = agregar_antiguedad(df)
    df, filas = filtrar(df, meta["periodo"])
    df = armonizar_categoricas(df)
    return df.cache(), filas


def guardar_parquet(df: DataFrame, ruta) -> None:
    """Escribe un solo archivo parquet y quita los .crc que deja Spark."""
    df.coalesce(1).write.mode("overwrite").parquet(str(ruta))
    for extra in ruta.glob(".*.crc"):
        extra.unlink()
    exito = ruta / "_SUCCESS"
    if exito.exists():
        exito.unlink()


def construir(spark: SparkSession) -> pd.DataFrame:
    """Prepara 2025 (union de los cuatro archivos) y 2026 y los guarda en parquet."""
    config.preparar_directorios()
    partes_2025, resumen = [], []
    for meta in config.ARCHIVOS:
        df, filas = preparar_archivo(spark, meta)
        resumen += filas
        if meta["anio"] == 2025:
            partes_2025.append(df)
        else:
            guardar_parquet(df, config.PARQUET_2026)
    df_2025 = partes_2025[0]
    for parte in partes_2025[1:]:
        df_2025 = df_2025.unionByName(parte)
    guardar_parquet(df_2025, config.PARQUET_2025)
    resumen = pd.DataFrame(resumen)
    resumen.to_csv(config.RESUMEN_FILTROS, index=False)
    return resumen


def cargar(spark: SparkSession, anio: int = 2025) -> DataFrame:
    """Lee el conjunto preparado de 2025 o de 2026; lo construye si no existe."""
    ruta = config.PARQUET_2025 if anio == 2025 else config.PARQUET_2026
    if not ruta.exists():
        construir(spark)
    return spark.read.parquet(str(ruta))


if __name__ == "__main__":
    sesion = iniciar_spark()
    print(construir(sesion).to_string(index=False))
    sesion.stop()
