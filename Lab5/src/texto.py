"""Limpieza de los tweets y carga del conjunto de datos.

Aqui conviven dos limpiezas distintas y esa es la idea. `limpieza_clasificacion`
reproduce exactamente la del ejercicio 3, la que alimenta a los clasificadores.
`limpieza_sentimiento` es mucho mas suave y existe porque el ejercicio 8
pregunta si vale la pena conservar los emoticones: para responder que si o que
no hay que poder medir las dos versiones sobre los mismos tweets.
"""

from __future__ import annotations

import re
from typing import Iterable

import nltk
import pandas as pd

from . import config

for _recurso in ("stopwords", "wordnet", "omw-1.4"):
    nltk.download(_recurso, quiet=True)

from nltk.corpus import stopwords  # noqa: E402
from nltk.stem import WordNetLemmatizer  # noqa: E402

PALABRAS_VACIAS = set(stopwords.words("english"))
_LEMATIZADOR = WordNetLemmatizer()

URL = re.compile(r"http\S+|www\.\S+|https\S+")
NO_ALFABETICO = re.compile(r"[^a-zA-Z\s]")
ESPACIOS = re.compile(r"\s+")

# Emoticones ASCII de los mas comunes. El orden importa: las variantes con
# nariz van primero para que no las corte la version corta.
EMOTICONES = re.compile(
    r"(?<!\w)(?::|;|=|8|x|X)(?:-|\^)?(?:\)|\(|\]|\[|D|P|p|O|o|/|\\|\||3)"
    r"|(?<!\w)<3|(?<!\w)</3|(?<!\w)\^_?\^|(?<!\w)T_T|(?<!\w)-_-"
)

# Rangos Unicode de emoji, los mismos que usa el ejercicio 3.
EMOJI = re.compile(
    "["
    "\U0001f600-\U0001f64f"
    "\U0001f300-\U0001f5ff"
    "\U0001f680-\U0001f6ff"
    "\U0001f1e0-\U0001f1ff"
    "\U00002702-\U000027b0"
    "\U000024c2-\U0001f251"
    "]+",
    flags=re.UNICODE,
)


def quitar_emoji(texto: str) -> str:
    return EMOJI.sub("", texto)


def limpieza_clasificacion(texto: str, lematizar: bool = False) -> str:
    """Limpieza del ejercicio 3, replicada tal como se ejecuto.

    Minusculas, fuera las URL, fuera todo lo que no sea letra o espacio, fuera
    los emoji y fuera las palabras vacias. Notese que el filtro de caracteres se
    aplica antes que el de emoji, asi que para cuando este corre ya no queda
    ningun simbolo: se conserva el orden original para que el texto resultante
    sea identico al que entreno los modelos del ejercicio 6.

    La lematizacion viene desactivada por omision, y eso no es un descuido. El
    ejercicio 3 envuelve al lematizador de WordNet en un `try` que cae a la
    identidad si el corpus no esta descargado, y en el entorno donde se corrio
    esa rama fue la que se tomo: el corpus versionado en `processed/` conserva
    "deeds" y "us" sin reducir. Comprobado sobre las 7,613 filas, esta funcion
    con `lematizar=False` reproduce el 99.92 % del corpus y con `lematizar=True`
    solo el 40.18 %. Los modelos del ejercicio 6 se entrenaron sobre el primero,
    de modo que lematizar aqui abriria una brecha entre el texto de
    entrenamiento y el de un tweet nuevo. El interruptor queda por si se decide
    reprocesar todo el laboratorio.
    """
    if pd.isna(texto):
        return ""
    texto = str(texto).lower()
    texto = URL.sub("", texto)
    texto = NO_ALFABETICO.sub("", texto)
    texto = ESPACIOS.sub(" ", texto).strip()
    texto = quitar_emoji(texto)
    tokens = [t for t in texto.split() if t not in PALABRAS_VACIAS]
    if lematizar:
        tokens = [_LEMATIZADOR.lemmatize(t) for t in tokens]
    return " ".join(tokens)


def limpieza_sentimiento(texto: str) -> str:
    """Limpieza minima para el analisis de polaridad.

    Solo quita las URL y las menciones, y normaliza los espacios. Conserva
    mayusculas, signos de exclamacion, negaciones, emoticones y emoji, que son
    precisamente las senales sobre las que VADER esta calibrado. La almohadilla
    de los hashtag se quita pero la palabra se queda, porque `#earthquake` lleva
    contenido y `#` no.
    """
    if pd.isna(texto):
        return ""
    texto = str(texto)
    texto = URL.sub(" ", texto)
    texto = re.sub(r"@\w+", " ", texto)
    texto = texto.replace("#", "")
    texto = re.sub(r"&amp;", "&", texto)
    texto = ESPACIOS.sub(" ", texto).strip()
    return texto


def contar_emoticones(textos: Iterable[str]) -> pd.Series:
    """Cuenta emoticones ASCII por tweet, ya sin las URL.

    Se limpian las URL antes de contar porque `http://` contiene `:/`, que el
    patron reconoceria como cara de disgusto en casi todos los tweets con enlace.
    """
    serie = pd.Series(list(textos), dtype="object").fillna("")
    return serie.map(lambda t: len(EMOTICONES.findall(URL.sub(" ", str(t)))))


def contar_emoji(textos: Iterable[str]) -> pd.Series:
    serie = pd.Series(list(textos), dtype="object").fillna("")
    return serie.map(lambda t: len(EMOJI.findall(str(t))))


def cargar_tweets() -> pd.DataFrame:
    """Devuelve el conjunto de entrenamiento con la limpieza del ejercicio 3.

    Prefiere el CSV que dejo el ejercicio 3 en `processed/`. Si no esta, lo
    reconstruye desde `data/train.csv` con la misma limpieza, de manera que los
    cuadernos 08 al 10 corren aunque solo se tenga el dato crudo.
    """
    if config.TRAIN_PROCESADO.exists():
        df = pd.read_csv(config.TRAIN_PROCESADO)
    else:
        df = pd.read_csv(config.TRAIN)
        df["full_text"] = df["keyword"].fillna("") + " " + df["text"].fillna("")
        df["cleaned_text"] = df["full_text"].map(limpieza_clasificacion)
        df["word_count"] = df["cleaned_text"].str.split().str.len()
        df["text_length_original"] = df["text"].str.len()
        df["text_length_cleaned"] = df["cleaned_text"].str.len()
    df["cleaned_text"] = df["cleaned_text"].fillna("")
    return df
