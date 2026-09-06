"""Analisis de sentimiento en espanol por lexico, al estilo de VADER.

Por que un lexico propio y no una libreria. Las opciones de estanteria fallan
en este corpus por razones distintas: VADER y TextBlob estan hechos para
ingles y sobre texto en espanol devuelven casi todo neutro; los modelos de
transformers en espanol (por ejemplo RoBERTuito) funcionan bien pero arrastran
`torch` y varios cientos de megas de pesos que hay que descargar en la primera
corrida, lo que rompe la promesa de reproducibilidad del enunciado.

Lo que se hace en cambio es lo mismo que hace VADER, adaptado al espanol: un
diccionario de polaridad con valores de -3 a 3, mas las reglas que cambian el
significado de una frase sin cambiar sus palabras de contenido.

    negacion       "no sirve" invierte y atenua la polaridad de "sirve"
    intensificador "muy corrupto" pesa mas que "corrupto"
    atenuador      "algo corrupto" pesa menos
    mayusculas     "CORRUPTOS" grita, y gritar intensifica
    exclamaciones  cada signo suma un poco
    emoji          entran al puntaje con su propia polaridad

El vocabulario mezcla dos capas. La primera es polaridad general del espanol.
La segunda es del dominio: estos comentarios hablan de gobierno, congreso,
sueldos y obras publicas, y ahi hay palabras que en abstracto son neutras pero
en contexto son claramente valorativas ("diputado" no, pero "corrupto",
"ladron", "impunidad" y "coima" si). Cada palabra de la capa de dominio salio
de revisar las mas frecuentes del propio corpus, lo cual conviene declarar: el
lexico esta ajustado a estos datos y no es un recurso general.
"""

from __future__ import annotations

import math
import unicodedata
from typing import Iterable

import pandas as pd

# --------------------------------------------------------------------------
# Lexico
# --------------------------------------------------------------------------

POSITIVAS = {
    # valoracion general
    "excelente": 3.0, "excelentes": 3.0, "maravilloso": 3.0, "maravillosa": 3.0,
    "increible": 2.5, "espectacular": 2.5, "extraordinario": 2.7, "genial": 2.5,
    "perfecto": 2.5, "perfecta": 2.5, "fantastico": 2.5, "estupendo": 2.4,
    "bueno": 1.8, "buena": 1.8, "buenos": 1.8, "buenas": 1.8, "buen": 1.8,
    "mejor": 1.6, "mejores": 1.6, "mejora": 1.4, "mejoro": 1.4, "mejorar": 1.2,
    "bien": 1.5, "bonito": 1.8, "bonita": 1.8, "lindo": 1.8, "linda": 1.8,
    "hermoso": 2.2, "hermosa": 2.2, "grandioso": 2.4, "gran": 1.2, "grande": 0.8,
    "positivo": 1.5, "positiva": 1.5, "correcto": 1.3, "correcta": 1.3,
    "util": 1.5, "utiles": 1.5, "interesante": 1.4, "claro": 0.8, "clara": 0.8,
    "agradable": 1.6, "comodo": 1.2, "seguro": 1.0, "segura": 1.0,
    "rapido": 0.9, "eficiente": 1.8, "eficaz": 1.6, "ordenado": 1.2,
    "limpio": 1.2, "limpia": 1.2, "moderno": 1.0, "digno": 1.6, "digna": 1.6,
    # agradecimiento, apoyo y afecto
    "gracias": 2.0, "agradecido": 2.0, "agradecida": 2.0, "agradezco": 2.0,
    "felicidades": 2.6, "felicitaciones": 2.6, "felicito": 2.4, "enhorabuena": 2.4,
    "bendiciones": 2.2, "bendicion": 2.0, "bendito": 1.6, "amen": 1.2,
    "apoyo": 1.8, "apoyamos": 1.8, "apoyo": 1.8, "apoyar": 1.5, "apoyando": 1.5,
    "felicidad": 2.4, "alegria": 2.2, "alegre": 2.0, "contento": 2.0,
    "orgullo": 2.2, "orgulloso": 2.2, "orgullosa": 2.2, "admiro": 2.0,
    "amor": 2.4, "amo": 2.2, "cariño": 2.0, "querido": 1.6, "querida": 1.6,
    "saludos": 1.2, "abrazo": 1.6, "abrazos": 1.6, "exitos": 2.0, "exito": 2.0,
    "adelante": 1.4, "viva": 1.8, "vivan": 1.8, "arriba": 1.0, "animo": 1.6,
    "esperanza": 1.6, "esperanzador": 1.8, "confianza": 1.5, "tranquilidad": 1.4,
    "paz": 1.8, "unidos": 1.4, "union": 1.2, "solidaridad": 1.8, "ayuda": 1.2,
    "gusta": 1.6, "gustó": 1.8, "gusto": 1.4, "encanta": 2.2, "encanto": 2.0,
    "recomiendo": 1.8, "aplaudo": 2.0, "aplausos": 2.0, "respeto": 1.5,
    "honesto": 2.2, "honesta": 2.2, "honestidad": 2.2, "honrado": 2.0,
    "transparencia": 2.0, "transparente": 2.0, "justicia": 1.4, "justo": 1.4,
    "verdad": 0.8, "cierto": 0.6, "razon": 0.8, "acuerdo": 0.8,
    # dominio: obra publica y servicios que la gente celebra
    "logro": 1.8, "logros": 1.8, "avance": 1.4, "avances": 1.4, "progreso": 1.6,
    "desarrollo": 1.2, "beneficio": 1.4, "beneficios": 1.4, "gratis": 1.0,
    "oportunidad": 1.4, "oportunidades": 1.4, "educacion": 0.8, "salud": 0.6,
    "felicidades": 2.6, "gracias": 2.0, "bravo": 2.2, "excelencia": 2.4,
}

