"""Clasificadores de desastre: el del ejercicio 6 y el del ejercicio 10.

`crear_pipeline` reproduce el montaje del ejercicio 6 sin tocar un solo
parametro. `crear_pipeline_mixto` es el mismo montaje con una rama numerica
adicional, que es lo unico que cambia el ejercicio 10. Manteniendo el
vectorizador, los hiperparametros y la semilla identicos, cualquier diferencia
de metrica entre los dos solo puede venir de la variable nueva.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import RepeatedStratifiedKFold, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import LinearSVC

from . import config

TEXTO = "cleaned_text"
OBJETIVO = "target"

# Los mismos ajustes del ejercicio 6.
TFIDF = dict(ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=100_000)


def clasificadores() -> dict:
    """Los tres algoritmos del ejercicio 6, con sus hiperparametros."""
    return {
        "Naive Bayes": MultinomialNB(alpha=0.5),
        "Regresión Logística": LogisticRegression(max_iter=1000, C=2.0),
        "SVM lineal": LinearSVC(C=1.0),
    }


def crear_pipeline(clasificador) -> Pipeline:
    """TF-IDF de unigramas y bigramas sobre el texto limpio, y el clasificador."""
    return Pipeline(
        [("tfidf", TfidfVectorizer(**TFIDF)), ("modelo", clasificador)]
    )


def crear_pipeline_mixto(clasificador, numericas: Sequence[str]) -> Pipeline:
    """El mismo pipeline mas una rama para las variables numericas.

    Las numericas pasan por `MinMaxScaler` y no por `StandardScaler`: hay que
    dejarlas en [0, 1] porque Naive Bayes multinomial no admite entradas
    negativas, y porque asi quedan en la misma escala que los pesos TF-IDF, que
    tampoco salen de ese intervalo.
    """
    preparacion = ColumnTransformer(
        [
            ("tfidf", TfidfVectorizer(**TFIDF), TEXTO),
            ("numericas", MinMaxScaler(), list(numericas)),
        ]
    )
    return Pipeline([("caracteristicas", preparacion), ("modelo", clasificador)])


def metricas(y_real, y_pred) -> dict:
    return {
        "accuracy": accuracy_score(y_real, y_pred),
        "precision": precision_score(y_real, y_pred),
        "recall": recall_score(y_real, y_pred),
        "f1": f1_score(y_real, y_pred),
    }


def dividir(df: pd.DataFrame):
    """La particion del ejercicio 6: 80/20 estratificada con la misma semilla."""
    return train_test_split(
        df,
        test_size=0.20,
        random_state=config.SEMILLA,
        stratify=df[OBJETIVO],
    )


def evaluar(df: pd.DataFrame, numericas: Sequence[str] = ()) -> pd.DataFrame:
    """Entrena los tres modelos sobre la particion fija y devuelve sus metricas.

    Con `numericas` vacio el montaje es exactamente el del ejercicio 6.
    """
    entrena, valida = dividir(df)
    filas = []
    for nombre, clasificador in clasificadores().items():
        if numericas:
            modelo = crear_pipeline_mixto(clasificador, numericas)
            xe, xv = entrena[[TEXTO, *numericas]], valida[[TEXTO, *numericas]]
        else:
            modelo = crear_pipeline(clasificador)
            xe, xv = entrena[TEXTO], valida[TEXTO]
        modelo.fit(xe, entrena[OBJETIVO])
        filas.append({"modelo": nombre, **metricas(valida[OBJETIVO], modelo.predict(xv))})
    return pd.DataFrame(filas)


def comparar_validacion_cruzada(
    df: pd.DataFrame,
    numericas: Sequence[str] = (),
    repeticiones: int = 3,
    pliegues: int = 5,
) -> pd.DataFrame:
    """F1 por pliegue con validacion cruzada estratificada y repetida.

    Una sola particion 80/20 no basta para afirmar que una variable mejoro el
    modelo: la diferencia que produce puede ser menor que el ruido de la
    particion. Con quince ajustes por modelo se obtiene una media y una
    desviacion, y la comparacion del ejercicio 10 se puede sostener.
    """
    particion = RepeatedStratifiedKFold(
        n_splits=pliegues, n_repeats=repeticiones, random_state=config.SEMILLA
    )
    y = df[OBJETIVO].to_numpy()
    columnas = [TEXTO, *numericas] if numericas else [TEXTO]
    filas = []
    for nombre, clasificador in clasificadores().items():
        for i, (idx_e, idx_v) in enumerate(particion.split(df, y)):
            modelo = (
                crear_pipeline_mixto(clasificadores()[nombre], numericas)
                if numericas
                else crear_pipeline(clasificadores()[nombre])
            )
            sub = df.iloc[idx_e]
            val = df.iloc[idx_v]
            xe = sub[columnas] if numericas else sub[TEXTO]
            xv = val[columnas] if numericas else val[TEXTO]
            modelo.fit(xe, y[idx_e])
            filas.append(
                {"modelo": nombre, "pliegue": i, "f1": f1_score(y[idx_v], modelo.predict(xv))}
            )
    return pd.DataFrame(filas)


def resumen_cruzada(detalle: pd.DataFrame) -> pd.DataFrame:
    return (
        detalle.groupby("modelo")["f1"]
        .agg(f1_medio="mean", desviacion="std")
        .reset_index()
        .sort_values("f1_medio", ascending=False)
        .reset_index(drop=True)
    )
