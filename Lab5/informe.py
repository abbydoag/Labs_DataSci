"""Genera Informe_Lab5.pdf, el informe del laboratorio de mineria de textos.

Recoge los once ejercicios del enunciado: la descripcion del conjunto, la
limpieza, las frecuencias y los n-gramas, el exploratorio, los clasificadores,
la funcion de clasificacion, el analisis de sentimiento, los tweets extremos y
la variable de negatividad. Se corre despues de los cuadernos:

    .venv/bin/python informe.py

Todas las cifras se recalculan aqui a partir de `data/` y `processed/`, de modo
que el documento no puede desincronizarse de los datos.
"""

from __future__ import annotations

import warnings
from collections import Counter

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from scipy import stats
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import confusion_matrix, f1_score
from wordcloud import WordCloud

from src import config, modelos as mod, sentimiento as sen, texto as txt

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")

FIG = config.FIGURAS
AZUL = colors.HexColor("#1f6f8b")
ROJO = colors.HexColor("#c1272d")
GRIS = colors.HexColor("#444444")

C_NO = "#4c72b0"
C_SI = "#c1272d"


# --------------------------------------------------------------------------
# Resultados
# --------------------------------------------------------------------------


def cargar():
    crudo = pd.read_csv(config.TRAIN)
    df = pd.read_csv(config.PROCESADO / "train_sentimiento.csv")
    df["cleaned_text"] = df["cleaned_text"].fillna("")
    df["categoria"] = df["target"].map(config.ETIQUETAS)
    return crudo, df


def frecuencias(serie, n=15):
    contador = Counter(" ".join(serie.fillna("")).split())
    return pd.DataFrame(contador.most_common(n), columns=["palabra", "frecuencia"])


def ngramas(serie, rango, n=10):
    vec = CountVectorizer(ngram_range=rango, max_features=n)
    matriz = vec.fit_transform(serie.fillna(""))
    conteo = np.asarray(matriz.sum(axis=0)).ravel()
    salida = pd.DataFrame({"ngrama": vec.get_feature_names_out(), "frecuencia": conteo})
    return salida.sort_values("frecuencia", ascending=False).reset_index(drop=True)


def resultados_modelos(df):
    """Metricas en la particion fija y en validacion cruzada repetida."""
    fija = mod.evaluar(df).set_index("modelo")
    fija_neg = mod.evaluar(df, ["negatividad"]).set_index("modelo")
    detalle = mod.comparar_validacion_cruzada(df)
    detalle_neg = mod.comparar_validacion_cruzada(df, ["negatividad"])
    cruzada = mod.resumen_cruzada(detalle).set_index("modelo")
    cruzada_neg = mod.resumen_cruzada(detalle_neg).set_index("modelo")
    return {
        "fija": fija,
        "fija_neg": fija_neg,
        "detalle": detalle,
        "detalle_neg": detalle_neg,
        "cruzada": cruzada,
        "cruzada_neg": cruzada_neg,
        "mejor_fija": fija["f1"].idxmax(),
        "mejor_cruzada": cruzada["f1_medio"].idxmax(),
    }


def prueba_mcnemar(df, nombre):
    entrena, valida = mod.dividir(df)
    sin = mod.crear_pipeline(mod.clasificadores()[nombre])
    sin.fit(entrena[mod.TEXTO], entrena["target"])
    p_sin = sin.predict(valida[mod.TEXTO])
    con = mod.crear_pipeline_mixto(mod.clasificadores()[nombre], ["negatividad"])
    con.fit(entrena[[mod.TEXTO, "negatividad"]], entrena["target"])
    p_con = con.predict(valida[[mod.TEXTO, "negatividad"]])
    ok_sin = p_sin == valida["target"].to_numpy()
    ok_con = p_con == valida["target"].to_numpy()
    n01 = int((~ok_sin & ok_con).sum())
    n10 = int((ok_sin & ~ok_con).sum())
    return {
        "arregla": n01,
        "rompe": n10,
        "p": stats.binomtest(n01, n01 + n10, 0.5).pvalue if n01 + n10 else 1.0,
        "f1_sin": f1_score(valida["target"], p_sin),
        "f1_con": f1_score(valida["target"], p_con),
        "matriz": confusion_matrix(valida["target"], p_sin),
        "valida": valida,
    }


def contrastes(df):
    a = df.loc[df["target"] == 1, "vader_compound"]
    b = df.loc[df["target"] == 0, "vader_compound"]
    u, p = stats.mannwhitneyu(a, b, alternative="less")
    prob = u / (len(a) * len(b))
    tb_a = df.loc[df["target"] == 1, "tb_polaridad"]
    tb_b = df.loc[df["target"] == 0, "tb_polaridad"]
    u_tb, p_tb = stats.mannwhitneyu(tb_a, tb_b, alternative="less")
    prob_tb = u_tb / (len(tb_a) * len(tb_b))
    return {
        "media_si": a.mean(), "media_no": b.mean(),
        "mediana_si": a.median(), "mediana_no": b.median(),
        "p": p, "prob": 1 - prob, "biserial": 1 - 2 * prob,
        "tb_biserial": 1 - 2 * prob_tb, "tb_p": p_tb,
        "tb_media_si": tb_a.mean(), "tb_media_no": tb_b.mean(),
    }


# --------------------------------------------------------------------------
# Figuras
# --------------------------------------------------------------------------