NEGATIVAS = {
    # valoracion general
    "malo": -1.9, "mala": -1.9, "malos": -1.9, "malas": -1.9, "mal": -1.7,
    "peor": -2.2, "peores": -2.2, "pesimo": -2.8, "pesima": -2.8,
    "horrible": -2.8, "terrible": -2.7, "espantoso": -2.7, "atroz": -2.8,
    "desastre": -2.6, "desastroso": -2.6, "fatal": -2.6, "lamentable": -2.4,
    "deplorable": -2.6, "vergonzoso": -2.6, "verguenza": -2.5, "penoso": -2.2,
    "pena": -1.6, "triste": -1.8, "tristeza": -1.8, "feo": -1.6, "fea": -1.6,
    "inutil": -2.2, "inutiles": -2.2, "sirve": 0.0, "basura": -2.6,
    "porqueria": -2.6, "asco": -2.6, "asqueroso": -2.6, "ridiculo": -2.2,
    "absurdo": -2.0, "falso": -2.0, "falsa": -2.0, "mentira": -2.2,
    "mentiras": -2.2, "mentiroso": -2.4, "engaño": -2.2, "estafa": -2.6,
    "fraude": -2.6, "burla": -2.0, "payaso": -2.0, "payasos": -2.0,
    "tonto": -2.0, "estupido": -2.6, "idiota": -2.8, "imbecil": -2.8,
    "bruto": -2.2, "ignorante": -1.8, "incompetente": -2.4, "inepto": -2.4,
    "lento": -1.0, "caro": -1.2, "carisimo": -1.8, "sucio": -1.6,
    "peligroso": -1.8, "peligro": -1.6, "riesgo": -1.0, "dificil": -0.8,
    "problema": -1.4, "problemas": -1.4, "error": -1.4, "errores": -1.4,
    "falla": -1.4, "fallas": -1.4, "queja": -1.2, "quejas": -1.2,
    # emociones negativas
    "odio": -2.8, "odia": -2.6, "rabia": -2.4, "enojo": -2.0, "enojado": -2.0,
    "molesto": -1.8, "molesta": -1.8, "harto": -2.0, "hartos": -2.0,
    "cansado": -1.4, "decepcion": -2.2, "decepcionado": -2.2, "frustracion": -2.0,
    "miedo": -1.8, "temor": -1.6, "preocupacion": -1.4, "preocupado": -1.4,
    "dolor": -2.0, "sufrimiento": -2.4, "sufre": -2.0, "llorar": -1.8,
    "desgracia": -2.4, "tragedia": -2.6, "horror": -2.6, "impotencia": -2.2,
    # dominio: corrupcion, gobierno y protesta
    "corrupto": -2.8, "corrupta": -2.8, "corruptos": -2.8, "corruptas": -2.8,
    "corrupcion": -2.8, "corruptela": -2.6, "coima": -2.6, "coimas": -2.6,
    "soborno": -2.6, "sobornos": -2.6, "robo": -2.6, "roban": -2.6,
    "roba": -2.6, "robar": -2.6, "robaron": -2.6, "robando": -2.6,
    "ladron": -2.8, "ladrones": -2.8, "rateros": -2.8, "ratero": -2.8,
    "saqueo": -2.6, "saquean": -2.6, "impunidad": -2.6, "impune": -2.4,
    "delincuente": -2.6, "delincuentes": -2.6, "crimen": -2.4, "criminal": -2.6,
    "criminales": -2.6, "mafia": -2.6, "narco": -2.4, "extorsion": -2.6,
    "violencia": -2.4, "violento": -2.2, "asesinato": -2.8, "asesinos": -2.8,
    "muerte": -2.2, "muertos": -2.2, "muriendo": -2.2, "muere": -2.0,
    "hambre": -2.4, "pobreza": -2.2, "pobres": -1.4, "miseria": -2.4,
    "desnutricion": -2.4, "abandono": -2.0, "olvidado": -1.6, "olvidados": -1.6,
    "injusticia": -2.4, "injusto": -2.2, "abuso": -2.4, "abusos": -2.4,
    "atropello": -2.2, "represion": -2.4, "dictadura": -2.6, "tirano": -2.6,
    "traicion": -2.6, "traidor": -2.6, "traidores": -2.6, "vendido": -2.2,
    "vendidos": -2.2, "sinverguenza": -2.6, "sinverguenzas": -2.6,
    "descarado": -2.4, "descarados": -2.4, "cinico": -2.2, "cinismo": -2.2,
    "mediocre": -2.0, "mediocridad": -2.0, "fracaso": -2.4, "fracasado": -2.4,
    "caos": -2.2, "colapso": -2.2, "crisis": -2.0, "emergencia": -1.4,
    "protesta": -0.8, "renuncia": -1.2, "renuncie": -1.6, "carcel": -1.6,
    "denuncia": -1.2, "escandalo": -2.0, "negligencia": -2.4, "corruptos": -2.8,
    "pacto": -1.2, "chapuza": -2.2, "bache": -1.6, "baches": -1.6,
    "trafico": -1.2, "trancadera": -1.8, "inundacion": -1.8, "derrumbe": -1.8,
    "danos": -1.6, "damnificados": -2.0, "perdidas": -1.8,
}

