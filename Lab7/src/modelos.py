"""Piezas compartidas de los modelos supervisados y la segmentacion.

Las etapas de codificacion son las mismas para regresion lineal y Random
Forest; cada cuaderno solo cambia el modelo final del pipeline.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import OneHotEncoder, StringIndexer, VectorAssembler
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src import config

PERIODOS_TRAIN = ["2025T1", "2025T2", "2025T3"]
PERIODO_VALID = "2025T4"


def dividir(df: DataFrame) -> tuple[DataFrame, DataFrame]:
    """Train con 2025 T1 a T3 y validacion con 2025 T4, como indica el enunciado."""
    train = df.filter(F.col("periodo_archivo").isin(PERIODOS_TRAIN))
    valid = df.filter(F.col("periodo_archivo") == PERIODO_VALID)
    return train, valid


def etapas_codificacion() -> list:
    """StringIndexer y OneHotEncoder de las categoricas, y el VectorAssembler.

    handleInvalid="keep" en el indexador reserva el ultimo indice para
    categorias que no aparecieron en entrenamiento. El OneHotEncoder descarta
    esa ultima posicion (dropLast), asi que una categoria nueva queda como un
    vector de ceros y cada categoria observada tiene su propia columna.
    """
    indices = [f"{c}_idx" for c in config.CATEGORICAS]
    dummies = [f"{c}_ohe" for c in config.CATEGORICAS]
    indexador = StringIndexer(inputCols=config.CATEGORICAS, outputCols=indices,
                              handleInvalid="keep", stringOrderType="alphabetAsc")
    codificador = OneHotEncoder(inputCols=indices, outputCols=dummies, dropLast=True)
    ensamblador = VectorAssembler(inputCols=config.NUMERICAS + dummies, outputCol="features")
    return [indexador, codificador, ensamblador]


def pipeline_regresion(modelo) -> Pipeline:
    """Pipeline completo: codificacion de predictores y el modelo que se pase."""
    return Pipeline(stages=etapas_codificacion() + [modelo])


def metricas(pred: DataFrame, col_pred: str = "prediction") -> dict:
    """MAE, RMSE y R2 sobre todas las filas del DataFrame de predicciones."""
    resultado = {}
    for nombre in ["mae", "rmse", "r2"]:
        evaluador = RegressionEvaluator(labelCol=config.OBJETIVO, predictionCol=col_pred,
                                        metricName=nombre)
        resultado[nombre] = evaluador.evaluate(pred)
    return resultado


def ajustar_grilla(train: DataFrame, valid: DataFrame, configuraciones: list[dict],
                   construir_modelo) -> tuple[pd.DataFrame, dict]:
    """Ajusta un pipeline por configuracion con train y lo evalua en validacion.

    construir_modelo recibe el diccionario de parametros y devuelve el
    estimador final (LinearRegression, RandomForestRegressor, ...).
    """
    filas, ajustados = [], {}
    for i, params in enumerate(configuraciones):
        modelo = pipeline_regresion(construir_modelo(params)).fit(train)
        en_train = metricas(modelo.transform(train))
        en_valid = metricas(modelo.transform(valid))
        filas.append({"config": i, **params,
                      "rmse_train": en_train["rmse"],
                      "mae_valid": en_valid["mae"], "rmse_valid": en_valid["rmse"],
                      "r2_valid": en_valid["r2"]})
        ajustados[i] = modelo
    return pd.DataFrame(filas), ajustados


def guardar_modelo(modelo, ruta: Path) -> None:
    """Guarda un PipelineModel y quita los .crc y _SUCCESS que deja Spark."""
    modelo.write().overwrite().save(str(ruta))
    for extra in list(ruta.rglob(".*.crc")) + list(ruta.rglob("_SUCCESS")):
        extra.unlink()


def predecir_referencia(train: DataFrame, df: DataFrame) -> tuple[DataFrame, float]:
    """Modelo de referencia: predice para todos la media del salario de entrenamiento."""
    media = train.agg(F.mean(config.OBJETIVO)).first()[0]
    return df.withColumn("prediction", F.lit(float(media))), media


def nombres_features(modelo_pipeline) -> list[str]:
    """Nombre legible de cada posicion del vector de features ya ajustado."""
    indexador = modelo_pipeline.stages[0]
    nombres = list(config.NUMERICAS)
    for col, etiquetas in zip(config.CATEGORICAS, indexador.labelsArray):
        nombres += [f"{col}={e}" for e in etiquetas]
    return nombres