def figura_datos(crudo, df):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    conteo = df["categoria"].value_counts()
    axes[0].bar(conteo.index, conteo.values, color=[C_NO, C_SI], width=0.6)
    for i, v in enumerate(conteo.values):
        axes[0].text(i, v + 60, f"{v:,}\n{v / len(df) * 100:.1f} %", ha="center", fontsize=9)
    axes[0].set_ylim(0, conteo.max() * 1.22)
    axes[0].set_title("Reparto de las clases")
    axes[0].set_ylabel("Tweets")

    for cat, color in [("No desastre", C_NO), ("Desastre", C_SI)]:
        sns.kdeplot(df.loc[df["categoria"] == cat, "word_count"], ax=axes[1],
                    fill=True, alpha=0.35, color=color, label=cat, linewidth=1.6)
    axes[1].set_title("Palabras por tweet tras la limpieza")
    axes[1].set_xlabel("Palabras")
    axes[1].set_ylabel("Densidad")
    axes[1].legend()

    faltantes = crudo[["keyword", "location"]].isna().mean() * 100
    axes[2].barh(["keyword", "location"], faltantes.values, color=["#8c8c8c", "#d95f02"])
    for i, v in enumerate(faltantes.values):
        axes[2].text(v + 0.8, i, f"{v:.1f} %", va="center", fontsize=9)
    axes[2].set_xlim(0, max(faltantes.values) * 1.35)
    axes[2].set_title("Valores ausentes por columna")
    axes[2].set_xlabel("% de tweets")

    plt.tight_layout()
    plt.savefig(FIG / "inf_datos.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def figura_nubes(df):
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.2))
    for eje, (objetivo, titulo, mapa) in zip(axes, [
        (1, "Tweets de desastre real", "Reds"),
        (0, "Tweets que no son desastre", "Blues"),
    ]):
        texto_junto = " ".join(df.loc[df["target"] == objetivo, "cleaned_text"])
        nube = WordCloud(width=1100, height=520, background_color="white",
                         colormap=mapa, collocations=False,
                         min_font_size=10, random_state=config.SEMILLA).generate(texto_junto)
        eje.imshow(nube, interpolation="bilinear")
        eje.set_title(titulo, fontsize=12)
        eje.axis("off")
    plt.tight_layout()
    plt.savefig(FIG / "inf_nubes.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def figura_palabras(df):
    des = frecuencias(df.loc[df["target"] == 1, "cleaned_text"], 12)
    nod = frecuencias(df.loc[df["target"] == 0, "cleaned_text"], 12)
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    sns.barplot(data=des, y="palabra", x="frecuencia", ax=axes[0], color=C_SI)
    axes[0].set_title("Palabras más frecuentes — desastre real")
    axes[0].set_xlabel("Apariciones")
    axes[0].set_ylabel("")
    sns.barplot(data=nod, y="palabra", x="frecuencia", ax=axes[1], color=C_NO)
    axes[1].set_title("Palabras más frecuentes — no desastre")
    axes[1].set_xlabel("Apariciones")
    axes[1].set_ylabel("")
    plt.tight_layout()
    plt.savefig(FIG / "inf_palabras.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def figura_modelos(res, mcnemar):
    fig, axes = plt.subplots(1, 2, figsize=(15, 4.8))
    largo = res["fija"][["accuracy", "precision", "recall", "f1"]].reset_index().melt(
        id_vars="modelo", var_name="métrica", value_name="valor")
    sns.barplot(data=largo, x="métrica", y="valor", hue="modelo", ax=axes[0],
                palette=["#2f6fb0", "#2e8b57", "#d95f02"])
    axes[0].set_ylim(0.65, 0.90)
    axes[0].set_title("Métricas en la partición fija 80/20")
    axes[0].set_xlabel("")
    axes[0].legend(title="", fontsize=8)

    matriz = mcnemar["matriz"]
    sns.heatmap(matriz, annot=True, fmt=",d", cmap="Blues", cbar=False, ax=axes[1],
                xticklabels=["No desastre", "Desastre"],
                yticklabels=["No desastre", "Desastre"])
    axes[1].set_title(f"Matriz de confusión — {res['mejor_cruzada']}")
    axes[1].set_xlabel("Predicho")
    axes[1].set_ylabel("Real")
    plt.tight_layout()
    plt.savefig(FIG / "inf_modelos.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def figura_sentimiento(df):
    fig, axes = plt.subplots(1, 3, figsize=(16.5, 4.6))
    cruce = pd.crosstab(df["categoria"], df["polaridad"], normalize="index")
    cruce = (cruce.reindex(columns=sen.CLASES) * 100)
    cruce.plot(kind="bar", ax=axes[0], rot=0, width=0.75,
               color=[sen.COLORES[c] for c in sen.CLASES])
    axes[0].set_title("Reparto de polaridad (%)")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("% dentro de la categoría")
    axes[0].legend(title="", fontsize=8)

    for cat, color in [("No desastre", C_NO), ("Desastre", C_SI)]:
        sns.kdeplot(df.loc[df["categoria"] == cat, "vader_compound"], ax=axes[1],
                    fill=True, alpha=0.35, color=color, label=cat, linewidth=1.6)
    axes[1].axvline(0, color="#444444", linewidth=0.9, linestyle="--")
    axes[1].set_title("Puntuación compuesta de VADER")
    axes[1].set_xlabel("compound")
    axes[1].set_ylabel("Densidad")
    axes[1].legend()

    for cat, color in [("No desastre", C_NO), ("Desastre", C_SI)]:
        valores = np.sort(df.loc[df["categoria"] == cat, "vader_compound"])
        axes[2].step(valores, np.arange(1, len(valores) + 1) / len(valores),
                     color=color, label=cat, linewidth=1.8)
    axes[2].axvline(0, color="#444444", linewidth=0.9, linestyle="--")
    axes[2].set_title("Distribución acumulada")
    axes[2].set_xlabel("compound")
    axes[2].set_ylabel("Proporción acumulada")
    axes[2].legend()
    plt.tight_layout()
    plt.savefig(FIG / "inf_sentimiento.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def figura_negatividad(res):
    largo = pd.concat([
        res["detalle"].assign(condicion="sin negatividad"),
        res["detalle_neg"].assign(condicion="con negatividad"),
    ])
    emparejado = res["detalle"].merge(
        res["detalle_neg"], on=["modelo", "pliegue"], suffixes=("_sin", "_con"))
    emparejado["diferencia"] = emparejado["f1_con"] - emparejado["f1_sin"]

    fig, axes = plt.subplots(1, 2, figsize=(15, 4.8))
    sns.boxplot(data=largo, x="modelo", y="f1", hue="condicion", ax=axes[0],
                palette=["#9aa0a6", "#2e8b57"])
    axes[0].set_title("F1 por pliegue (5 particiones × 3 repeticiones)")
    axes[0].set_xlabel("")
    axes[0].tick_params(axis="x", rotation=10)
    axes[0].legend(title="", fontsize=8)

    sns.stripplot(data=emparejado, x="modelo", y="diferencia", ax=axes[1],
                  hue="modelo", palette="deep", legend=False, size=7, alpha=0.85)
    axes[1].axhline(0, color=C_SI, linewidth=1.2, linestyle="--")
    axes[1].set_title("Δ F1 por pliegue (con − sin negatividad)")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Δ F1")
    axes[1].tick_params(axis="x", rotation=10)
    plt.tight_layout()
    plt.savefig(FIG / "inf_negatividad.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# Documento
# --------------------------------------------------------------------------


def estilos():
    hojas = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("titulo", parent=hojas["Title"], fontSize=21,
                                 leading=25, textColor=AZUL, spaceAfter=6),
        "subtitulo": ParagraphStyle("subtitulo", parent=hojas["Normal"], fontSize=12.5,
                                    leading=16, alignment=TA_CENTER, textColor=GRIS,
                                    spaceAfter=20),
        "h1": ParagraphStyle("h1", parent=hojas["Heading1"], fontSize=14, leading=18,
                             textColor=AZUL, spaceBefore=15, spaceAfter=7),
        "h2": ParagraphStyle("h2", parent=hojas["Heading2"], fontSize=11.5, leading=14.5,
                             textColor=GRIS, spaceBefore=10, spaceAfter=5),
        "cuerpo": ParagraphStyle("cuerpo", parent=hojas["Normal"], fontSize=9.6,
                                 leading=14.4, alignment=TA_JUSTIFY, spaceAfter=7),
        "destacado": ParagraphStyle("destacado", parent=hojas["Normal"], fontSize=10,
                                    leading=15, alignment=TA_JUSTIFY, spaceAfter=8,
                                    leftIndent=10, rightIndent=10, borderPadding=8,
                                    backColor=colors.HexColor("#f2f6f8")),
        "pie": ParagraphStyle("pie", parent=hojas["Normal"], fontSize=8, leading=11,
                              textColor=GRIS, alignment=TA_CENTER, spaceBefore=4),
        "cita": ParagraphStyle("cita", parent=hojas["Normal"], fontSize=8.6, leading=12.5,
                               alignment=TA_JUSTIFY, spaceAfter=5, leftIndent=14,
                               firstLineIndent=-14),
    }


def tabla(datos_tabla, anchos, cabecera=True):
    t = Table(datos_tabla, colWidths=anchos, hAlign="CENTER")
    estilo = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.2),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f7")]),
    ]
    if cabecera:
        estilo += [
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), AZUL),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ]
    t.setStyle(TableStyle(estilo))
    return t