LEXICO: dict[str, float] = {}
LEXICO.update(POSITIVAS)
LEXICO.update(NEGATIVAS)
# "sirve" se declara arriba en neutro a proposito: casi siempre aparece como
# "no sirve", y la regla de negacion se encarga de darle el signo.
LEXICO["sirve"] = 1.2
LEXICO["funciona"] = 1.2
LEXICO["cumple"] = 1.4
LEXICO["cumplen"] = 1.4

EMOJI_POLARIDAD = {
    "😀": 2.0, "😃": 2.0, "😄": 2.2, "😁": 2.0, "😊": 2.2, "🙂": 1.2,
    "😍": 2.6, "🥰": 2.6, "😘": 2.2, "❤": 2.4, "❤️": 2.4, "💖": 2.4,
    "💚": 2.0, "💙": 2.0, "🇬🇹": 1.4, "👏": 2.0, "👍": 2.0, "🙌": 2.0,
    "💪": 1.8, "🙏": 1.4, "✅": 1.4, "🎉": 2.2, "😂": 1.0, "🤣": 1.0,
    "😢": -2.0, "😭": -2.2, "😔": -1.8, "😞": -1.8, "😡": -2.6, "🤬": -2.8,
    "😠": -2.4, "👎": -2.2, "🤮": -2.6, "🤢": -2.4, "💩": -2.6, "🙄": -1.4,
    "😒": -1.6, "😤": -1.8, "❌": -1.4, "⚠": -1.0, "😱": -1.6, "🤡": -2.2,
}

NEGACIONES = {
    "no", "ni", "nunca", "jamas", "nada", "nadie", "ninguno", "ninguna",
    "ningun", "tampoco", "sin", "apenas",
}

INTENSIFICADORES = {
    "muy": 0.35, "mucho": 0.30, "mucha": 0.30, "muchos": 0.30, "muchas": 0.30,
    "super": 0.40, "tan": 0.30, "demasiado": 0.40, "totalmente": 0.35,
    "completamente": 0.35, "absolutamente": 0.40, "realmente": 0.30,
    "verdaderamente": 0.30, "bastante": 0.20, "sumamente": 0.40,
    "extremadamente": 0.45, "increiblemente": 0.40, "puro": 0.25, "pura": 0.25,
    "recontra": 0.45, "requete": 0.40, "bien": 0.20,
    "poco": -0.30, "poca": -0.30, "algo": -0.25, "medio": -0.20,
    "ligeramente": -0.30, "apenas": -0.30, "casi": -0.20, "mas o menos": -0.25,
}

