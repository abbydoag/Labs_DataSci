"""Carga, normalizacion e integracion de los dos conjuntos de YouTube.

Aqui vive todo lo que el ejercicio 2 llama preprocesamiento estructural: pasar
a numero los conteos que vienen como texto, convertir a lista las columnas que
son listas disfrazadas de cadena, anclar los tiempos relativos a una fecha y
normalizar nombres y handles sin tocar los identificadores.

Regla que se respeta en todo el modulo: los ID (`video_id`, `channel_id`,
`comment_id`, `author_channel_id`) se limpian de espacios y nada mas. Nunca se
sustituyen por el nombre visible, porque los nombres cambian y se repiten.
"""

from __future__ import annotations

import ast
import re
from typing import Any

import numpy as np
import pandas as pd

from . import config

# --------------------------------------------------------------------------
# Conteos almacenados como texto
# --------------------------------------------------------------------------

# YouTube abrevia los conteos grandes segun el idioma de la interfaz. En este
# conjunto no aparece ninguna abreviatura, pero el conversor las contempla
# porque una recoleccion nueva si podria traerlas y el enunciado pide
# documentar el tratamiento.
MULTIPLICADORES = {
    "mil": 1_000,
    "k": 1_000,
    "m": 1_000_000,
    "mill": 1_000_000,
    "millon": 1_000_000,
    "millones": 1_000_000,
    "b": 1_000_000_000,
}

_NUMERO = re.compile(r"(\d+(?:[.,]\d+)*)\s*([a-zA-Zñ]*)")


def a_entero(valor: Any) -> float:
    """Convierte a numero un conteo escrito como texto.

    Cubre los cuatro casos que trae el conjunto y los dos que podria traer:

    - `"2,390 vistas"`  -> 2390. La coma es separador de miles en la interfaz
      en espanol de YouTube, no separador decimal.
    - `"4"`             -> 4.
    - `" "` o `""`      -> 0. Un comentario sin "me gusta" no muestra el cero,
      muestra un espacio. Es un cero observado, no un dato faltante, y por eso
      no se convierte en NaN: tratarlo como faltante inflaria el promedio de
      "me gusta" al excluir justo a los comentarios que no gustaron a nadie.
    - `NaN`             -> NaN. Ausencia real de dato.
    - `"2.4 mil"`, `"1,2 M"` -> 2400, 1200000. Abreviaturas, por si aparecen.

    Cualquier otra cosa devuelve NaN en vez de reventar, para que un valor
    invalido se pueda contar y reportar en el diagnostico de calidad.
    """
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return np.nan
    if isinstance(valor, (int, np.integer)):
        return float(valor)

    texto = str(valor).strip().lower()
    if texto == "":
        return 0.0

    encontrado = _NUMERO.search(texto)
    if encontrado is None:
        return np.nan

    crudo, sufijo = encontrado.groups()
    factor = MULTIPLICADORES.get(sufijo, 1)

    # El conjunto viene de la interfaz en espanol de America Latina, donde la
    # coma separa los miles y el punto los decimales: "2,390 vistas" son dos
    # mil trescientos noventa y "2.4 mil" son dos mil cuatrocientos. Se aplica
    # la misma regla siempre, haya o no abreviatura.
    crudo = crudo.replace(",", "")

    try:
        return float(crudo) * factor
    except ValueError:
        return np.nan


def parsear_lista(valor: Any) -> list[str]:
    """Convierte a lista de Python las columnas que son listas en texto.

    `query_hits` y `keywords` llegan como `'["guatemala lluvias"]'`. Se leen
    con `ast.literal_eval`, que solo evalua literales y no ejecuta codigo. Lo
    que no se pueda leer devuelve lista vacia.
    """
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return []
    if isinstance(valor, list):
        return [str(x) for x in valor]
    try:
        leido = ast.literal_eval(str(valor))
    except (ValueError, SyntaxError):
        return []
    if isinstance(leido, list):
        return [str(x).strip() for x in leido if str(x).strip()]
    return []


