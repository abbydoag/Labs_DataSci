"""Genera Informe_Lab4_Parte2.pdf, el informe de la segunda parte del laboratorio.

A diferencia del informe de la Parte 1, dirigido a publico no tecnico, este
recoge los resultados de los modelos de aprendizaje automatico con el detalle
que pide el enunciado. Se corre despues de los cuadernos 7 al 14:

    .venv/bin/python informe_parte2.py
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
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

from src import config, datos as dts, ml

FIG = config.FIGURAS
AZUL = colors.HexColor("#1f6f8b")
ROJO = colors.HexColor("#c1272d")
GRIS = colors.HexColor("#444444")

COLOR_MODELO = {
    "Regresión Logística": "#2f6fb0",
    "Random Forest": "#2e8b57",
    "XGBoost": "#d95f02",
}

CORTES = [0.0, 0.01, 0.10, 0.50, 1.0]
ETIQUETAS_PROB = ["Muy baja", "Baja", "Alta", "Muy alta"]
CMAP_PROB = ListedColormap(["#2c7bb6", "#abd9e9", "#fdae61", "#d7191c"])
CMAP_PROB.set_bad((0, 0, 0, 0))
NORMA_PROB = BoundaryNorm(CORTES, CMAP_PROB.N)


# --------------------------------------------------------------------------
# Resultados
# --------------------------------------------------------------------------


def cargar():
    """Reune lo que dejaron guardado los cuadernos 9 al 13."""
    validacion = joblib.load(config.MODELOS / "validacion_espacial_temporal.joblib")
    generalizacion = joblib.load(config.MODELOS / "generalizacion_lagos.joblib")
    interpretabilidad = joblib.load(config.MODELOS / "interpretabilidad.joblib")
    guardado = joblib.load(config.MODELOS / "modelos_division_aleatoria.joblib")
    predicciones = pd.read_parquet(config.DERIVADO / "predicciones_mapa.parquet")
    return validacion, generalizacion, interpretabilidad, guardado, predicciones


def metricas_division_aleatoria(guardado):
    """Recalcula la tabla del cuaderno 9 sobre el mismo conjunto de prueba.

    Las metricas no se guardaron en el joblib, pero si los modelos y los indices
    del conjunto de prueba, asi que reproducirlas cuesta una prediccion.
    """
    from sklearn.metrics import fbeta_score

    tabla_datos = pd.read_parquet(config.DERIVADO / "dataset_ml.parquet")
    tabla_datos[ml.RESPUESTA] = ml.variable_respuesta(tabla_datos)
    tabla_datos = ml.caracteristicas(tabla_datos)

    prueba = tabla_datos.loc[guardado["idx_prueba"]]
    X, y = prueba[ml.PREDICTORAS], prueba[ml.RESPUESTA]

    filas = {}
    for nombre, modelo in guardado["modelos"].items():
        entrada = guardado["escalador"].transform(X) if guardado["usa_escala"][nombre] else X
        prob = modelo.predict_proba(entrada)[:, 1]
        pred = (prob >= guardado["umbrales"][nombre]).astype(int)
        m = ml.metricas(y, pred, prob)
        m["F2"] = fbeta_score(y, pred, beta=2, zero_division=0)
        m["umbral"] = guardado["umbrales"][nombre]
        filas[nombre] = m

    return pd.DataFrame(filas).T


# --------------------------------------------------------------------------
# Figuras
# --------------------------------------------------------------------------


def figura_modelos(tabla_modelos):
    fig, eje = plt.subplots(figsize=(9.2, 3.9))
    metricas = ["Precision", "Recall", "F1", "F2", "PR-AUC"]
    ancho = 0.26

    for k, nombre in enumerate(tabla_modelos.index):
        valores = [tabla_modelos.loc[nombre, m] for m in metricas]
        barras = eje.bar(np.arange(len(metricas)) + (k - 1) * ancho, valores, ancho,
                         label=nombre, color=COLOR_MODELO[nombre], alpha=0.92)
        eje.bar_label(barras, fmt="%.3f", fontsize=6.6, padding=2)

    eje.set_xticks(np.arange(len(metricas)), metricas, fontsize=9)
    eje.set_ylim(0, 1.14)
    eje.set_ylabel("Conjunto de prueba")
    eje.legend(fontsize=8, ncol=3, loc="upper center")
    eje.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    fig.savefig(FIG / "p2_modelos.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def figura_validacion(pivote):
    fig, eje = plt.subplots(figsize=(9.2, 3.6))
    estrategias = ["Aleatoria", "Espacial", "Temporal"]
    tonos = ["#8fb8de", "#e8a33d", "#b05c9a"]
    ancho = 0.26

    orden = ["Regresión Logística", "Random Forest", "XGBoost"]
    for k, estrategia in enumerate(estrategias):
        valores = [pivote.loc[m, estrategia] for m in orden]
        barras = eje.bar(np.arange(3) + (k - 1) * ancho, valores, ancho,
                         label=estrategia, color=tonos[k], alpha=0.92)
        eje.bar_label(barras, fmt="%.3f", fontsize=6.8, padding=2)

    eje.set_xticks(np.arange(3), ["Reg. Logística", "Random Forest", "XGBoost"], fontsize=9)
    eje.set_ylabel("F2")
    eje.set_ylim(0, 1.12)
    eje.legend(fontsize=8, ncol=3, loc="upper center")
    eje.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    fig.savefig(FIG / "p2_validacion.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def figura_generalizacion(tabla_gen):
    sub = tabla_gen[tabla_gen["predictoras"] == "Transferible"].set_index("corrida")
    orden = ["Atitlan → Atitlan", "Amatitlan → Amatitlan",
             "Atitlan → Amatitlan", "Amatitlan → Atitlan"]
    sub = sub.loc[orden]

    fig, eje = plt.subplots(figsize=(9.2, 3.7))
    ancho = 0.36
    pos = np.arange(len(orden))
    b1 = eje.bar(pos - ancho / 2, sub["F2"], ancho, label="F2", color="#1f6f8b", alpha=0.92)
    b2 = eje.bar(pos + ancho / 2, sub["PR-AUC"], ancho, label="PR-AUC", color="#c1272d", alpha=0.92)
    eje.bar_label(b1, fmt="%.3f", fontsize=6.8, padding=2)
    eje.bar_label(b2, fmt="%.3f", fontsize=6.8, padding=2)

    eje.set_xticks(pos, [o.replace(" → ", "\n→ ") for o in orden], fontsize=8)
    eje.set_ylim(0, 1.14)
    eje.axvline(1.5, color="#888", linestyle="--", linewidth=1)
    eje.text(0.5, 1.06, "dentro del mismo lago", ha="center", fontsize=7.5, color="#666")
    eje.text(2.5, 1.06, "transferencia entre lagos", ha="center", fontsize=7.5, color="#666")
    eje.legend(fontsize=8, loc="lower right")
    eje.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    fig.savefig(FIG / "p2_generalizacion.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def figura_importancia(interpretabilidad):
    shap_medio = interpretabilidad["shap_medio"].sort_values()
    por_lago = interpretabilidad["por_lago"]

    fig, ejes = plt.subplots(1, 2, figsize=(10.4, 4.6))

    ejes[0].barh(shap_medio.index, shap_medio.values, color="#d95f02", alpha=0.9)
    ejes[0].set_xlabel("SHAP medio absoluto (log-odds)")
    ejes[0].set_title("Influencia global", loc="left", fontsize=10, fontweight="bold")
    ejes[0].tick_params(labelsize=7.5)

    principales = interpretabilidad["shap_medio"].head(6).index[::-1]
    pos = np.arange(len(principales))
    ejes[1].barh(pos - 0.2, por_lago.loc[principales, "Atitlan"], 0.4,
                 label="Atitlán", color="#1f6f8b", alpha=0.9)
    ejes[1].barh(pos + 0.2, por_lago.loc[principales, "Amatitlan"], 0.4,
                 label="Amatitlán", color="#c1272d", alpha=0.9)
    ejes[1].set_yticks(pos, principales, fontsize=7.5)
    ejes[1].set_xlabel("SHAP medio absoluto")
    ejes[1].set_title("El modelo no usa lo mismo en cada lago", loc="left",
                      fontsize=10, fontweight="bold")
    ejes[1].legend(fontsize=8)

    for eje in ejes:
        eje.grid(alpha=0.25, axis="x")
    fig.tight_layout()
    fig.savefig(FIG / "p2_importancia.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def figura_mapas(predicciones):
    """Mapa predictivo de la fecha mas afectada de cada lago."""
    fig, ejes = plt.subplots(1, 2, figsize=(10.6, 4.4))

    for eje, lago in zip(ejes, ["Atitlan", "Amatitlan"]):
        sub_lago = predicciones[predicciones["lago"] == lago]
        peor = sub_lago.groupby("fecha")[ml.RESPUESTA].mean().idxmax()
        sub = sub_lago[sub_lago["fecha"] == peor]

        capas, _ = dts.indices_escena(lago, peor.strftime("%Y-%m-%d"))
        rejilla = np.full(capas["chl_agua"].shape, np.nan, dtype=np.float32)
        rejilla[sub["fila"].values, sub["columna"].values] = sub["prob"].values

        eje.imshow(rejilla, cmap=CMAP_PROB, norm=NORMA_PROB, interpolation="nearest")
        eje.set_title(f"{config.NOMBRE_LARGO[lago]} — {peor:%Y-%m-%d}",
                      loc="left", fontsize=10, fontweight="bold")
        eje.set_xticks([])
        eje.set_yticks([])

    barra = fig.colorbar(plt.cm.ScalarMappable(norm=NORMA_PROB, cmap=CMAP_PROB), ax=ejes,
                         fraction=0.03, pad=0.02, spacing="uniform",
                         ticks=[0.005, 0.055, 0.3, 0.75])
    barra.ax.set_yticklabels(ETIQUETAS_PROB, fontsize=8)
    barra.set_label("Probabilidad de alta presencia", fontsize=8)

    fig.savefig(FIG / "p2_mapas.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def figura_error(predicciones):
    """Donde se equivoca el modelo, en funcion de la clorofila real."""
    tabla_datos = pd.read_parquet(
        config.DERIVADO / "dataset_ml.parquet", columns=["chl"]
    )
    junto = predicciones.reset_index(drop=True).join(tabla_datos.reset_index(drop=True))
    junto["banda"] = pd.cut(
        junto["chl"], bins=[0, 2, 5, 8, 9.5, 10.5, 13, 20, 50, np.inf],
        labels=["0-2", "2-5", "5-8", "8-9.5", "9.5-10.5", "10.5-13", "13-20", "20-50", ">50"],
    )
    tasa = junto.groupby("banda", observed=True).apply(
        lambda s: 100 * (s["pred"] != s[ml.RESPUESTA]).mean(), include_groups=False
    )

    fig, eje = plt.subplots(figsize=(8.6, 3.4))
    barras = eje.bar(range(len(tasa)), tasa.values, color="#8b1a1a", alpha=0.88)
    eje.bar_label(barras, fmt="%.2f%%", fontsize=7, padding=2)
    eje.axvspan(3.5, 5.5, color="#f9a03f", alpha=0.18)
    eje.set_xticks(range(len(tasa)), tasa.index.astype(str), fontsize=8)
    eje.set_xlabel("Clorofila-a real del píxel (µg/L)")
    eje.set_ylabel("% mal clasificado")
    eje.set_ylim(0, max(tasa.values) * 1.25)
    eje.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    fig.savefig(FIG / "p2_error.png", dpi=150, bbox_inches="tight")
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


def construir(tabla_modelos, validacion, generalizacion, interpretabilidad,
              predicciones):
    e = estilos()
    doc = SimpleDocTemplate(
        str(config.BASE / "Informe_Lab4_Parte2.pdf"), pagesize=A4,
        leftMargin=2.1 * cm, rightMargin=2.1 * cm,
        topMargin=1.9 * cm, bottomMargin=1.9 * cm,
        title="Modelos de aprendizaje automatico para detectar cianobacteria",
        author="Fabian Prado, Abby Donis, Hansel Lopez",
    )

    P = lambda txt, est="cuerpo": Paragraph(txt, e[est])  # noqa: E731
    h = []

    # ---- Portada -------------------------------------------------------
    h.append(P("Detección de cianobacteria con aprendizaje automático", "titulo"))
    h.append(P("Laboratorio 4 · Parte 2 — Lagos de Atitlán y Amatitlán<br/>"
               "Fabian Prado · Abby Donis · Hansel López", "subtitulo"))

    h.append(P(
        "La Parte I de este laboratorio reconstruyó 18 meses de historia de los lagos de "
        "Atitlán y Amatitlán a partir de 22 imágenes de Sentinel-2, y estimó la "
        "concentración de clorofila-a con el script CyanoLakes. Esta segunda parte "
        "convierte esos rasters en un problema de clasificación: dado el espectro de un "
        "píxel de agua, ¿supera o no el nivel de vigilancia de 10 µg/L que define la "
        "Organización Mundial de la Salud?", "destacado"))

    h.append(P(
        "El conjunto de datos tiene <b>3,759,121 observaciones</b>, una por cada píxel de "
        "agua válida en cada una de las 22 escenas, con sus coordenadas en UTM 15N, su "
        "fecha, su lago, diez bandas espectrales y los índices derivados. De ellas, 44,349 "
        "—el 1.18 %— superan el umbral."))

    h.append(P("El punto de partida: qué no puede ser predictor", "h1"))
    h.append(P(
        "El enunciado advierte que una variable usada directa o indirectamente para "
        "construir la respuesta no puede incluirse después como predictora. En este "
        "problema esa advertencia no es una formalidad, y conviene empezar por ahí porque "
        "condiciona todo lo demás."))
    h.append(P(
        "La clorofila se estima con un polinomio del NDCI, y el NDCI es "
        "(B05 − B04)/(B05 + B04). Al despejar la raíz real de ese polinomio en 10 µg/L se "
        "obtiene NDCI = 0.2413494, de modo que la etiqueta equivale exactamente a "
        "<b>B05 &gt; 1.636 · B04</b>: una sola desigualdad lineal entre dos columnas del "
        "conjunto de datos. Se comprobó sobre los 3.76 millones de filas y la regla "
        "reproduce la etiqueta en el 100.0000 % de los casos."))
    h.append(P(
        "Un modelo que reciba B04 y B05 no predice nada: recalcula la respuesta. Por eso "
        "quedan fuera esas dos bandas, el NDCI y la clorofila, y con ellas el NDVI y el FAI, "
        "que también se calculan con B04. Quedan <b>16 predictoras</b>: siete bandas, seis "
        "índices construidos solo con bandas permitidas y tres características espaciales. "
        "La pieza clave es B07, borde rojo a 783 nm, que no interviene en ninguna fórmula "
        "de la respuesta y aporta señal de clorofila obtenida de forma independiente."))

    h.append(P("Los tres modelos y su evaluación", "h1"))
    h.append(P(
        "Se entrenaron Regresión Logística, Random Forest y XGBoost sobre una división "
        "70/30. El conjunto de entrenamiento se dividió a su vez para elegir el umbral de "
        "decisión sobre datos con la prevalencia real: como el ajuste se hace sobre una "
        "muestra equilibrada al 50 % de positivos, las probabilidades salen calibradas para "
        "un mundo que no existe y el corte de 0.5 dispara alarmas por todas partes. Los "
        "umbrales elegidos quedaron entre 0.92 y 0.99."))

    filas = [["Modelo", "Accuracy", "Precisión", "Recall", "F1", "F2", "PR-AUC", "Umbral"]]
    for nombre in tabla_modelos.index:
        f = tabla_modelos.loc[nombre]
        filas.append([nombre.replace("Regresión Logística", "Reg. Logística"),
                      f"{f['Accuracy']:.4f}", f"{f['Precision']:.4f}", f"{f['Recall']:.4f}",
                      f"{f['F1']:.4f}", f"{f['F2']:.4f}", f"{f['PR-AUC']:.4f}",
                      f"{f['umbral']:.2f}"])
    h.append(tabla(filas, [3.1 * cm, 1.9 * cm, 1.9 * cm, 1.8 * cm, 1.6 * cm, 1.6 * cm,
                           1.8 * cm, 1.5 * cm]))
    h.append(Spacer(1, 6))
    h.append(Image(str(FIG / "p2_modelos.png"), width=16.4 * cm, height=6.9 * cm))
    h.append(P("Comparación de los tres modelos sobre el conjunto de prueba. El accuracy y "
               "el ROC-AUC se omiten a propósito del gráfico: con una clase al 1.18 % ambos "
               "se acercan a 1 casi por construcción.", "pie"))

    h.append(P("Por qué se compara con F2 y no con F1", "h2"))
    h.append(P(
        "Los dos errores no cuestan lo mismo. Un <b>falso negativo</b> deja una floración "
        "sin detectar: no se muestrea, no se avisa y el lago se sigue usando para pesca, "
        "riego, consumo y recreación. Las cianobacterias del género <i>Microcystis</i>, "
        "dominante en lagos eutróficos tropicales, producen microcistinas, hepatotoxinas "
        "que no se eliminan hirviendo el agua. Un <b>falso positivo</b> manda un equipo a "
        "muestrear una zona limpia: cuesta dinero y, si el aviso se hace público, daña al "
        "turismo y a la pesca sin motivo."))
    h.append(P(
        "La diferencia decisiva es que un falso positivo se corrige y un falso negativo no "
        "se entera. La zona marcada por error se visita, se mide y se descarta en cuestión "
        "de días; la floración no detectada no genera ninguna señal que permita corregirla. "
        "Por eso la métrica de comparación es el recall, y el compromiso se cierra con F2, "
        "que lo pondera cuatro veces por encima de la precisión. Es el mismo razonamiento "
        "con el que la OMS define el nivel de 10 µg/L como <i>vigilancia</i> y no como "
        "<i>alerta</i>."))

    h.append(PageBreak())

    # ---- Validacion ----------------------------------------------------
    h.append(P("Validación espacial y temporal", "h1"))
    h.append(P(
        "La división aleatoria reparte píxeles sueltos, y dos píxeles de agua separados por "
        "20 metros son casi el mismo dato: comparten temperatura, profundidad, exposición al "
        "viento y la misma masa de agua. Para medir cuánto de aquel resultado era memoria se "
        "repitió el experimento reteniendo bloques espaciales de 1 km × 1 km completos, y "
        "después fechas completas."))
    h.append(P(
        "Los rasters ya venían en EPSG:32615 desde la descarga de la Parte I, así que la "
        "reproyección que pide el enunciado no hizo falta. Con bloques de 1 km resultan 232 "
        "bloques en Atitlán y 58 en Amatitlán, de los que 65 y 37 contienen positivos: "
        "suficiente para cinco particiones."))

    pivote = validacion["pivote_f2"]
    filas = [["Modelo", "F2 aleatoria", "F2 espacial", "Δ", "F2 temporal", "Δ"]]
    for nombre in ["Regresión Logística", "Random Forest", "XGBoost"]:
        f = pivote.loc[nombre]
        filas.append([nombre.replace("Regresión Logística", "Reg. Logística"),
                      f"{f['Aleatoria']:.4f}", f"{f['Espacial']:.4f}",
                      f"{f['Δ espacial']:+.4f}", f"{f['Temporal']:.4f}",
                      f"{f['Δ temporal']:+.4f}"])
    h.append(tabla(filas, [3.4 * cm, 2.6 * cm, 2.5 * cm, 2.0 * cm, 2.6 * cm, 2.0 * cm]))
    h.append(Spacer(1, 6))
    h.append(Image(str(FIG / "p2_validacion.png"), width=16.4 * cm, height=6.4 * cm))
    h.append(P("F2 de cada modelo bajo las tres particiones.", "pie"))

    h.append(P(
        "<b>Las dos caídas son de naturaleza distinta.</b> La espacial casi no mueve la "
        "media —XGBoost pierde 0.0084— pero quintuplica la dispersión entre particiones, de "
        "0.0020 a 0.0102 de desviación. El desempeño pasa a depender de qué zona toque "
        "predecir, y la validación aleatoria no permitía verlo. La temporal mueve las dos "
        "cosas: XGBoost pierde 0.1263 y el rango entre la mejor y la peor partición se abre "
        "a 0.2580."))
    h.append(P(
        "<b>Random Forest se desploma en validación temporal</b>, y el detalle importa: su "
        "precisión se mantiene en 0.7910 y lo que se hunde es el recall, de 0.9674 a 0.6101. "
        "No se vuelve impreciso, se vuelve tímido. Es un fallo de calibración y no de "
        "discriminación: los votos promediados de un bosque se concentran en un rango "
        "estrecho de probabilidad, así que el umbral aprendido en unas fechas corta de más "
        "en otras. En operación habría que recalibrar el umbral con cada escena nueva."))
    h.append(P(
        "La causa del desplome temporal se ve en el reparto de fechas: una de las cinco "
        "particiones retiene 21,865 positivos porque se lleva el 19 de junio de 2026, la "
        "peor floración de la serie. Entrenar sin esa fecha es entrenar sobre un lago mucho "
        "más limpio del que hay que predecir. No es solo autocorrelación temporal: es el "
        "deterioro progresivo de Amatitlán durante 2026 que ya había documentado la Parte I."))

    h.append(P("Generalización entre lagos", "h1"))
    h.append(P(
        "Antes de correr los experimentos hubo que resolver algo que los habría invalidado. "
        "Entre las predictoras están las coordenadas x e y, y los dos lagos ocupan rangos "
        "disjuntos separados por 47 km. Un árbol entrenado en Atitlán aprende cortes del "
        "tipo x &lt; 695,000 y todos los píxeles de Amatitlán caen del mismo lado de todos "
        "ellos: el modelo los manda a una sola hoja y devuelve una constante. Quitar x e y "
        "sube el recall del Experimento A de 0.2662 a 0.5988."))

    sub_gen = generalizacion["tabla"]
    sub_gen = sub_gen[sub_gen["predictoras"] == "Transferible"].set_index("corrida")
    filas = [["Entrena → evalúa", "Recall", "Precisión", "F2", "PR-AUC"]]
    for corrida in ["Atitlan → Atitlan", "Amatitlan → Amatitlan",
                    "Atitlan → Amatitlan", "Amatitlan → Atitlan"]:
        f = sub_gen.loc[corrida]
        filas.append([corrida, f"{f['Recall']:.4f}", f"{f['Precision']:.4f}",
                      f"{f['F2']:.4f}", f"{f['PR-AUC']:.4f}"])
    h.append(tabla(filas, [5.2 * cm, 2.4 * cm, 2.6 * cm, 2.2 * cm, 2.4 * cm]))
    h.append(Spacer(1, 6))
    h.append(Image(str(FIG / "p2_generalizacion.png"), width=16.4 * cm, height=6.6 * cm))
    h.append(P("Las dos primeras columnas entrenan y evalúan en el mismo lago; las dos "
               "últimas transfieren.", "pie"))

    h.append(P(
        "<b>El resultado inesperado está en la última fila.</b> Entrenar en Amatitlán y "
        "evaluar en Atitlán da F2 de 0.6873, mejor que entrenar y evaluar dentro de Atitlán "
        "(0.5021). No es contradictorio: Atitlán tiene 1,324 píxeles positivos en 18 meses "
        "y un modelo entrenado ahí ve unos 900 ejemplos de floración en total, mientras que "
        "Amatitlán aporta 43,025, treinta y dos veces más. La cantidad de ejemplos de la "
        "clase rara pesa más que la afinidad entre dominios."))
    h.append(P(
        "Lo que se transfiere entre lagos es el <b>ordenamiento</b> —el ROC-AUC se mantiene "
        "entre 0.9369 y 0.9963 en los cruces— y lo que no se transfiere es la "
        "<b>calibración</b>: la precisión cae hasta 0.39 y el umbral óptimo salta de 0.67 a "
        "0.99 según el lago. Es el mismo diagnóstico que dejó la validación temporal."))

    h.append(PageBreak())

    # ---- Interpretabilidad ---------------------------------------------
    h.append(P("Qué aprendió el modelo", "h1"))
    h.append(Image(str(FIG / "p2_importancia.png"), width=16.4 * cm, height=7.2 * cm))
    h.append(P("Influencia de cada variable medida con SHAP, y su reparto por lago.", "pie"))

    h.append(P(
        "Las direcciones de los efectos son las que la óptica del agua predice, lo que "
        "indica que el modelo aprendió física y no correlaciones espurias. <b>B07 alto "
        "empuja hacia alta presencia</b> (+4.675 de log-odds) y bajo hacia baja (−4.406): es "
        "el pico de reflectancia que levantan las células en el borde rojo, donde el agua "
        "limpia no refleja casi nada. <b>La razón azul/verde va al revés</b> (+4.611 en "
        "valores bajos, −3.283 en altos) porque la clorofila absorbe azul y refleja verde; "
        "es el principio de los algoritmos de color del océano que se usan desde los años "
        "setenta, y el modelo lo redescubrió sin que nadie se lo dijera."))
    h.append(P(
        "<b>El modelo no usa las mismas variables en los dos lagos.</b> En Atitlán se apoya "
        "en el borde rojo (SHAP 4.185) y el índice ndmi casi no pesa (0.494); en Amatitlán "
        "el borde rojo baja a 3.314 y ndmi se triplica hasta 1.561. La explicación es el "
        "sedimento que descarga el río Villalobos: sobre agua turbia el borde rojo se vuelve "
        "ambiguo y hace falta el contraste infrarrojo para separar biomasa de barro. Coincide "
        "con lo que la Parte I había encontrado por otro camino, que el NDWI predice la "
        "clorofila en Atitlán (r = −0.955) y no en Amatitlán (r = −0.348, p = 0.29)."))
    h.append(P(
        "Un resultado negativo que también informa: las variables espaciales apenas se usan. "
        "Barajar x, y o la distancia a la orilla cuesta entre 0.0001 y 0.0003 de PR-AUC. Eso "
        "explica por qué la validación espacial apenas degradó el desempeño mientras la "
        "temporal lo hundió: un modelo que no mira la posición no pierde nada cuando se le "
        "retiene una zona entera."))

    h.append(P("Mapas predictivos", "h1"))
    h.append(P(
        "Las probabilidades se calcularon <b>fuera de muestra por bloques espaciales</b>: "
        "cada píxel recibe la suya de un modelo que nunca vio ningún píxel de su bloque. "
        "Pintar el mapa con el modelo entrenado sobre todo el conjunto habría mostrado lo "
        "bien que recuerda, no lo bien que predice. Además se corrigieron a la prevalencia "
        "real con la fórmula estándar de muestreo por casos y controles, sin lo cual todo lo "
        "interesante ocurría entre 0.98 y 1.00 y una escala de cuatro categorías no "
        "distinguía nada."))
    h.append(Image(str(FIG / "p2_mapas.png"), width=16.4 * cm, height=6.8 * cm))
    h.append(P("Probabilidad de alta presencia en la fecha más afectada de cada lago.", "pie"))

    filas = [["Categoría", "Probabilidad", "Píxeles", "% del total", "% positivos reales"]]
    for etiqueta, rango, n, pct, pos in [
        ("Muy baja", "< 0.01", "3,691,057", "98.19 %", "0.00 %"),
        ("Baja", "0.01 – 0.10", "9,646", "0.26 %", "3.86 %"),
        ("Alta", "0.10 – 0.50", "7,640", "0.20 %", "13.98 %"),
        ("Muy alta", "> 0.50", "50,778", "1.35 %", "84.15 %"),
    ]:
        filas.append([etiqueta, rango, n, pct, pos])
    h.append(tabla(filas, [2.8 * cm, 3.0 * cm, 3.0 * cm, 2.8 * cm, 3.6 * cm]))
    h.append(P("La última columna comprueba que la escala significa algo: la proporción de "
               "píxeles que de verdad superan el umbral crece de forma monótona.", "pie"))

    h.append(PageBreak())

    h.append(P("Dónde se equivoca el modelo", "h1"))
    h.append(Image(str(FIG / "p2_error.png"), width=15.6 * cm, height=6.1 * cm))
    h.append(P("Porcentaje de píxeles mal clasificados según su clorofila real. La franja "
               "sombreada rodea el umbral de 10 µg/L.", "pie"))

    h.append(P(
        "El error es prácticamente <b>cero en los dos extremos y casi una moneda al aire en "
        "la banda que rodea al umbral</b>: 44.43 % entre 9.5 y 10.5 µg/L, frente a 0.00 % por "
        "debajo de 2 y 0.21 % entre 20 y 50. Esto no es un defecto del modelo sino una "
        "consecuencia inevitable de haber binarizado una variable continua. Un píxel con 9.9 "
        "µg/L y otro con 10.1 tienen espectros indistinguibles —la diferencia está por debajo "
        "del ruido radiométrico del sensor— pero la etiqueta los separa en clases opuestas."))
    h.append(P(
        "La consecuencia práctica es tranquilizadora: las floraciones que importan desde el "
        "punto de vista sanitario, las que se acercan al nivel de alerta de 50 µg/L, caen en "
        "las bandas donde el modelo no se equivoca casi nunca. El modelo falla justo donde la "
        "propia distinción entre «hay» y «no hay» es más discutible."))
    h.append(P(
        "<b>Geográficamente no hay bahía ciega.</b> Entre los 31 bloques con al menos 200 "
        "positivos reales, la tasa mediana de floración no detectada es del 3.06 % y el peor "
        "bloque llega al 16.16 %, repartidos a lo largo de Amatitlán sin agruparse en una "
        "zona concreta. Lo que sí aparece es que los falsos positivos forman un halo "
        "alrededor de las manchas verdaderas: el contorno de cada mancha tiene una "
        "incertidumbre de unos pocos píxeles, mientras que el núcleo es fiable."))

    filas = [["Lago", "Recall", "Precisión", "No detectado", "Falsa alarma"]]
    for lago, sub in predicciones.groupby("lago"):
        vp = int((sub["tipo_error"] == 3).sum())
        fn = int((sub["tipo_error"] == 2).sum())
        fp = int((sub["tipo_error"] == 1).sum())
        filas.append([config.NOMBRE_LARGO[lago], f"{vp/(vp+fn):.4f}", f"{vp/(vp+fp):.4f}",
                      f"{fn*0.0004:.2f} km²", f"{fp*0.0004:.2f} km²"])
    h.append(tabla(filas, [4.0 * cm, 2.6 * cm, 2.8 * cm, 3.2 * cm, 3.2 * cm]))
    h.append(Spacer(1, 8))

    # ---- Conclusiones --------------------------------------------------
    h.append(P("Conclusiones", "h1"))
    h.append(P(
        "<b>El modelo sí puede usarse como herramienta de apoyo al monitoreo en Amatitlán, "
        "con dos condiciones, y todavía no en Atitlán.</b>", "destacado"))
    h.append(P(
        "Detecta lo que importa: recupera el 96.7 % de los píxeles con alta presencia en "
        "Amatitlán sobre predicción fuera de muestra, y por encima de 13 µg/L falla en menos "
        "del 1 % de los casos. Prioriza bien el trabajo de campo: un equipo que muestree las "
        "zonas marcadas como «muy alta» acierta cinco de cada seis veces, frente al 1.18 % "
        "que obtendría eligiendo al azar. Y se apoya en variables físicamente sensatas, lo "
        "que da razones para esperar que aguante condiciones nuevas."))
    h.append(P(
        "Las dos condiciones son <b>recalibrar el umbral en cada escena</b>, porque la "
        "validación temporal y la transferencia entre lagos coinciden en que el problema es "
        "de calibración y no de discriminación, y <b>tratar sus salidas como una "
        "priorización de dónde muestrear</b>, nunca como un sustituto del muestreo."))
    h.append(P(
        "En Atitlán la precisión cae a 0.4694: más de la mitad de los avisos son falsos. Con "
        "1,324 píxeles positivos en 18 meses —el 0.039 % de su superficie— no hay material "
        "para caracterizar el fenómeno allí, y haría falta acumular muchos más eventos antes "
        "de darle el mismo uso."))

    h.append(P("La limitación de fondo", "h2"))
    h.append(P(
        "La etiqueta no viene de un muestreo de campo: es un índice espectral umbralado, "
        "calculado con B04 y B05. Que el modelo la reconstruya usando B07, B02 y B03 "
        "demuestra que la firma de una floración es redundante a lo ancho del espectro —un "
        "resultado real sobre la óptica del agua— pero <b>no</b> demuestra que detectaría "
        "una floración que el índice CyanoLakes no hubiera detectado. Si el índice se "
        "equivoca en una situación concreta, el modelo reproduce el error con la misma "
        "confianza. Además, la clorofila-a mide fitoplancton total y no cianobacteria: las "
        "guías de la OMS aplican el equivalente de 10 µg/L cuando las cianobacterias dominan "
        "la comunidad, y esa dominancia aquí se asume sin comprobarla."))
    h.append(P(
        "A esto se añaden los 20 metros de resolución, que borran las manchas incipientes; "
        "las once fechas por lago, muy pocas para separar estacionalidad de tendencia; y el "
        "sesgo de la nubosidad, que hace que las fechas disponibles no sean una muestra "
        "aleatoria del tiempo sino las que quedaron despejadas, cargadas hacia la estación "
        "seca."))

    h.append(P("Qué mejoraría el modelo", "h2"))
    h.append(P(
        "<b>Primero, muestreo de campo coincidente con el paso del satélite.</b> Es lo único "
        "que ataca la limitación de fondo, y bastarían unas decenas de puntos por lago para "
        "validar el índice, recalibrar el polinomio de clorofila para estas aguas concretas y "
        "confirmar con conteo celular la dominancia de cianobacteria que hoy se asume."))
    h.append(P(
        "<b>Segundo, más fechas</b>, que es lo más barato porque las imágenes ya existen y "
        "son gratuitas: Sentinel-2 pasa cada cinco días, así que en 18 meses hubo más de 100 "
        "oportunidades por lago y se usaron 11. Con 40 o 50 se podría validar hacia adelante "
        "en el tiempo, separar estacionalidad de tendencia y recoger más eventos positivos en "
        "Atitlán, que es lo que ese lago necesita."))
    h.append(P(
        "<b>Tercero, variables meteorológicas e hidrológicas</b>: temperatura del agua, "
        "precipitación acumulada de los días previos, viento y carga de nutrientes del río "
        "Villalobos. Son las que de verdad controlan el fenómeno y ninguna banda espectral "
        "las mide. Con ellas el modelo podría pasar de describir la floración del día de la "
        "imagen a anticiparla, que es un salto cualitativo en utilidad para la gestión."))

    h.append(Spacer(1, 10))
    h.append(P(
        "El resultado más valioso de esta segunda parte no es el modelo sino lo que la "
        "validación enseñó sobre él. Un experimento hecho sin cuidado —repartiendo píxeles al "
        "azar y dejando B04 y B05 entre las predictoras— habría reportado un ROC-AUC de "
        "1.0000 y cero falsos negativos, y habría sido completamente vacío. Lo que queda tras "
        "quitar esos atajos es un modelo más modesto y mucho más creíble.", "destacado"))

    h.append(P("El detalle técnico completo, con el código y todas las salidas, está en los "
               "cuadernos 07 al 14 del repositorio.", "pie"))

    doc.build(h)
    print(f"Escrito {config.BASE / 'Informe_Lab4_Parte2.pdf'}")


def main():
    validacion, generalizacion, interpretabilidad, guardado, predicciones = cargar()

    print("Recalculando las metricas de la division aleatoria ...")
    tabla_modelos = metricas_division_aleatoria(guardado)

    print("Generando figuras ...")
    figura_modelos(tabla_modelos)
    figura_validacion(validacion["pivote_f2"])
    figura_generalizacion(generalizacion["tabla"])
    figura_importancia(interpretabilidad)
    figura_mapas(predicciones)
    figura_error(predicciones)

    print("Armando el documento ...")
    construir(tabla_modelos, validacion, generalizacion, interpretabilidad,
              predicciones)


if __name__ == "__main__":
    main()