# Constante de normalizacion de VADER. Comprime la suma de polaridades al
# intervalo (-1, 1) sin cortarla: un comentario con muchas palabras cargadas se
# acerca a los extremos pero nunca los alcanza.
ALFA = 15.0

UMBRAL = 0.05
NEGACION_FACTOR = -0.74  # el mismo amortiguamiento que usa VADER
MAYUSCULA_BOOST = 0.733
EXCLAMACION_BOOST = 0.292
MAX_EXCLAMACIONES = 4


def _sin_tildes(texto: str) -> str:
    normal = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normal if unicodedata.category(c) != "Mn")


def _fichas(texto: str) -> list[str]:
    limpio = "".join(c if c.isalnum() or c.isspace() else " " for c in texto)
    return limpio.split()


def _grita(ficha: str) -> bool:
    """Una palabra grita si va toda en mayusculas y tiene mas de tres letras."""
    return ficha.isupper() and len(ficha) > 3


def puntuar(texto: str) -> float:
    """Devuelve la polaridad compuesta de un texto, entre -1 y 1.

    Se calcula sobre `texto_original`, no sobre `texto_limpio`: la limpieza
    borra justamente las negaciones, las mayusculas, los signos y los emoji,
    que son la mitad de la senal.
    """
    if not isinstance(texto, str) or not texto.strip():
        return 0.0

    crudo = _fichas(texto)
    minusculas = [_sin_tildes(f.lower()) for f in crudo]
    hay_mayusculas = any(_grita(f) for f in crudo) and not all(
        f.isupper() for f in crudo if f.isalpha()
    )

    puntajes: list[float] = []
    for i, palabra in enumerate(minusculas):
        if palabra not in LEXICO:
            continue
        valor = LEXICO[palabra]

        # Gritar intensifica en la direccion que ya tenia la palabra.
        if hay_mayusculas and _grita(crudo[i]):
            valor += math.copysign(MAYUSCULA_BOOST, valor)

        # Se miran las tres palabras anteriores, como VADER: los modificadores
        # del espanol casi siempre van antes ("muy corrupto", "no muy bueno").
        for distancia in (1, 2, 3):
            j = i - distancia
            if j < 0:
                break
            previa = minusculas[j]
            if previa in INTENSIFICADORES:
                escala = INTENSIFICADORES[previa] * (1 - 0.05 * (distancia - 1))
                valor += math.copysign(abs(valor) * escala, valor)
            if previa in NEGACIONES:
                valor *= NEGACION_FACTOR

        puntajes.append(valor)

    for simbolo in texto:
        if simbolo in EMOJI_POLARIDAD:
            puntajes.append(EMOJI_POLARIDAD[simbolo])

    if not puntajes:
        return 0.0

    suma = sum(puntajes)
    exclamaciones = min(texto.count("!"), MAX_EXCLAMACIONES)
    if exclamaciones:
        suma += math.copysign(exclamaciones * EXCLAMACION_BOOST, suma)

    return suma / math.sqrt(suma * suma + ALFA)


def etiquetar(puntaje: float, umbral: float = UMBRAL) -> str:
    """Corta el puntaje continuo en las tres categorias de siempre."""
    if puntaje >= umbral:
        return "positivo"
    if puntaje <= -umbral:
        return "negativo"
    return "neutro"


def palabras_encontradas(texto: str) -> list[tuple[str, float]]:
    """Palabras del lexico presentes en el texto. Sirve para auditar un caso."""
    salida = []
    for f in _fichas(texto):
        clave = _sin_tildes(f.lower())
        if clave in LEXICO:
            salida.append((f, LEXICO[clave]))
    for simbolo in texto:
        if simbolo in EMOJI_POLARIDAD:
            salida.append((simbolo, EMOJI_POLARIDAD[simbolo]))
    return salida


def puntuar_serie(serie: Iterable[str]) -> pd.Series:
    return pd.Series([puntuar(t) for t in serie], index=getattr(serie, "index", None))


def agregar_sentimiento(
    df: pd.DataFrame, columna: str = "texto_original"
) -> pd.DataFrame:
    """Agrega `sentimiento` (continuo) y `sentimiento_etiqueta` (tres clases)."""
    salida = df.copy()
    salida["sentimiento"] = [puntuar(t) for t in salida[columna].fillna("")]
    salida["sentimiento_etiqueta"] = salida["sentimiento"].map(etiquetar)
    return salida
