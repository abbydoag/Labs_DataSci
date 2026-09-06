"""Las dos versiones del texto de los comentarios y las decisiones detras.

El ejercicio 2.5 pide conservar `texto_original` y construir `texto_limpio`.
Las dos se usan para cosas distintas y por eso conviven:

- `texto_original` no se toca. Es el que audita el resultado y el que alimenta
  el analisis de sentimiento, porque la polaridad vive justo en lo que la
  limpieza borra: los emoji, los signos de exclamacion, las mayusculas y las
  palabras vacias que niegan ("no", "nunca", "nada").
- `texto_limpio` es para contar. Frecuencias, bigramas, nubes y temas
  necesitan que "Corruptos!" y "corruptos" sean la misma palabra.

Cada paso de la limpieza queda como funcion separada para poder medir cuanto
recorta cada uno, que es lo que pide el ejercicio 2.7.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter

import nltk
import pandas as pd

nltk.download("stopwords", quiet=True)

from nltk.corpus import stopwords  # noqa: E402
from nltk.stem import SnowballStemmer  # noqa: E402

PALABRAS_VACIAS = set(stopwords.words("spanish"))

# Ruido propio de los comentarios de YouTube que las listas generales no traen.
# Se agrega despues de mirar las palabras mas frecuentes: son formas verbales y
# muletillas que aparecen en todos los videos y no distinguen ningun tema.
VACIAS_EXTRA = {
    "ja",
    "jaja",
    "jajaja",
    "jajajaja",
    "jajajajaja",
    "jeje",
    "jejeje",
    "asi",
    "aqui",
    "ahi",
    "ahora",
    "pues",
    "solo",
    "tan",
    "ser",
    "hacer",
    "hace",
    "hacen",
    "haciendo",
    "van",
    "ver",
    "dice",
    "dicen",
    "dijo",
    "puede",
    "cosas",
    "mas",
    "si",
    "no",
    "q",
    "xq",
    "pq",
    "d",
    "the",
    "you",
}
VACIAS = PALABRAS_VACIAS | VACIAS_EXTRA

_RAIZ = SnowballStemmer("spanish")

URL = re.compile(r"https?://\S+|www\.\S+")
HASHTAG = re.compile(r"#(\w+)", re.UNICODE)
MENCION = re.compile(r"@([\w.\-]+)", re.UNICODE)
NUMERO = re.compile(r"\d+")
NO_LETRA = re.compile(r"[^a-záéíóúüñ\s]", re.UNICODE)
ESPACIOS = re.compile(r"\s+")
REPETIDAS = re.compile(r"(.)\1{2,}")
CAMELLO = re.compile(r"(?<=[a-záéíóúñ])(?=[A-ZÁÉÍÓÚÑ])")

# Los emoji se detectan por categoria Unicode en vez de por rangos fijos: los
# rangos se quedan cortos con las banderas y con los simbolos combinados, y en
# este corpus hay banderas de Guatemala en cantidad.
def es_emoji(caracter: str) -> bool:
    punto = ord(caracter)
    return (
        0x1F000 <= punto <= 0x1FAFF
        or 0x2600 <= punto <= 0x27BF
        or 0x1F1E6 <= punto <= 0x1F1FF
        or punto in (0x2764, 0x2049, 0x203C)
        or 0xFE00 <= punto <= 0xFE0F
    )


def extraer_emojis(texto: str) -> list[str]:
    """Devuelve los emoji de un texto, uniendo las banderas en un solo simbolo.

    Una bandera se escribe con dos indicadores regionales seguidos, asi que
    contar caracteres sueltos duplicaria cada bandera. En este corpus la de
    Guatemala aparece bastante y conviene que cuente como una.
    """
    if not isinstance(texto, str):
        return []
    salida: list[str] = []
    i = 0
    while i < len(texto):
        c = texto[i]
        if 0xFE00 <= ord(c) <= 0xFE0F:
            i += 1
            continue
        if 0x1F1E6 <= ord(c) <= 0x1F1FF:
            if i + 1 < len(texto) and 0x1F1E6 <= ord(texto[i + 1]) <= 0x1F1FF:
                salida.append(texto[i : i + 2])
                i += 2
                continue
        if es_emoji(c):
            salida.append(c)
        i += 1
    return salida


def quitar_emojis(texto: str) -> str:
    return "".join(c for c in texto if not es_emoji(c))


def extraer_hashtags(texto: str) -> list[str]:
    if not isinstance(texto, str):
        return []
    return [h.lower() for h in HASHTAG.findall(texto)]


def extraer_menciones(texto: str) -> list[str]:
    if not isinstance(texto, str):
        return []
    return ["@" + m.lower() for m in MENCION.findall(texto)]


def extraer_urls(texto: str) -> list[str]:
    if not isinstance(texto, str):
        return []
    return URL.findall(texto)


def separar_camello(texto: str) -> str:
    """Parte `#LluviasEnGuatemala` en `lluvias en guatemala`.

    Sin esto cada hashtag seria una palabra unica que no se cruza con nada, y
    justo el contenido del hashtag es lo que interesa para los temas.
    """
    return CAMELLO.sub(" ", texto)


def limpiar(texto: str, quitar_vacias: bool = True) -> str:
    """Construye `texto_limpio` en el orden en que se documenta el ejercicio 2.6.

    El orden importa y por eso se fija aqui:

    1. URL fuera. Van primero porque contienen letras, puntos y numeros que
       los pasos siguientes convertirian en basura ("httpsyoutube", "com").
    2. Menciones fuera. Un `@handle` identifica a una cuenta, no aporta tema, y
       ademas es dato personal que no conviene arrastrar a una nube de palabras.
    3. Hashtags: se quita la almohadilla y se separa el camello, de modo que el
       contenido del hashtag se suma al texto como palabras normales.
    4. Emoji fuera de esta version, pero guardados aparte. Aqui estorban
       porque no son palabras; en el sentimiento son de los mejores indicios.
    5. Minusculas.
    6. Letras repetidas al maximo de dos ("holaaaaa" -> "holaa"), para que el
       alargamiento expresivo no invente palabras nuevas.
    7. Numeros y puntuacion fuera. Los conteos que importan ya viven en sus
       propias columnas numericas.
    8. Palabras vacias del espanol mas la lista propia.
    9. Palabras de una o dos letras fuera, que es lo que queda de las
       contracciones rotas por el paso anterior.

    No se lematiza. NLTK no trae lematizador de espanol y meter spaCy solo por
    esto agregaria un modelo de varios cientos de megas al entorno. En su lugar
    se ofrece `raiz`, que aplica el stemmer Snowball, para cuando haga falta
    juntar variantes ("corrupto", "corruptos", "corrupcion"). Las frecuencias y
    los bigramas del exploratorio usan `texto_limpio` sin raiz porque las
    palabras completas se leen mejor en las figuras.
    """
    if not isinstance(texto, str):
        return ""

    t = URL.sub(" ", texto)
    t = MENCION.sub(" ", t)
    t = HASHTAG.sub(lambda m: " " + separar_camello(m.group(1)) + " ", t)
    t = quitar_emojis(t)
    t = t.lower()
    t = REPETIDAS.sub(r"\1\1", t)
    t = NUMERO.sub(" ", t)
    t = NO_LETRA.sub(" ", t)
    t = ESPACIOS.sub(" ", t).strip()

    fichas = [p for p in t.split() if len(p) > 2]
    if quitar_vacias:
        fichas = [p for p in fichas if p not in VACIAS and sin_tildes(p) not in VACIAS]
    return " ".join(fichas)


def sin_tildes(texto: str) -> str:
    normal = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normal if unicodedata.category(c) != "Mn")


def raiz(texto: str) -> str:
    """Aplica el stemmer Snowball a un texto ya limpio."""
    return " ".join(_RAIZ.stem(p) for p in texto.split())


def fichas(texto: str) -> list[str]:
    return texto.split() if isinstance(texto, str) else []


def bigramas(texto: str) -> list[tuple[str, str]]:
    palabras = fichas(texto)
    return list(zip(palabras, palabras[1:]))


def contar(serie: pd.Series, func) -> Counter:
    """Aplica `func` a cada texto y acumula todo en un solo contador."""
    total: Counter = Counter()
    for valor in serie.dropna():
        total.update(func(valor))
    return total


def agregar_versiones(df: pd.DataFrame, columna: str = "text") -> pd.DataFrame:
    """Agrega al conjunto de comentarios las dos versiones y sus derivados.

    Devuelve una copia. `texto_original` queda identico a la columna de origen
    y `texto_limpio` es el resultado de `limpiar`.
    """
    salida = df.copy()
    salida["texto_original"] = salida[columna].fillna("")
    salida["hashtags"] = salida["texto_original"].map(extraer_hashtags)
    salida["menciones"] = salida["texto_original"].map(extraer_menciones)
    salida["urls"] = salida["texto_original"].map(extraer_urls)
    salida["emojis"] = salida["texto_original"].map(extraer_emojis)
    salida["n_emojis"] = salida["emojis"].map(len)
    salida["texto_limpio"] = salida["texto_original"].map(limpiar)
    salida["texto_raiz"] = salida["texto_limpio"].map(raiz)
    salida["largo_original"] = salida["texto_original"].str.len()
    salida["largo_limpio"] = salida["texto_limpio"].str.len()
    salida["n_palabras"] = salida["texto_limpio"].map(lambda t: len(t.split()))
    return salida