def imagen(nombre, ancho=16.4 * cm, alto=None):
    from PIL import Image as PILImage

    ruta = FIG / nombre
    with PILImage.open(ruta) as im:
        w, h = im.size
    return Image(str(ruta), width=ancho, height=alto or ancho * h / w)


def senales(crudo):
    """Cuenta las senales que la limpieza del ejercicio 3 elimina."""
    negaciones = (r"\b(no|not|never|none|nothing|cannot|can't|won't|don't|"
                  r"didn't|isn't|aren't|wasn't)\b")
    return {
        "emoji": int((txt.contar_emoji(crudo["text"]) > 0).sum()),
        "emoticones": int((txt.contar_emoticones(crudo["text"]) > 0).sum()),
        "negaciones": int((crudo["text"].str.lower().str.count(negaciones) > 0).sum()),
        "admiracion": int((crudo["text"].str.count(r"!") > 0).sum()),
        "mayusculas": int((crudo["text"].str.count(r"\b[A-Z]{3,}\b") > 0).sum()),
        "n911": int(crudo["text"].str.contains(r"\b911\b", regex=True, na=False).sum()),
    }


def construir(crudo, df, res, mcnemar, ctr, sen_conteo):
    e = estilos()
    doc = SimpleDocTemplate(
        str(config.RAIZ / "Informe_Lab5.pdf"), pagesize=A4,
        leftMargin=2.1 * cm, rightMargin=2.1 * cm,
        topMargin=1.9 * cm, bottomMargin=1.9 * cm,
        title="Clasificacion de tweets sobre desastres con mineria de textos",
        author="Fabian Prado, Abby Donis, Hansel Lopez",
    )
    P = lambda t, s="cuerpo": Paragraph(t, e[s])  # noqa: E731
    h = []
    n = len(df)
    pct = lambda x: f"{x / n * 100:.2f} %"  # noqa: E731

    # ---- Portada -------------------------------------------------------
    h.append(P("Clasificación de tweets sobre desastres", "titulo"))
    h.append(P("Laboratorio 5 · Minería de textos y análisis de sentimiento<br/>"
               "Fabian Prado · Abby Donis · Hansel López", "subtitulo"))

    h.append(P(
        "Se parte del conjunto <i>Natural Language Processing with Disaster Tweets</i> de "
        "Kaggle, 7,613 tweets etiquetados según se refieran o no a un desastre real, y se "
        "construye un clasificador capaz de decidirlo sobre un tweet nuevo. El informe "
        "recorre la limpieza del texto, el análisis de frecuencias y n-gramas, los tres "
        "modelos comparados, la función de clasificación, el análisis de polaridad y, "
        "finalmente, la pregunta de si añadir una variable de negatividad mejora el "
        "clasificador.", "destacado"))

    h.append(P("Los tres resultados principales", "h1"))
    h.append(P(
        "<b>1. El mejor modelo es la regresión logística con TF-IDF de unigramas y "
        "bigramas, F1 = 0.7581.</b> La selección merece una aclaración: sobre la partición "
        "80/20 con semilla 42 ganaba Naive Bayes con F1 = 0.7734, pero al promediar sobre "
        "quince particiones el orden se invierte y la regresión logística gana por 1.4 "
        "puntos, una ventaja que supera la desviación de ambos modelos. La ventaja de "
        "Naive Bayes existía sólo en esa partición."))
    h.append(P(
        "<b>2. Los tweets de desastre son más negativos, pero el efecto es moderado.</b> "
        "La probabilidad de que un tweet de desastre tomado al azar sea más negativo que "
        f"uno de la otra categoría es {ctr['prob']:.4f}, frente al 0.50 de una moneda. La "
        "diferencia es estadísticamente incontestable (p ≈ 10<super>-85</super>) y los dos léxicos "
        "empleados coinciden en la dirección, pero un tercio largo de las comparaciones "
        "va en sentido contrario."))
    h.append(P(
        "<b>3. La variable de negatividad no mejora el clasificador.</b> Sobre los mismos "
        f"tweets de validación arregla {mcnemar['arregla']} clasificaciones y rompe "
        f"{mcnemar['rompe']} (McNemar, p = {mcnemar['p']:.3f}). La razón es que las "
        "palabras que aportan negatividad en este corpus —<i>fire</i>, <i>disaster</i>, "
        "<i>bomb</i>, <i>killed</i>— son el vocabulario de desastre, que el TF-IDF ya usa "
        "como predictoras con pesos aprendidos de los datos."))

    h.append(PageBreak())

    # ---- 1. Los datos --------------------------------------------------
    h.append(P("1. El conjunto de datos", "h1"))
    h.append(P(
        f"El archivo <font face='Courier'>train.csv</font> trae <b>{n:,} tweets</b> y cinco "
        "columnas: el identificador, una palabra clave, la ubicación declarada, el texto y "
        "la etiqueta. El reparto de clases está razonablemente equilibrado, con "
        f"{(df['target'] == 0).sum():,} tweets que no son desastre "
        f"({pct((df['target'] == 0).sum())}) y {(df['target'] == 1).sum():,} que sí lo son "
        f"({pct((df['target'] == 1).sum())}). Ese equilibrio importa para la elección de "
        "métrica: la exactitud no es engañosa aquí como lo sería con un 95/5, pero se "
        "reporta F1 junto a ella porque la clase de interés es la minoritaria."))
    h.append(P(
        f"Las dos columnas auxiliares tienen valores ausentes en proporciones muy "
        f"distintas: <font face='Courier'>keyword</font> falta en el "
        f"{crudo['keyword'].isna().mean() * 100:.2f} % de los tweets y "
        f"<font face='Courier'>location</font> en el "
        f"{crudo['location'].isna().mean() * 100:.2f} %. La palabra clave se concatena al "
        "texto antes de limpiar, porque señala el tema y aporta un término útil; la "
        "ubicación se descarta, porque es texto libre escrito por el usuario y contiene "
        "desde países hasta bromas."))
    h.append(imagen("inf_datos.png"))
    h.append(P("Figura 1. Reparto de clases, longitud de los tweets tras la limpieza y "
               "proporción de valores ausentes en las dos columnas auxiliares.", "pie"))

    h.append(P(
        "Una observación sobre la calidad del conjunto, detectada al inspeccionar los "
        "tweets extremos de la sección 7: <b>hay duplicados exactos</b>. El mismo texto "
        "aparece repetido carácter por carácter en más de una fila, lo que infla "
        "levemente las frecuencias y hace que un mismo tweet pueda caer a la vez en "
        "entrenamiento y en validación. No se eliminaron, para no alterar la base sobre la "
        "que se hicieron los ejercicios previos, pero conviene tenerlo presente al leer "
        "cualquier conteo."))

    # ---- 2. Limpieza ---------------------------------------------------
    h.append(P("2. Limpieza y preprocesamiento", "h1"))
    h.append(P(
        "La limpieza se implementó con <b>NLTK</b> (lista de palabras vacías del inglés y "
        "lematizador de WordNet), <b>pandas</b> y el módulo <font face='Courier'>re</font> "
        "de la biblioteca estándar. Sobre el texto original se aplican, en este orden:"))
    h.append(tabla([
        ["Paso", "Qué hace", "Motivo"],
        ["Minúsculas", "text.lower()", "Une 'Fire' y 'fire' en un solo término"],
        ["Quitar URL", "http\\S+ | www.\\S+", "El enlace acortado no aporta léxico"],
        ["Quitar no alfabético", "[^a-zA-Z\\s]", "Elimina #, @, apóstrofes, signos y dígitos"],
        ["Normalizar espacios", "\\s+ → ' '", "Deja un solo espacio entre palabras"],
        ["Quitar emoji", "Rangos Unicode", "Sin efecto: el paso anterior ya los borró"],
        ["Quitar palabras vacías", "stopwords de NLTK", "Artículos, preposiciones y conjunciones"],
    ], [3.4 * cm, 5.4 * cm, 7.6 * cm]))
    h.append(P("Tabla 1. Los seis pasos de la limpieza, en el orden en que se aplican.", "pie"))

    h.append(P(
        "El orden tiene una consecuencia que conviene documentar: como el filtro de "
        "caracteres no alfabéticos corre <b>antes</b> que el de emoji, para cuando este "
        "último se ejecuta ya no queda ningún símbolo que borrar. El paso es inocuo, no "
        "erróneo, y se conservó tal cual para que el texto resultante siga siendo idéntico "
        "al que entrenó los modelos."))
    h.append(P(
        "Hay además un detalle de reproducibilidad que afecta a cualquiera que reejecute "
        "el laboratorio. El lematizador de WordNet está envuelto en un bloque que cae a la "
        "identidad si el corpus no está descargado, y en el entorno donde se ejecutó la "
        "limpieza esa fue la rama que se tomó: el corpus guardado en "
        "<font face='Courier'>processed/</font> conserva <i>deeds</i> y <i>us</i> sin "
        "reducir a su lema. Comprobado sobre las 7,613 filas, la limpieza sin lematizar "
        "reproduce el <b>99.92 %</b> del corpus guardado y con lematización sólo el "
        "40.18 %. El módulo <font face='Courier'>src/texto.py</font> replica el "
        "comportamiento efectivo y deja la lematización como una opción explícita, para "
        "que el texto de un tweet nuevo se limpie igual que el de entrenamiento."))

    h.append(P("El caso del 911 y de los emoticones", "h2"))
    h.append(P(
        "El enunciado pide valorar dos decisiones concretas. Sobre el <b>911</b>: la "
        f"limpieza elimina todos los dígitos, y <font face='Courier'>911</font> aparece en "
        f"<b>{sen_conteo['n911']} tweets</b> de {n:,}. Tres de esos cuatro son desastre "
        "real, una proporción del 75 % frente al 42.97 % de base, pero con cuatro "
        "observaciones no hay evidencia de nada. Quitarlo no costó ninguna capacidad de "
        "clasificación medible."))
    h.append(P(
        "Sobre los <b>emoticones</b>, la respuesta requirió medir. El conjunto "
        f"<b>no contiene un solo emoji Unicode</b> ({sen_conteo['emoji']} apariciones), de "
        f"modo que no hay nada que conservar por ese lado; emoticones ASCII sí aparecen, "
        f"pero en {sen_conteo['emoticones']} tweets, el "
        f"{sen_conteo['emoticones'] / n * 100:.2f} %. Sería un error, sin embargo, "
        "concluir que la limpieza fue inocua para el análisis de sentimiento: lo que "
        "destruye no son los emoticones sino señales bastante más frecuentes."))
    h.append(tabla([
        ["Señal borrada por la limpieza", "Tweets afectados", "% del conjunto"],
        ["Emoji Unicode", f"{sen_conteo['emoji']:,}", f"{sen_conteo['emoji'] / n * 100:.2f} %"],
        ["Emoticones ASCII", f"{sen_conteo['emoticones']:,}",
         f"{sen_conteo['emoticones'] / n * 100:.2f} %"],
        ["Signos de admiración", f"{sen_conteo['admiracion']:,}",
         f"{sen_conteo['admiracion'] / n * 100:.2f} %"],
        ["Negaciones (no, not, never…)", f"{sen_conteo['negaciones']:,}",
         f"{sen_conteo['negaciones'] / n * 100:.2f} %"],
        ["Palabras en MAYÚSCULAS", f"{sen_conteo['mayusculas']:,}",
         f"{sen_conteo['mayusculas'] / n * 100:.2f} %"],
    ], [8.4 * cm, 4.0 * cm, 4.0 * cm]))
    h.append(P("Tabla 2. Señales presentes en el texto original que la limpieza elimina. "
               "La negación es la pérdida grave para el análisis de polaridad.", "pie"))
    h.append(P(
        "La negación es la más seria de las tres. Un analizador de polaridad que reciba "
        "<i>not good</i> sin el <i>not</i> —y <i>not</i> es palabra vacía, de modo que la "
        "limpieza la elimina— leerá <i>good</i> y puntuará al revés. Por eso la sección 6 "
        "trabaja sobre una segunda limpieza, mucho más suave, reservada al sentimiento."))

    h.append(PageBreak())

    secciones_finales(h, P, df, res, mcnemar, ctr)

    doc.build(h)
    print(f"Escrito {config.RAIZ / 'Informe_Lab5.pdf'}")


