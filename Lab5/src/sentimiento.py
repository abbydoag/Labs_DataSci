"""Polaridad de los tweets: ejercicios 8, 9 y 10.

El lexico principal es VADER (Hutto y Gilbert, 2014), elegido porque esta
construido y validado sobre texto de redes sociales: trae reglas para la
negacion, para los intensificadores, para las MAYUSCULAS enfaticas, para los
signos de exclamacion y para los emoticones. Eso lo vuelve el instrumento
adecuado para responder la pregunta del ejercicio 8 sobre si conviene conservar
los emoticones, porque es capaz de leerlos.

TextBlob entra como segunda opinion. No se usa para decidir nada: sirve para
mostrar que las conclusiones del ejercicio 9 no dependen de un solo lexico.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Umbral estandar de VADER. Los autores lo fijan en 0.05 sobre la puntuacion
# compuesta y es el que usa la documentacion oficial del paquete.
UMBRAL = 0.05

CLASES = ["negativo", "neutro", "positivo"]
COLORES = {"negativo": "#c1272d", "neutro": "#9aa0a6", "positivo": "#2e8b57"}

_ANALIZADOR = SentimentIntensityAnalyzer()


def puntuar_vader(textos: pd.Series) -> pd.DataFrame:
    """Devuelve las cuatro puntuaciones de VADER para cada tweet.

    `neg`, `neu` y `pos` son la proporcion del texto que cae en cada tono y
    suman uno. `compound` es la suma de las valencias normalizada al intervalo
    [-1, 1] y es la que se usa para clasificar.
    """
    filas = [_ANALIZADOR.polarity_scores(str(t)) for t in textos.fillna("")]
    marco = pd.DataFrame(filas, index=textos.index)
    return marco.rename(columns={
        "neg": "vader_neg",
        "neu": "vader_neu",
        "pos": "vader_pos",
        "compound": "vader_compound",
    })


def puntuar_textblob(textos: pd.Series) -> pd.DataFrame:
    """Polaridad y subjetividad de TextBlob, el lexico de contraste."""
    pares = [TextBlob(str(t)).sentiment for t in textos.fillna("")]
    return pd.DataFrame(
        {
            "tb_polaridad": [p.polarity for p in pares],
            "tb_subjetividad": [p.subjectivity for p in pares],
        },
        index=textos.index,
    )


def clasificar_polaridad(compound: pd.Series, umbral: float = UMBRAL) -> pd.Series:
    """Traduce la puntuacion compuesta a positivo, negativo o neutro."""
    return pd.Series(
        np.select(
            [compound >= umbral, compound <= -umbral],
            ["positivo", "negativo"],
            default="neutro",
        ),
        index=compound.index,
        name="polaridad",
    )


def negatividad(compound: pd.Series) -> pd.Series:
    """Variable de negatividad del ejercicio 10, en el intervalo [0, 1].

    Es la puntuacion compuesta invertida y reescalada: 0 en el tweet mas
    positivo posible y 1 en el mas negativo. Se deja no negativa a proposito
    porque el mejor modelo del ejercicio 6 es Naive Bayes multinomial, que
    rechaza cualquier caracteristica con valores negativos.
    """
    return ((1.0 - compound) / 2.0).rename("negatividad")


def puntuar(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Agrega al marco las puntuaciones de los dos lexicos y las derivadas."""
    salida = df.copy()
    salida = pd.concat(
        [salida, puntuar_vader(salida[columna]), puntuar_textblob(salida[columna])],
        axis=1,
    )
    salida["polaridad"] = clasificar_polaridad(salida["vader_compound"])
    salida["negatividad"] = negatividad(salida["vader_compound"])
    return salida
