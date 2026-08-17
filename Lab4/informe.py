"""Genera Informe_Lab4.pdf, el informe dirigido a publico no tecnico.

Produce primero las figuras a partir de las escenas descargadas y luego arma el
documento. Se corre despues de los cuadernos:

    .venv/bin/python informe.py
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
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

from src import config, datos, graficos
from src import indices as ix

FIG = config.FIGURAS
COLOR = {"Atitlan": "#1f6f8b", "Amatitlan": "#c1272d"}
AZUL = colors.HexColor("#1f6f8b")
ROJO = colors.HexColor("#c1272d")
GRIS = colors.HexColor("#444444")


# --------------------------------------------------------------------------
# Figuras
# --------------------------------------------------------------------------


def figura_evolucion(resumen):
    fig, ejes = plt.subplots(2, 1, figsize=(9, 6.4), sharex=True)
    for eje, lago in zip(ejes, ["Atitlan", "Amatitlan"]):
        sub = resumen[resumen["lago"] == lago]
        eje.plot(sub["fecha"], sub["chl_media"], "o-", color=COLOR[lago],
                 linewidth=2.2, markersize=7)
        eje.fill_between(sub["fecha"], 0, sub["chl_media"], color=COLOR[lago], alpha=0.12)
        eje.axhline(2.6, color="#888", linestyle=":", linewidth=1)
        eje.axhline(7.3, color="#d95f02", linestyle="--", linewidth=1)
        eje.text(sub["fecha"].iloc[0], 2.75, "frontera mesotrofica (2.6)",
                 fontsize=7.5, color="#666")
        if sub["chl_media"].max() > 6:
            eje.text(sub["fecha"].iloc[0], 7.5, "frontera eutrofica (7.3)",
                     fontsize=7.5, color="#d95f02")
        eje.set_title(config.NOMBRE_LARGO[lago], loc="left", fontsize=12, fontweight="bold")
        eje.set_ylabel("Clorofila-a (µg/L)")
        eje.grid(alpha=0.25)
        eje.set_ylim(0, max(3, sub["chl_media"].max() * 1.25))
    ejes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.tight_layout()
    fig.savefig(FIG / "informe_evolucion.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def figura_comparacion(resumen):
    fig, ejes = plt.subplots(1, 3, figsize=(12, 3.8))

    datos_caja = [resumen[resumen["lago"] == l]["chl_media"].dropna().values
                  for l in ["Atitlan", "Amatitlan"]]
    partes = ejes[0].boxplot(datos_caja, tick_labels=["Atitlan", "Amatitlan"],
                             patch_artist=True, widths=0.55)
    for caja, lago in zip(partes["boxes"], ["Atitlan", "Amatitlan"]):
        caja.set_facecolor(COLOR[lago]); caja.set_alpha(0.6)
    for i, g in enumerate(datos_caja, start=1):
        ejes[0].scatter(np.random.normal(i, 0.05, len(g)), g, color="black", s=26, zorder=3)
    ejes[0].set_ylabel("Clorofila-a media (µg/L)")
    ejes[0].set_title("Cuanta hay", loc="left", fontsize=11, fontweight="bold")

    for k, lago in enumerate(["Atitlan", "Amatitlan"]):
        sub = resumen[resumen["lago"] == lago]
        alturas = [100 * (sub["chl_media"] > c).mean() for c in (2.6, 7.3)]
        ejes[1].bar(np.arange(2) + (k - 0.5) * 0.35, alturas, 0.35,
                    color=COLOR[lago], alpha=0.9, label=config.NOMBRE_LARGO[lago])
    ejes[1].set_xticks(range(2), ["Mesotrofico\n(>2.6)", "Eutrofico\n(>7.3)"], fontsize=9)
    ejes[1].set_ylabel("% de las fechas")
    ejes[1].set_title("Cada cuanto", loc="left", fontsize=11, fontweight="bold")
    ejes[1].legend(fontsize=8)

    for lago in ["Atitlan", "Amatitlan"]:
        sub = resumen[resumen["lago"] == lago].sort_values("fecha")
        ejes[2].plot(sub["fecha"], sub["pct_alto"], "o-", color=COLOR[lago],
                     linewidth=2, label=config.NOMBRE_LARGO[lago])
    ejes[2].set_ylabel("% del lago sobre 10 µg/L")
    ejes[2].set_title("Que tan extendida", loc="left", fontsize=11, fontweight="bold")
    ejes[2].tick_params(axis="x", rotation=40, labelsize=7)
    ejes[2].legend(fontsize=8)

    for eje in ejes:
        eje.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    fig.savefig(FIG / "informe_comparacion.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def figura_mapas(lago, resumen):
    sub = resumen[resumen["lago"] == lago].dropna(subset=["chl_media"])
    f_min = sub.loc[sub["chl_media"].idxmin()]
    f_max = sub.loc[sub["chl_media"].idxmax()]

    fig, ejes = plt.subplots(1, 2, figsize=(11, 5))
    for eje, fila, etiqueta in [
        (ejes[0], f_min, "Fecha mas limpia"),
        (ejes[1], f_max, "Fecha mas cargada"),
    ]:
        fecha = fila["fecha"].strftime("%Y-%m-%d")
        capas, _ = datos.indices_escena(lago, fecha)
        graficos.dibujar_mapa_chl(
            eje, capas, f"{etiqueta}\n{fecha}  —  media {fila['chl_media']:.1f} µg/L")
    graficos.barra_color_chl(fig, list(ejes))
    fig.suptitle(config.NOMBRE_LARGO[lago], fontsize=13, fontweight="bold")
    fig.savefig(FIG / f"informe_mapas_{lago}.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


def figura_persistencia():
    fig, ejes = plt.subplots(1, 2, figsize=(11, 5))
    for eje, lago in zip(ejes, ["Atitlan", "Amatitlan"]):
        pila, fechas, _ = datos.pila_chl(lago)
        obs = np.sum(np.isfinite(pila), axis=0)
        confiable = obs >= max(2, len(fechas) // 2)
        excesos = np.sum(pila > ix.UMBRAL_ALTO_CHL, axis=0)
        pers = np.where(confiable, 100 * excesos / np.maximum(obs, 1), np.nan)

        capas, _ = datos.indices_escena(lago, fechas[0])
        eje.imshow(graficos.color_verdadero_realzado(capas))
        im = eje.imshow(np.ma.masked_invalid(pers), cmap="inferno", vmin=0, vmax=100,
                        interpolation="nearest")
        eje.set_title(config.NOMBRE_LARGO[lago], fontsize=12, fontweight="bold")
        eje.set_xticks([]); eje.set_yticks([])
        plt.colorbar(im, ax=eje, fraction=0.046, label="% de fechas sobre 10 µg/L")
    fig.tight_layout()
    fig.savefig(FIG / "informe_persistencia.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# Documento
# --------------------------------------------------------------------------


def estilos():
    hojas = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("titulo", parent=hojas["Title"], fontSize=23,
                                 leading=27, textColor=AZUL, spaceAfter=6),
        "subtitulo": ParagraphStyle("subtitulo", parent=hojas["Normal"], fontSize=13,
                                    leading=17, alignment=TA_CENTER, textColor=GRIS,
                                    spaceAfter=22),
        "h1": ParagraphStyle("h1", parent=hojas["Heading1"], fontSize=15, leading=19,
                             textColor=AZUL, spaceBefore=16, spaceAfter=8),
        "h2": ParagraphStyle("h2", parent=hojas["Heading2"], fontSize=12, leading=15,
                             textColor=GRIS, spaceBefore=11, spaceAfter=5),
        "cuerpo": ParagraphStyle("cuerpo", parent=hojas["Normal"], fontSize=10,
                                 leading=15, alignment=TA_JUSTIFY, spaceAfter=8),
        "destacado": ParagraphStyle("destacado", parent=hojas["Normal"], fontSize=10.5,
                                    leading=16, alignment=TA_JUSTIFY, spaceAfter=8,
                                    leftIndent=10, rightIndent=10, borderPadding=8,
                                    backColor=colors.HexColor("#f2f6f8")),
        "pie": ParagraphStyle("pie", parent=hojas["Normal"], fontSize=8, leading=11,
                              textColor=GRIS, alignment=TA_CENTER, spaceBefore=4),
    }


def tabla(datos_tabla, anchos, cabecera=True):
    t = Table(datos_tabla, colWidths=anchos, hAlign="CENTER")
    estilo = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.6),
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


def construir(resumen):
    e = estilos()
    doc = SimpleDocTemplate(
        str(config.BASE / "Informe_Lab4.pdf"), pagesize=A4,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="Cianobacteria en los lagos de Atitlan y Amatitlan",
        author="Fabian Prado, Abby Donis, Hansel Lopez",
    )

    at = resumen[resumen["lago"] == "Atitlan"]
    am = resumen[resumen["lago"] == "Amatitlan"]
    h = []
    P = lambda txt, est="cuerpo": Paragraph(txt, e[est])  # noqa: E731

    # --- Portada -----------------------------------------------------------
    h += [
        Spacer(1, 2.4 * cm),
        P("Cianobacteria en los lagos de Atitlan y Amatitlan", "titulo"),
        P("Lo que 18 meses de imagenes de satelite dicen sobre la salud de dos lagos "
          "de Guatemala", "subtitulo"),
        Spacer(1, 0.5 * cm),
        Image(str(FIG / "informe_evolucion.png"), width=15.2 * cm, height=10.8 * cm),
        Spacer(1, 0.6 * cm),
        P("Universidad del Valle de Guatemala &middot; CC3084 Data Science &middot; "
          "Laboratorio 4<br/>Fabian Prado Dluzniewski &middot; Abby Donis &middot; "
          "Hansel Lopez<br/>Agosto de 2026", "pie"),
        PageBreak(),
    ]

    # --- Resumen -----------------------------------------------------------
    h += [
        P("En resumen", "h1"),
        P("Analizamos 22 imagenes del satelite europeo Sentinel-2 —once de cada lago— "
          "tomadas entre enero de 2025 y julio de 2026, para medir cuanta cianobacteria "
          "hay en el agua sin necesidad de ir a tomar muestras. Estas son las tres "
          "conclusiones principales.", "cuerpo"),
        P("<b>1. El lago de Atitlan se mantuvo limpio durante todo el periodo.</b> "
          "En las once fechas analizadas el agua se clasifica como oligotrofica, que es "
          "la categoria de mejor calidad. No detectamos ninguna floracion de "
          "cianobacteria.", "destacado"),
        P("<b>2. El lago de Amatitlan esta cinco veces mas cargado, y empeoro durante "
          "2026.</b> Entre febrero y junio de 2026 la concentracion se multiplico por "
          "2.7, y la superficie afectada paso de ser insignificante a cubrir mas de la "
          "mitad del lago.", "destacado"),
        P("<b>3. En Amatitlan el problema tiene una ubicacion concreta.</b> Las zonas "
          "que se ensucian una y otra vez estan en la mitad oriental del lago, cerca de "
          "donde desemboca el rio Villalobos, que trae las aguas del area metropolitana "
          "de la ciudad de Guatemala.", "destacado"),

        P("Como se midio", "h1"),
        P("Las cianobacterias no se ven desde el espacio, pero si se ve el pigmento verde "
          "que usan para hacer fotosintesis: la clorofila. Ese pigmento absorbe la luz "
          "roja y refleja una banda de luz muy especifica, justo en el limite entre el "
          "rojo y el infrarrojo. El satelite Sentinel-2 lleva un sensor puesto "
          "exactamente ahi, asi que comparando cuanta luz de cada tipo devuelve el agua "
          "se puede estimar cuanta clorofila tiene, y con ella cuanta floracion.", "cuerpo"),
        P("Usamos un procedimiento publicado y validado por especialistas —el script "
          "CyanoLakes, de Kravitz y Matthews— que ademas distingue automaticamente el "
          "agua de la tierra y separa las natas que flotan en la superficie. El resultado "
          "se expresa en microgramos de clorofila por litro (µg/L), la misma unidad que "
          "usa un laboratorio de calidad de agua.", "cuerpo"),
        P("Las fechas no las elegimos nosotros: vienen fijadas por el curso y "
          "corresponden a dias en que el satelite paso con el cielo despejado sobre "
          "cada lago.", "cuerpo"),

        P("Como leer los numeros", "h1"),
        tabla([
            ["Clorofila-a media", "Categoria", "Que significa"],
            ["Menos de 2.6 µg/L", "Oligotrofico", "Agua limpia, poca vida vegetal"],
            ["2.6 a 7.3 µg/L", "Mesotrofico", "Productividad moderada"],
            ["7.3 a 56 µg/L", "Eutrofico", "Floraciones frecuentes"],
            ["Mas de 56 µg/L", "Hipereutrofico", "Floracion severa y persistente"],
        ], [4.2 * cm, 3.4 * cm, 8.2 * cm]),
        Spacer(1, 0.3 * cm),
        P("La Organizacion Mundial de la Salud fija ademas dos referencias para agua de "
          "uso recreativo: a partir de 10 µg/L recomienda vigilancia, y a partir de "
          "50 µg/L, alerta. Usamos el nivel de 10 µg/L para medir que porcion de cada "
          "lago esta afectada.", "cuerpo"),
        PageBreak(),
    ]

    # --- Atitlan -----------------------------------------------------------
    h += [
        P("Lago de Atitlan", "h1"),
        P(f"<b>Estado general: oligotrofico, es decir, agua de buena calidad.</b> "
          f"El promedio de las once fechas es de {at['chl_media'].mean():.2f} µg/L, muy "
          f"por debajo del limite de 2.6 que separa el agua limpia de la de "
          f"productividad moderada. Ninguna de las once fechas alcanza siquiera ese "
          f"limite.", "destacado"),
        P(f"La concentracion oscilo entre {at['chl_media'].min():.2f} y "
          f"{at['chl_media'].max():.2f} µg/L. Los valores mas altos se dieron en abril "
          f"—en 2025 y otra vez en 2026— que es el final de la estacion seca, cuando el "
          f"agua esta mas caliente y lleva meses sin renovarse. Aun asi, esos maximos "
          f"siguen siendo caracteristicos de un lago limpio.", "cuerpo"),
        P("La superficie del lago que supera el nivel de vigilancia de la OMS nunca pasa "
          "del 0.14 %. Dicho de otro modo: en 18 meses de observacion, el 99.8 % del "
          "lago no cruzo ese nivel ni una sola vez.", "cuerpo"),
        P("<b>Donde estan las pocas senales.</b> Los valores algo mas altos no aparecen "
          "en el centro del lago sino pegados a la orilla, en tres puntos: la bahia de "
          "Santiago Atitlan, el sector frente a San Lucas Toliman y un area cerca de "
          "Santa Cruz La Laguna. Son bahias cerradas, con poblados en la orilla y rios "
          "que bajan de la cuenca. Ninguna alcanza niveles preocupantes hoy, pero son "
          "exactamente los lugares que conviene vigilar, porque son los unicos donde el "
          "lago da senales.", "cuerpo"),
        Image(str(FIG / "informe_mapas_Atitlan.png"), width=15.2 * cm, height=7.0 * cm),
        P("Comparacion entre la fecha mas limpia y la mas cargada del periodo. El azul "
          "intenso indica agua limpia. La diferencia entre ambas es real pero pequena en "
          "terminos absolutos.", "pie"),
        PageBreak(),
    ]

    # --- Amatitlan ---------------------------------------------------------
    fila_max = am.loc[am["chl_media"].idxmax()]
    h += [
        P("Lago de Amatitlan", "h1"),
        P(f"<b>Estado general: mesotrofico, con episodios eutroficos y una tendencia "
          f"clara al alza.</b> El promedio del periodo es de {am['chl_media'].mean():.2f} "
          f"µg/L, unas cinco veces el de Atitlan, en un lago ocho veces mas pequeno. "
          f"Las once fechas superan el limite de agua limpia; dos de ellas entran en "
          f"categoria eutrofica.", "destacado"),
        P("Lo mas relevante no es el promedio sino la trayectoria durante 2026:", "cuerpo"),
        tabla([
            ["Fecha", "Clorofila-a media", "Superficie sobre 10 µg/L"],
            ["2 de febrero de 2026", "4.29 µg/L", "0.01 %"],
            ["29 de marzo de 2026", "6.44 µg/L", "7.8 %"],
            ["13 de abril de 2026", "6.76 µg/L", "4.9 %"],
            ["28 de abril de 2026", "9.90 µg/L", "35.6 %"],
            ["19 de junio de 2026", "11.49 µg/L", "53.4 %"],
        ], [5.4 * cm, 5.0 * cm, 5.4 * cm]),
        Spacer(1, 0.25 * cm),
        P(f"En cuatro meses y medio la concentracion media se multiplico por 2.7 y la "
          f"superficie afectada paso de practicamente nada a mas de la mitad del lago. "
          f"El 19 de junio de 2026, la peor fecha registrada, unos 7.8 de los 14.7 "
          f"kilometros cuadrados del lago estaban por encima del nivel de vigilancia "
          f"sanitaria al mismo tiempo.", "cuerpo"),
        P("<b>Hay ademas episodios locales intensos que un promedio esconde.</b> El 24 "
          "de noviembre de 2025 y el 8 de enero de 2026 el promedio del lago parecia "
          "moderado, pero habia zonas con concentraciones diez y veinte veces mayores, "
          "junto con material flotando en la superficie. Son floraciones concentradas en "
          "una parte del lago.", "cuerpo"),
        Image(str(FIG / "informe_mapas_Amatitlan.png"), width=15.2 * cm, height=6.6 * cm),
        P("Comparacion entre la fecha mas limpia y la mas cargada. Los tonos verdes y "
          "amarillos indican concentraciones crecientes de clorofila.", "pie"),
        PageBreak(),
    ]

    # --- Donde se acumula --------------------------------------------------
    h += [
        P("Donde se acumula el problema", "h1"),
        P("Una de las preguntas mas utiles para gestion no es cuanta cianobacteria hay, "
          "sino si siempre se junta en el mismo sitio. Una zona que aparece cargada una y "
          "otra vez apunta a una causa fija —una descarga, una desembocadura, una zona de "
          "poca circulacion— y no a un evento pasajero.", "cuerpo"),
        Image(str(FIG / "informe_persistencia.png"), width=15.2 * cm, height=6.6 * cm),
        P("Cuantas veces, de las once observaciones, cada punto del lago supero el nivel "
          "de vigilancia. Negro y morado: nunca o casi nunca. Naranja y amarillo: de "
          "forma repetida.", "pie"),
        Spacer(1, 0.3 * cm),
        tabla([
            ["", "Atitlan", "Amatitlan"],
            ["Superficie que nunca supera 10 µg/L", "99.8 %", "28.5 %"],
            ["Afectacion ocasional (1 a 25 % de las fechas)", "0.2 %", "65.8 %"],
            ["Afectacion recurrente (25 a 50 % de las fechas)", "0.0 %", "5.6 %"],
            ["Superficie recurrente en km2", "0.05 km2", "0.82 km2"],
        ], [8.0 * cm, 3.3 * cm, 3.3 * cm]),
        Spacer(1, 0.3 * cm),
        P("En Atitlan la afectacion es practicamente inexistente. En Amatitlan se "
          "invierte: solo un 28.5 % del lago se libra, y hay 0.82 kilometros cuadrados "
          "que superan el nivel de vigilancia en una de cada cuatro fechas o mas. Esa "
          "franja esta en el sector oriental, aguas abajo de la entrada del rio "
          "Villalobos, entre 3 y 6 kilometros de San Miguel Petapa.", "cuerpo"),
        P("<b>Un dato esperanzador:</b> ningun punto de ninguno de los dos lagos esta "
          "afectado de forma cronica, es decir, en mas del 75 % de las observaciones. "
          "Amatitlan no esta permanentemente florecido: se carga y se descarga, pero "
          "siempre por el mismo lado. Eso significa que el sistema todavia responde, y "
          "que actuar sobre la fuente tendria un efecto medible.", "destacado"),
        PageBreak(),
    ]

    # --- Comparacion -------------------------------------------------------
    h += [
        P("Los dos lagos, lado a lado", "h1"),
        Image(str(FIG / "informe_comparacion.png"), width=15.4 * cm, height=4.9 * cm),
        Spacer(1, 0.3 * cm),
        tabla([
            ["", "Atitlan", "Amatitlan"],
            ["Clorofila-a media del periodo", "1.24 µg/L", "6.29 µg/L"],
            ["Rango entre fechas", "0.59 a 2.12", "4.29 a 11.49"],
            ["Superficie media sobre 10 µg/L", "0.04 %", "10.8 %"],
            ["Superficie maxima sobre 10 µg/L", "0.14 %", "53.4 %"],
            ["Fechas en categoria mesotrofica o peor", "0 de 11", "11 de 11"],
            ["Fechas en categoria eutrofica", "0 de 11", "2 de 11"],
            ["Superficie del lago", "122 km2", "14.7 km2"],
            ["Profundidad media", "unos 180 m", "unos 18 m"],
            ["Poblacion en la cuenca", "unos 150 mil", "mas de 1.5 millones"],
        ], [7.4 * cm, 3.6 * cm, 3.6 * cm]),

        P("Que explica la diferencia", "h1"),
        P("<b>La profundidad.</b> Atitlan tiene unos 180 metros de profundidad media; "
          "Amatitlan, unos 18. La misma cantidad de nutrientes repartida en una columna "
          "de agua diez veces mas profunda produce una concentracion mucho menor. Ademas "
          "un lago profundo guarda buena parte de sus nutrientes lejos de la superficie "
          "iluminada, donde las algas los necesitan.", "cuerpo"),
        P("<b>La presion urbana.</b> La cuenca de Amatitlan recibe la descarga del area "
          "metropolitana de la ciudad de Guatemala, con mas de un millon y medio de "
          "habitantes; el rio Villalobos llega cargado de aguas residuales sin "
          "tratamiento suficiente. La cuenca de Atitlan tiene alrededor de diez veces "
          "menos poblacion. Esto es coherente con lo que muestran los mapas: los focos "
          "persistentes de Amatitlan estan justo donde descarga ese rio.", "cuerpo"),
        P("<b>El volumen y el recambio.</b> Amatitlan es pequeno frente a lo que recibe. "
          "Atitlan, aunque no tiene salida superficial, tiene un volumen enorme que "
          "diluye muchisimo mas cualquier carga que le llegue.", "cuerpo"),
        P("<b>La temperatura.</b> Amatitlan esta unos 370 metros mas bajo que Atitlan, lo "
          "que se traduce en agua mas calida. La cianobacteria se reproduce mas rapido "
          "cuanto mas caliente esta el agua.", "cuerpo"),
        P("La comparacion honesta no es que un lago este bien y el otro mal, sino que son "
          "sistemas de escalas distintas: Amatitlan es un lago pequeno y poco profundo "
          "recibiendo la carga de una capital, mientras que Atitlan es grande y profundo "
          "con una presion proporcionalmente mucho menor. Eso no lo hace inmune.", "cuerpo"),
        PageBreak(),
    ]

    # --- Limitaciones y conclusiones --------------------------------------
    h += [
        P("Que tan confiables son estos resultados", "h1"),
        P("<b>Lo que si podemos afirmar.</b> Las 22 imagenes tuvieron mas del 99.6 % de "
          "cobertura util despues de descartar nubes, y la superficie de agua detectada "
          "coincide con la conocida de cada lago y varia menos de un 4 % entre fechas. "
          "La diferencia entre los dos lagos es tan grande y tan consistente que no "
          "depende de detalles del metodo.", "cuerpo"),
        P("<b>Lo que no podemos afirmar.</b> Las fechas disponibles no son una muestra "
          "aleatoria del calendario: son los dias en que el satelite encontro cielo "
          "despejado, y en Guatemala eso ocurre mucho mas en la estacion seca. De las 22 "
          "escenas, 18 corresponden a esa estacion. Por eso cualquier conclusion sobre "
          "estacionalidad es indicativa y no concluyente, y haria falta varios anos "
          "completos de observaciones para afirmar un patron anual.", "cuerpo"),
        P("<b>Sobre el metodo.</b> El satelite estima la clorofila a partir del color del "
          "agua; no cuenta celulas de cianobacteria ni mide toxinas. Un valor alto indica "
          "abundancia de algas, pero determinar si esa floracion es toxica requiere "
          "analisis de laboratorio. Estos resultados sirven para saber donde y cuando "
          "tomar muestras, no para sustituirlas.", "cuerpo"),

        P("Conclusiones", "h1"),
        P("<b>1.</b> El lago de Atitlan se mantuvo en buen estado durante los 18 meses "
          "analizados. Conviene vigilar las bahias de Santiago Atitlan y San Lucas "
          "Toliman, que son los unicos puntos donde el lago da alguna senal.", "cuerpo"),
        P("<b>2.</b> El lago de Amatitlan muestra un deterioro claro y medible durante "
          "2026, con la concentracion multiplicandose por 2.7 entre febrero y junio y la "
          "superficie afectada superando la mitad del lago en la ultima fecha observada. "
          "Es el hallazgo que merece atencion inmediata.", "cuerpo"),
        P("<b>3.</b> El problema de Amatitlan tiene una ubicacion identificable: la mitad "
          "oriental del lago, aguas abajo de la desembocadura del rio Villalobos. Que la "
          "afectacion sea recurrente pero no cronica sugiere que el lago aun responde y "
          "que una intervencion sobre esa fuente tendria efecto observable.", "cuerpo"),
        P("<b>4.</b> El seguimiento por satelite funciona para este proposito y cuesta "
          "una fraccion de lo que costaria un muestreo equivalente. Permite revisar el "
          "lago completo cada pocos dias, identificar donde tomar muestras y verificar si "
          "una medida de gestion esta funcionando.", "cuerpo"),

        Spacer(1, 0.7 * cm),
        P("Datos: mision Sentinel-2, programa Copernicus de la Union Europea. "
          "Indice de cianobacteria: script CyanoLakes Chlorophyll-a de Jeremy Kravitz y "
          "Mark Matthews (2020), publicado en custom-scripts.sentinel-hub.com. "
          "El codigo completo del analisis esta en el repositorio del proyecto.", "pie"),
    ]

    doc.build(h)
    print(f"Escrito {config.BASE / 'Informe_Lab4.pdf'}")


def main():
    resumen = datos.tabla_resumen()
    print("Generando figuras ...")
    figura_evolucion(resumen)
    figura_comparacion(resumen)
    for lago in ["Atitlan", "Amatitlan"]:
        figura_mapas(lago, resumen)
    figura_persistencia()
    print("Armando el documento ...")
    construir(resumen)


if __name__ == "__main__":
    main()