def parsear_fuentes(valor: Any) -> list[str]:
    """Separa `dataset_sources`, que viene con los archivos unidos por `|`."""
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return []
    return [x.strip() for x in str(valor).split("|") if x.strip()]


# --------------------------------------------------------------------------
# Tiempos relativos
# --------------------------------------------------------------------------

# Equivalencia en dias de cada unidad que usa YouTube, en singular y en plural.
# Se listan las dos formas en vez de recortar la "s" final porque el plural de
# "mes" es "meses" y el de "dia" lleva tilde: cualquier regla automatica se
# equivoca con alguno de los dos.
UNIDADES_DIAS = {
    "minuto": 1 / 1440,
    "minutos": 1 / 1440,
    "hora": 1 / 24,
    "horas": 1 / 24,
    "dia": 1.0,
    "dias": 1.0,
    "semana": 7.0,
    "semanas": 7.0,
    "mes": 30.44,
    "meses": 30.44,
    "ano": 365.25,
    "anos": 365.25,
}

_RELATIVO = re.compile(r"hace\s+(\d+)\s+([a-z]+)")


def _sin_tildes(texto: str) -> str:
    """Quita tildes y la enie. Solo para comparar, nunca para mostrar."""
    tabla = str.maketrans("áéíóúüñ", "aeiouun")
    return texto.translate(tabla)


def dias_desde(valor: Any) -> float:
    """Traduce "hace 2 semanas" al numero aproximado de dias.

    Es una aproximacion y hay que decirlo: YouTube redondea hacia abajo, asi
    que "hace 1 ano" cubre cualquier cosa entre 12 y 23 meses. Sirve para
    ordenar y para agrupar en tramos gruesos, no para fechar un comentario.
    """
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return np.nan
    texto = _sin_tildes(str(valor).lower())
    encontrado = _RELATIVO.search(texto)
    if encontrado is None:
        return np.nan
    cantidad, unidad = encontrado.groups()
    if unidad not in UNIDADES_DIAS:
        return np.nan
    return float(cantidad) * UNIDADES_DIAS[unidad]


def fue_editado(valor: Any) -> bool:
    """`published_text` marca con "(editado)" los comentarios modificados."""
    return "editado" in str(valor).lower()


# --------------------------------------------------------------------------
# Normalizacion de nombres, handles e identificadores
# --------------------------------------------------------------------------

ESPACIOS = re.compile(r"\s+")


def normalizar_id(valor: Any) -> str:
    """Limpia un identificador. Solo espacios: el ID nunca se reemplaza."""
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return ""
    return str(valor).strip()


def normalizar_nombre(valor: Any) -> str:
    """Colapsa espacios en un nombre visible y le quita los extremos.

    No pasa a minusculas ni quita tildes: el nombre se muestra en las figuras
    y debe verse como en YouTube. La version comparable se obtiene con
    `clave_nombre`.
    """
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return ""
    return ESPACIOS.sub(" ", str(valor)).strip()


def clave_nombre(valor: Any) -> str:
    """Version comparable de un nombre: minusculas, sin tildes, sin espacios dobles."""
    return _sin_tildes(normalizar_nombre(valor).lower())


def normalizar_handle(valor: Any) -> str:
    """Deja los handles en la forma `@nombre`.

    Llegan como `/@nombre`, `@nombre` o `nombre`. Se unifican para poder
    compararlos entre archivos, pero siguen siendo etiquetas: el nodo se
    identifica con `channel_id` o `author_channel_id`.
    """
    texto = normalizar_nombre(valor)
    if not texto:
        return ""
    texto = texto.lstrip("/")
    if not texto.startswith("@"):
        texto = "@" + texto
    return texto


# --------------------------------------------------------------------------
# Carga
# --------------------------------------------------------------------------