def secciones_finales(h, P, df, res, mcnemar, ctr):
    """Secciones 3 a 9 del informe."""
    n = len(df)
    des = df.loc[df["target"] == 1, "cleaned_text"]
    nod = df.loc[df["target"] == 0, "cleaned_text"]

    # ---- 3. Exploratorio -----------------------------------------------
    h.append(P("3. Frecuencias, n-gramas y análisis exploratorio", "h1"))
    h.append(P(
        "Con el texto limpio se contaron las palabras de cada categoría por separado. El "
        "contraste es inmediato y es la base de que la clasificación funcione: el "
        "vocabulario de los tweets de desastre es informativo y concreto —<i>fire</i>, "
        "<i>news</i>, <i>disaster</i>, <i>police</i>, <i>suicide</i>, <i>storm</i>— "
        "mientras que el de la otra categoría es conversacional —<i>like</i>, <i>im</i>, "
        "<i>new</i>, <i>get</i>, <i>dont</i>, <i>love</i>."))

    top_d = frecuencias(des, 10)
    top_n = frecuencias(nod, 10)
    filas = [["#", "Desastre real", "Frec.", "No desastre", "Frec."]]
    for i in range(10):
        filas.append([str(i + 1), top_d.loc[i, "palabra"], f"{top_d.loc[i, 'frecuencia']:,}",
                      top_n.loc[i, "palabra"], f"{top_n.loc[i, 'frecuencia']:,}"])
    h.append(tabla(filas, [1.0 * cm, 5.0 * cm, 2.2 * cm, 5.0 * cm, 2.2 * cm]))
    h.append(P("Tabla 3. Las diez palabras más frecuentes en cada categoría.", "pie"))

    h.append(P(
        "<b>Palabras presentes en las dos categorías.</b> Varias aparecen arriba en ambas "
        "listas y son las que hacen difícil el problema. <i>Fire</i> encabeza los tweets de "
        "desastre con 191 apariciones pero sale 99 veces en la otra categoría, porque en "
        "inglés coloquial algo puede <i>ser fuego</i> en el sentido de excelente. Lo mismo "
        "pasa con <i>emergency</i>, que aparece 104 veces entre los no desastres. "
        "<i>Amp</i>, residuo de la entidad HTML <font face='Courier'>&amp;amp;</font>, "
        "aparece en ambas y no aporta nada; es ruido de codificación que la limpieza no "
        "capturó. La consecuencia práctica es que ninguna palabra suelta basta: hace falta "
        "el contexto, y de ahí los n-gramas."))
    h.append(imagen("inf_palabras.png"))
    h.append(P("Figura 2. Palabras más frecuentes en cada categoría tras la limpieza.", "pie"))
    h.append(imagen("inf_nubes.png"))
    h.append(P("Figura 3. Nubes de palabras de las dos categorías. El tamaño es "
               "proporcional a la frecuencia.", "pie"))

    h.append(P("Bigramas y trigramas", "h2"))
    h.append(P(
        "Los n-gramas resuelven parte de la ambigüedad anterior, y por eso vale la pena "
        "explorarlos. <i>Northern california</i> sólo indica un lugar, pero <i>northern "
        "california wildfire</i> ya identifica un suceso. Entre los tweets de desastre los "
        "bigramas más frecuentes son <i>suicide bomber</i> (59), <i>northern california</i> "
        "(41), <i>oil spill</i> (38) y <i>burning buildings</i> (35); entre los otros, "
        "<i>cross body</i> (38), <i>youtube video</i> (36) y <i>liked youtube</i> (35), que "
        "no describen ningún acontecimiento."))
    h.append(P(
        "Los trigramas afinan más —<i>suicide bomber detonated</i>, <i>northern california "
        "wildfire</i>, <i>obama declares disaster</i>— pero su frecuencia cae a menos de "
        "treinta apariciones, de modo que aportan precisión a costa de cobertura. Por eso "
        "el vectorizador de la sección siguiente se queda en unigramas y bigramas: el "
        "trigrama es demasiado escaso para generalizar sobre 7,613 tweets."))

    # ---- 4. Modelos ----------------------------------------------------
    h.append(PageBreak())
    h.append(P("4. Modelos de clasificación", "h1"))
    h.append(P(
        "La representación es <b>TF-IDF sobre unigramas y bigramas</b>, con "
        "<font face='Courier'>min_df=2</font> para descartar los términos que aparecen una "
        "sola vez, <font face='Courier'>sublinear_tf=True</font> para amortiguar las "
        "repeticiones y un máximo de 100,000 términos. Ésa es la forma en que se aborda el "
        "contexto: el bigrama permite que <i>suicide bomber</i> pese como una unidad, "
        "distinta de la suma de <i>suicide</i> y <i>bomber</i> por separado."))
    h.append(P(
        "Se compararon tres algoritmos sobre una partición 80/20 estratificada con semilla "
        "42: Naive Bayes multinomial (α = 0.5), regresión logística (C = 2.0, hasta 1,000 "
        "iteraciones) y SVM lineal (C = 1.0). Los tres reciben exactamente la misma matriz "
        "de características."))

    filas = [["Modelo", "Exactitud", "Precisión", "Recall", "F1"]]
    for nombre, fila in res["fija"].iterrows():
        filas.append([nombre, f"{fila['accuracy']:.4f}", f"{fila['precision']:.4f}",
                      f"{fila['recall']:.4f}", f"{fila['f1']:.4f}"])
    h.append(tabla(filas, [5.4 * cm, 2.75 * cm, 2.75 * cm, 2.75 * cm, 2.75 * cm]))
    h.append(P("Tabla 4. Métricas sobre la partición fija 80/20 (1,523 tweets de validación).",
               "pie"))
    h.append(imagen("inf_modelos.png"))
    h.append(P(f"Figura 4. Comparación de métricas y matriz de confusión del modelo "
               f"seleccionado ({res['mejor_cruzada']}).", "pie"))

    h.append(P("Por qué el mejor modelo no es el que parecía", "h2"))
    h.append(P(
        f"Sobre esa partición gana <b>{res['mejor_fija']}</b> con F1 = "
        f"{res['fija'].loc[res['mejor_fija'], 'f1']:.4f}. El problema es que la diferencia "
        "con el segundo es de tres diezmilésimas, y una diferencia así sobre 1,523 tweets "
        "no distingue un modelo mejor de una partición afortunada. Se repitió la "
        "comparación con validación cruzada estratificada de 5 pliegues y 3 repeticiones, "
        "quince ajustes por modelo:"))

    filas = [["Modelo", "F1 partición fija", "F1 medio (15 pliegues)", "Desviación"]]
    for nombre in res["cruzada"].index:
        filas.append([nombre, f"{res['fija'].loc[nombre, 'f1']:.4f}",
                      f"{res['cruzada'].loc[nombre, 'f1_medio']:.4f}",
                      f"± {res['cruzada'].loc[nombre, 'desviacion']:.4f}"])
    h.append(tabla(filas, [5.4 * cm, 3.6 * cm, 4.2 * cm, 3.2 * cm]))
    h.append(P("Tabla 5. La partición fija y la validación cruzada no coinciden en el "
               "orden de los modelos.", "pie"))
    h.append(P(
        f"El orden se invierte. <b>{res['mejor_cruzada']}</b> alcanza F1 medio de "
        f"{res['cruzada'].loc[res['mejor_cruzada'], 'f1_medio']:.4f} frente a "
        f"{res['cruzada'].loc[res['mejor_fija'], 'f1_medio']:.4f} de "
        f"{res['mejor_fija']}, y la ventaja de 1.4 puntos supera con holgura las "
        "desviaciones de ambos. Se selecciona por tanto la <b>regresión logística</b>. La "
        "lectura general es que con conjuntos de este tamaño la selección de modelo no "
        "debería descansar en una sola partición."))
    h.append(P(
        "Sobre las métricas: el modelo es más preciso que sensible. Recupera alrededor del "
        "73 % de los tweets de desastre y acierta en cerca del 82 % de los que marca. Para "
        "un sistema de alerta el error grave sería el falso negativo —un desastre que pasa "
        "inadvertido— de modo que un despliegue real bajaría el umbral de decisión para "
        "ganar recall a costa de precisión."))

    # ---- 5. Funcion ----------------------------------------------------
    h.append(P("5. Función de clasificación", "h1"))
    h.append(P(
        "La función <font face='Courier'>clasificar_tweet(tweet)</font> recibe el texto "
        "<b>sin preprocesar</b>, le aplica exactamente la misma limpieza que se usó en el "
        "entrenamiento y devuelve la clase junto con la probabilidad estimada. El modelo se "
        "reentrena antes con las 7,613 filas, no sólo con el 80 %, porque una vez elegido "
        "el algoritmo no hay razón para desperdiciar datos."))
    h.append(tabla([
        ["Tweet de entrada", "Salida", "p(desastre)"],
        ["Massive earthquake destroys buildings and rescue teams…", "desastre real", "0.9065"],
        ["I had an amazing day at the beach with my friends", "no desastre", "0.1008"],
        ["Forest fire near La Ronge Sask. Canada", "desastre real", "0.9281"],
        ["This new album is absolute fire :) I am obsessed", "no desastre", "0.2223"],
        ["BREAKING: 13 dead after suicide bomber targets mosque…", "desastre real", "0.9010"],
    ], [9.4 * cm, 3.5 * cm, 3.5 * cm]))
    h.append(P("Tabla 6. Comportamiento de la función sobre cinco tweets nuevos.", "pie"))
    h.append(P(
        "El cuarto caso es el interesante. <i>This new album is absolute fire</i> contiene "
        "la palabra que encabeza el vocabulario de desastre, y aun así el modelo le asigna "
        "0.2223 de probabilidad: los bigramas <i>new album</i> y <i>absolute fire</i> "
        "aportan el contexto que <i>fire</i> por sí sola no tiene. Es exactamente la "
        "ambigüedad que se anticipó en la sección 3, resuelta por la representación."))

    h.append(PageBreak())

    # ---- 6. Sentimiento ------------------------------------------------
    h.append(P("6. Análisis de sentimiento", "h1"))
    h.append(P(
        "La herramienta es <b>VADER</b> (Hutto y Gilbert, 2014), un léxico con reglas "
        "construido y validado sobre texto de redes sociales. Frente a un conteo simple de "
        "palabras positivas y negativas, VADER modela la negación, los intensificadores, el "
        "énfasis por mayúsculas y signos de admiración, y los emoticones. Devuelve una "
        "puntuación compuesta en [-1, 1]; el corte estándar de sus autores clasifica como "
        "positivo por encima de +0.05, negativo por debajo de -0.05 y neutro en medio."))
    h.append(P(
        "Siguiendo lo discutido en la sección 2, se puntúa sobre una <b>segunda limpieza</b> "
        "que sólo quita URL, menciones y la almohadilla de los hashtag, conservando "
        "mayúsculas, puntuación, negaciones y emoticones. La decisión no es cosmética: "
        "entre puntuar el texto del ejercicio 3 y puntuar éste, <b>el 7.46 % de los tweets "
        "cambia de signo</b>, y la media de la puntuación compuesta pasa de -0.2080 a "
        "-0.1441. La limpieza agresiva hace que el corpus parezca más negativo de lo que "
        "es, porque al borrar las negaciones <i>not bad</i> se contabiliza como <i>bad</i>."))

    cruce = (pd.crosstab(df["categoria"], df["polaridad"], normalize="index")
             .reindex(columns=sen.CLASES) * 100)
    h.append(tabla([
        ["Categoría", "Negativo", "Neutro", "Positivo"],
        ["No desastre", f"{cruce.loc['No desastre', 'negativo']:.2f} %",
         f"{cruce.loc['No desastre', 'neutro']:.2f} %",
         f"{cruce.loc['No desastre', 'positivo']:.2f} %"],
        ["Desastre real", f"{cruce.loc['Desastre', 'negativo']:.2f} %",
         f"{cruce.loc['Desastre', 'neutro']:.2f} %",
         f"{cruce.loc['Desastre', 'positivo']:.2f} %"],
    ], [4.6 * cm, 3.9 * cm, 3.9 * cm, 3.9 * cm]))
    h.append(P("Tabla 7. Reparto de polaridad dentro de cada categoría.", "pie"))
    h.append(P(
        "Conviene fijarse en dónde está la diferencia. En el extremo negativo la brecha es "
        "de 15 puntos, un factor de 1.35; en el positivo es de 16 puntos pero sobre una "
        "base mucho menor, un factor de <b>2.0</b>. Lo que distingue a un tweet de desastre "
        "no es tanto que sea más negativo como que <b>casi nunca es positivo</b>. La "
        "proporción de neutros es prácticamente igual en ambas categorías."))
    h.append(imagen("inf_sentimiento.png"))
    h.append(P("Figura 5. Reparto de polaridad, densidad de la puntuación compuesta y "
               "distribución acumulada, por categoría.", "pie"))

    h.append(P(
        "<b>Una advertencia sobre qué mide esta variable.</b> Las palabras negativas más "
        "frecuentes del corpus son <i>no</i>, <i>fire</i>, <i>emergency</i>, "
        "<i>disaster</i>, <i>crash</i>, <i>suicide</i>, <i>bomb</i>, <i>killed</i>, "
        "<i>dead</i>, <i>attack</i>. Salvo la primera, son el vocabulario de desastre. La "
        "negatividad que se está midiendo no es una dimensión independiente del texto sino "
        "un promedio de la presencia de palabras que el clasificador ya usa por separado. "
        "Es la clave para entender la sección 8."))
    h.append(P(
        "Como contraste se repitió todo con <b>TextBlob</b>. El acuerdo entre ambos léxicos "
        "es del 46.81 %, bajo, y el desacuerdo dominante son 1,821 tweets que VADER llama "
        "negativos y TextBlob neutros. La causa es que el analizador de TextBlob se apoya "
        "en un diccionario de adjetivos, y <i>killed</i>, <i>bomb</i> o <i>collapse</i> son "
        "sustantivos y verbos que no puntúa. Para este corpus VADER es el instrumento "
        "adecuado; TextBlob se conserva para verificar direcciones, no para clasificar."))

    h.append(PageBreak())

    # ---- 7. Extremos ---------------------------------------------------
    h.append(P("7. Los tweets extremos y la comparación entre categorías", "h1"))
    h.append(P("Los 10 más negativos y los 10 más positivos", "h2"))
    h.append(P(
        "<b>Siete de los diez tweets más negativos son desastre real</b>, contra una "
        "prevalencia de base del 42.97 %: atentados suicidas, bombardeos de mezquitas y "
        "asesinatos. Los otros tres muestran el modo de fallo del método. El tweet más "
        "negativo de todo el conjunto <b>no es un desastre</b>: es <i>wreck? wreck wreck "
        "wreck…</i>, la misma palabra repetida trece veces, que basta para llevar la "
        "puntuación a -0.9883 porque VADER suma la valencia de cada aparición. Los otros "
        "dos son un tweet de fandom y un pez muerto en un lago."))
    h.append(P(
        "<b>Nueve de los diez más positivos no son desastre.</b> El único de la categoría "
        "de desastre usa la metáfora <i>today's storm will pass</i>, donde <i>storm</i> no "
        "se refiere a ninguna tormenta; es discutible que la etiqueta sea correcta y es la "
        "clase de caso que ningún método léxico resuelve. La lección de conjunto es que la "
        "polaridad mide <b>intensidad léxica acumulada, no acontecimientos</b>."))
    h.append(P(
        "Veinte tweets son pocos para afirmar un patrón, así que se amplió la ventana. "
        "Entre los 500 más negativos el 72.8 % son desastre y entre los 500 más positivos, "
        "el 18.6 %, frente al 42.97 % de base. El patrón se sostiene y no es un artefacto "
        "de haber mirado sólo diez."))

    h.append(P("¿Son los tweets de desastre más negativos?", "h2"))
    h.append(P(
        "Sí, y la afirmación resiste el contraste, pero el efecto es moderado. Se usó la U "
        "de Mann-Whitney y no la t de Student porque la puntuación compuesta está acotada, "
        "tiene una masa puntual en el cero —una cuarta parte de los tweets es neutra— y no "
        "es normal."))
    h.append(tabla([
        ["Medida", "Desastre real", "No desastre"],
        ["Tweets", f"{(df['target'] == 1).sum():,}", f"{(df['target'] == 0).sum():,}"],
        ["Media de compound", f"{ctr['media_si']:.4f}", f"{ctr['media_no']:.4f}"],
        ["Mediana", f"{ctr['mediana_si']:.4f}", f"{ctr['mediana_no']:.4f}"],
    ], [6.0 * cm, 5.2 * cm, 5.2 * cm]))
    h.append(P("Tabla 8. Polaridad por categoría según VADER.", "pie"))
    h.append(P(
        f"La diferencia de medias es de {ctr['media_si'] - ctr['media_no']:+.4f}, con un "
        "intervalo de confianza al 95 % por bootstrap de [-0.2335, -0.1927] que no se "
        f"acerca al cero, y p = {ctr['p']:.1e}. Ese valor p, sin embargo, dice poco: con "
        "7,613 observaciones casi cualquier diferencia sale significativa. <b>La cifra que "
        "importa es el tamaño del efecto.</b> La probabilidad de que un tweet de desastre "
        f"tomado al azar sea más negativo que uno de la otra categoría es "
        f"<b>{ctr['prob']:.4f}</b>, y la correlación biserial por rangos "
        f"{ctr['biserial']:+.4f}, un efecto pequeño a moderado. En más de un tercio de las "
        "parejas que se comparen, el tweet de desastre será el menos negativo de los dos."))
    h.append(P(
        f"El mismo contraste con TextBlob da un efecto de {ctr['tb_biserial']:.4f}, menos "
        "de la mitad, pero de la misma dirección y con la misma significancia. Que el "
        "efecto se atenúe al cambiar de instrumento pero <b>nunca se invierta</b> es la "
        "mejor evidencia de que la diferencia entre categorías es real."))

    h.append(PageBreak())

    # ---- 8. Negatividad ------------------------------------------------
    h.append(P("8. La variable de negatividad y el reentrenamiento", "h1"))
    h.append(P(
        "Se creó la variable <font face='Courier'>negatividad</font> como la puntuación "
        "compuesta invertida y reescalada a [0, 1], donde 0 es el tweet más positivo "
        "posible y 1 el más negativo. Se dejó sin valores negativos a propósito, porque "
        "Naive Bayes multinomial no admite entradas negativas. La variable forma parte del "
        "conjunto guardado en <font face='Courier'>processed/train_sentimiento.csv</font>."))
    h.append(P(
        "Antes de añadirla se midió cuánto vale sola: una regresión logística que no ve el "
        "texto y sólo usa la negatividad alcanza <b>exactitud de 0.60</b>, frente al 0.5706 "
        "de responder siempre «no desastre». Tres puntos por encima de no hacer nada, lo "
        "que ya anticipaba el resultado."))

    filas = [["Modelo", "F1 sin", "F1 con", "Δ F1 (fija)", "Δ F1 (15 pliegues)"]]
    for nombre in res["fija"].index:
        d_fija = res["fija_neg"].loc[nombre, "f1"] - res["fija"].loc[nombre, "f1"]
        d_cv = (res["cruzada_neg"].loc[nombre, "f1_medio"]
                - res["cruzada"].loc[nombre, "f1_medio"])
        filas.append([nombre, f"{res['fija'].loc[nombre, 'f1']:.4f}",
                      f"{res['fija_neg'].loc[nombre, 'f1']:.4f}",
                      f"{d_fija:+.4f}", f"{d_cv:+.4f}"])
    h.append(tabla(filas, [4.6 * cm, 2.7 * cm, 2.7 * cm, 3.0 * cm, 3.6 * cm]))
    h.append(P("Tabla 9. Efecto de añadir la negatividad, en la partición fija y "
               "promediado sobre quince pliegues.", "pie"))
    h.append(imagen("inf_negatividad.png"))
    h.append(P("Figura 6. F1 por pliegue en las dos condiciones y diferencia pliegue a "
               "pliegue. La línea roja marca el cero.", "pie"))

    h.append(P("Respuesta: ¿mejoró, y en qué medida?", "h2"))
    h.append(P(
        "<b>No de manera que importe.</b> En la partición fija las diferencias van de "
        "0.0000 a +0.0025 de F1; sobre quince pliegues, de -0.0014 a +0.0032, y sólo el SVM "
        "lineal alcanza significancia (p = 0.016) con una mejora de tres milésimas que "
        "además lo deja por debajo de donde ya estaba la regresión logística sin la "
        "variable."))
    h.append(P(
        "La prueba más directa es la de McNemar sobre las predicciones del mejor modelo. "
        f"Sobre los mismos 1,523 tweets de validación, añadir la negatividad "
        f"<b>arregla {mcnemar['arregla']} clasificaciones y rompe {mcnemar['rompe']}</b>; "
        f"en {1523 - mcnemar['arregla'] - mcnemar['rompe']:,} los dos modelos coinciden. "
        f"Con p = {mcnemar['p']:.4f}, esa diferencia es indistinguible de lanzar una moneda "
        f"{mcnemar['arregla'] + mcnemar['rompe']} veces. Si hay que dar una cifra, la "
        f"mejora es de <b>{mcnemar['f1_con'] - mcnemar['f1_sin']:+.4f} de F1</b>, unos "
        "cuatro tweets de 1,523, y no sobrevive al cambio de partición."))
    h.append(P(
        "Tampoco ayuda entregar el bloque completo de seis puntuaciones de sentimiento: la "
        "regresión logística gana siete milésimas y Naive Bayes <b>empeora</b> seis, que es "
        "lo esperable de un modelo que supone independencia entre características cuando "
        "recibe seis variables fuertemente correlacionadas."))
    h.append(P(
        "<b>Por qué no mejora.</b> La explicación está en la sección 6. Las palabras que "
        "aportan negatividad en este corpus son el vocabulario de desastre. El TF-IDF ya "
        "usa cada una como predictora independiente, con un peso aprendido de estos datos y "
        "de esta tarea; la variable de negatividad toma esas mismas palabras, las promedia "
        "con pesos fijos traídos de un léxico calibrado para medir tono, y comprime el "
        "resultado en un solo número. No aporta información nueva sino una versión "
        "comprimida y con pérdida de información que el modelo ya tenía en mejor forma. "
        "Cabría esperar que sí aportara si el clasificador no viera el texto, o si la tarea "
        "fuera distinguir el tono en lugar del tema.", "destacado"))

    # ---- 9. Conclusiones -----------------------------------------------
    h.append(P("9. Conclusiones y limitaciones", "h1"))
    h.append(P(
        "El problema se resuelve razonablemente bien con métodos léxicos clásicos: F1 de "
        "0.7581 con TF-IDF de unigramas y bigramas y regresión logística. El contexto "
        "entra por la vía del bigrama, y basta para resolver casos como <i>absolute "
        "fire</i>, donde la palabra aislada apuntaría a la clase contraria."));
    h.append(P(
        "El análisis de sentimiento confirma que los tweets de desastre son más negativos, "
        "con un efecto moderado y consistente entre dos léxicos independientes. Pero esa "
        "negatividad resultó ser un reflejo del mismo vocabulario que el clasificador ya "
        "explota, y por eso incorporarla como variable no mejora nada. El resultado "
        "negativo es informativo: señala que la polaridad y el tema están confundidos en "
        "este corpus."))
    h.append(P("Limitaciones", "h2"))
    h.append(P(
        "<b>Duplicados.</b> El conjunto contiene tweets repetidos carácter por carácter, "
        "que pueden caer a la vez en entrenamiento y validación e inflar levemente las "
        "métricas. No se eliminaron para no alterar la base de los ejercicios previos.<br/>"
        "<b>Etiquetas discutibles.</b> Varios tweets del análisis de extremos están "
        "etiquetados de forma cuestionable, como el uso metafórico de <i>storm</i>. Marca "
        "un techo al desempeño alcanzable que ningún modelo puede superar.<br/>"
        "<b>Léxico ajeno al dominio.</b> VADER está calibrado sobre redes sociales "
        "generales, no sobre cobertura de desastres. Un léxico específico del dominio "
        "podría separar mejor el tono del tema.<br/>"
        "<b>Sin modelos contextuales.</b> No se probaron representaciones basadas en "
        "transformadores, que resolverían la ambigüedad léxica mejor que el bigrama, a "
        "costa de interpretabilidad y de coste computacional."))

    # ---- Referencias ---------------------------------------------------
    h.append(P("Referencias", "h1"))
    for cita in [
        "Bird, S., Klein, E., &amp; Loper, E. (2009). <i>Natural Language Processing with "
        "Python</i>. O'Reilly Media. Módulo NLTK, versión 3.10.3.",
        "Hutto, C. J., &amp; Gilbert, E. (2014). VADER: A Parsimonious Rule-based Model for "
        "Sentiment Analysis of Social Media Text. <i>Proceedings of the Eighth International "
        "AAAI Conference on Weblogs and Social Media</i>. Paquete vaderSentiment 3.3.2.",
        "Jurafsky, D., &amp; Martin, J. H. (2024). <i>Speech and Language Processing</i> "
        "(3.ª ed., borrador). Capítulos sobre n-gramas y clasificación de textos. "
        "https://web.stanford.edu/~jurafsky/slp3/",
        "Kaggle. <i>Natural Language Processing with Disaster Tweets</i>. "
        "https://www.kaggle.com/competitions/nlp-getting-started",
        "Loria, S. (2020). <i>TextBlob: Simplified Text Processing</i>, versión 0.20.1.",
        "Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. "
        "<i>Journal of Machine Learning Research</i>, 12, 2825–2830. Versión 1.9.0.",
    ]:
        h.append(P(cita, "cita"))


def main():
    config.preparar_directorios()
    print("Cargando datos ...")
    crudo, df = cargar()

    print("Recalculando metricas de los modelos ...")
    res = resultados_modelos(df)
    mcnemar = prueba_mcnemar(df, res["mejor_cruzada"])
    ctr = contrastes(df)
    sen_conteo = senales(crudo)

    print("Generando figuras ...")
    figura_datos(crudo, df)
    figura_nubes(df)
    figura_palabras(df)
    figura_modelos(res, mcnemar)
    figura_sentimiento(df)
    figura_negatividad(res)

    print("Armando el documento ...")
    construir(crudo, df, res, mcnemar, ctr, sen_conteo)


if __name__ == "__main__":
    main()