def cargar_videos() -> pd.DataFrame:
    """Lee `youtube_videos.csv` y agrega las columnas derivadas.

    No elimina ninguna fila ni ninguna columna original: el diagnostico de
    calidad del ejercicio 2 necesita ver el conjunto completo.
    """
    df = pd.read_csv(config.VIDEOS, dtype=str)

    for col in ("video_id", "channel_id"):
        df[col] = df[col].map(normalizar_id)
    for col in ("channel_name", "title", "description", "description_snippet"):
        df[col] = df[col].map(normalizar_nombre)
    for col in ("channel_handle", "owner_handle"):
        df[col] = df[col].map(normalizar_handle)

    df["canal_clave"] = df["channel_name"].map(clave_nombre)
    df["vistas"] = df["view_count"].map(a_entero)
    df["vistas_texto"] = df["view_count_text"].map(a_entero)
    df["consultas"] = df["query_hits"].map(parsear_lista)
    df["etiquetas"] = df["keywords"].map(parsear_lista)
    df["archivos_origen"] = df["dataset_sources"].map(parsear_fuentes)
    df["n_etiquetas"] = df["etiquetas"].map(len)
    df["n_consultas"] = df["consultas"].map(len)
    df["fecha_publicacion"] = pd.to_datetime(
        df["publish_date"], format="ISO8601", utc=True
    )
    df["anio"] = df["fecha_publicacion"].dt.year
    df["dias_relativos"] = df["published_time"].map(dias_desde)

    return df


def cargar_comentarios() -> pd.DataFrame:
    """Lee `youtube_comments.csv` y agrega las columnas derivadas."""
    df = pd.read_csv(config.COMENTARIOS, dtype=str)

    for col in ("video_id", "comment_id", "channel_id", "author_channel_id"):
        df[col] = df[col].map(normalizar_id)
    for col in ("author_name", "channel_name", "video_title"):
        df[col] = df[col].map(normalizar_nombre)
    df["author_handle"] = df["author_handle"].map(normalizar_handle)

    df["autor_clave"] = df["author_name"].map(clave_nombre)
    df["me_gusta"] = df["like_count_text"].map(a_entero)
    df["respuestas"] = pd.to_numeric(df["reply_count"], errors="coerce")
    df["dias_relativos"] = df["published_text"].map(dias_desde)
    df["editado"] = df["published_text"].map(fue_editado)
    df["fijado"] = df["is_pinned"].astype(str).str.lower().eq("true")
    df["archivos_origen"] = df["dataset_sources"].map(parsear_fuentes)

    # El texto original se conserva intacto. La version limpia la agrega
    # `texto.agregar_versiones`, que es donde viven esas decisiones.
    df["texto_original"] = df["text"]

    return df


def integrar(
    comentarios: pd.DataFrame, videos: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Une comentarios con videos por `video_id` y reporta el emparejamiento.

    Se usa una union por la izquierda desde comentarios: interesa saber cuantos
    comentarios encontraron su video, no cuantos videos se quedaron sin
    comentarios (eso se mide aparte y es el hallazgo grande del conjunto).

    Las columnas repetidas en ambos archivos (`channel_name`, `channel_id`,
    `source_query`, `source_group`) se traen con el sufijo `_video` en vez de
    pisarse, porque en los comentarios describen al canal del video comentado
    y conviene poder verificar que coinciden.
    """
    columnas = [
        "video_id",
        "title",
        "channel_id",
        "channel_name",
        "channel_handle",
        "category",
        "source_query",
        "source_group",
        "vistas",
        "fecha_publicacion",
        "anio",
        "etiquetas",
        "n_etiquetas",
    ]
    unido = comentarios.merge(
        videos[columnas],
        on="video_id",
        how="left",
        suffixes=("", "_video"),
        indicator=True,
    )

    resumen = {
        "comentarios": len(comentarios),
        "emparejados": int((unido["_merge"] == "both").sum()),
        "huerfanos": int((unido["_merge"] == "left_only").sum()),
        "videos_totales": videos["video_id"].nunique(),
        "videos_con_comentarios": comentarios["video_id"].nunique(),
    }
    resumen["videos_sin_comentarios"] = (
        resumen["videos_totales"] - resumen["videos_con_comentarios"]
    )
    return unido.drop(columns="_merge"), resumen
