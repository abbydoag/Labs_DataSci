# Lab 9 - Inciso 7: proyeccion visual del modelo ganador del Lab 1.
# Reconstruye la serie total (Turista + Excursionista), la division 70/30 y el
# ARIMA(0,1,1) sobre log1p del Lab 1, y grafica la prediccion sobre prueba con
# su intervalo de confianza del 95%.
# Uso: ~/.venvs/base-ds/bin/python Lab9/pronostico.py

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings("ignore")

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "Lab 1" / "df" / "Base_Migracion_2009-2026jun.csv"
SALIDA = Path(__file__).resolve().parent / "figuras"

ORDEN = (0, 1, 1)
PROPORCION_TRAIN = 0.70
ALFA = 0.05

# La banda en escala original crece hasta ~20 millones; se corta el eje en un
# nivel apenas sobre el maximo historico y el corte se rotula en la figura
Y_MAX = 600_000
INICIO_VISTA = "2018-01-01"

# Paleta provisional, se ajusta a la que acuerde el equipo
COLOR_HISTORIA = "#7F8F8B"
COLOR_OBSERVADO = "#0E4D45"
COLOR_ESTIMACION = "#3F8A26"
COLOR_TEXTO = "#1E2A28"


def cargar_serie_total():
    df = pd.read_csv(DATOS)
    df["Viajero"] = pd.to_numeric(df["Viajero"], errors="coerce")
    df = df[df["Tipo de Viajero"].isin(["Turista", "Excursionista"])].copy()
    df["Fecha"] = pd.to_datetime(dict(year=df["Año"], month=df["Mes cod"], day=1))
    calendario = pd.date_range(df["Fecha"].min(), df["Fecha"].max(), freq="MS")
    return (
        df.groupby("Fecha")["Viajero"].sum()
        .reindex(calendario, fill_value=0)
        .astype(float)
        .asfreq("MS")
    )


def dividir_serie(serie, proporcion=PROPORCION_TRAIN):
    corte = int(np.floor(len(serie) * proporcion))
    return serie.iloc[:corte].copy(), serie.iloc[corte:].copy()


def pronosticar(train, test):
    ajuste = ARIMA(
        np.log1p(train),
        order=ORDEN,
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit()
    pron = ajuste.get_forecast(steps=len(test))
    banda = pron.conf_int(alpha=ALFA)
    # El intervalo se calcula en escala log y se regresa a viajeros
    return pd.DataFrame(
        {
            "media": np.maximum(0, np.expm1(np.asarray(pron.predicted_mean))),
            "inferior": np.maximum(0, np.expm1(np.asarray(banda.iloc[:, 0]))),
            "superior": np.maximum(0, np.expm1(np.asarray(banda.iloc[:, 1]))),
        },
        index=test.index,
    )


def metricas(test, pron):
    mae = mean_absolute_error(test, pron["media"])
    rmse = np.sqrt(mean_squared_error(test, pron["media"]))
    dentro = ((test >= pron["inferior"]) & (test <= pron["superior"])).mean()
    return {
        "MAE": mae,
        "RMSE": rmse,
        "RMSE_pct_promedio": 100 * rmse / test.mean(),
        "cobertura_95": 100 * dentro,
    }


def graficar(train, test, pron, m):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13})
    fig, ax = plt.subplots(figsize=(12, 6), dpi=200)

    historia = train.loc[INICIO_VISTA:]
    ax.fill_between(
        pron.index, pron["inferior"], pron["superior"].clip(upper=Y_MAX),
        color=COLOR_ESTIMACION, alpha=0.18, linewidth=0,
    )
    ax.plot(historia.index, historia, color=COLOR_HISTORIA, lw=1.6)
    ax.plot(test.index, test, color=COLOR_OBSERVADO, lw=2.6)
    ax.plot(pron.index, pron["media"], color=COLOR_ESTIMACION, lw=2.6, ls="--")
    ax.axvline(test.index[0], color=COLOR_TEXTO, lw=0.8, ls=":")

    # Etiquetas directas en lugar de leyenda
    ax.text(
        historia.index[2], historia.max() * 1.06,
        "Datos usados para entrenar", color=COLOR_HISTORIA, fontsize=12,
    )
    ax.text(
        test.index[1], Y_MAX * 0.97, "Inicio de prueba",
        color=COLOR_TEXTO, fontsize=11, va="top",
    )
    ultimo = test.index[-1]
    ax.annotate(
        "Real", (ultimo, test.iloc[-1]), xytext=(8, 0),
        textcoords="offset points", color=COLOR_OBSERVADO,
        fontsize=13, fontweight="bold", va="center",
    )
    ax.annotate(
        f"Estimación\n{pron['media'].iloc[-1]:,.0f} al mes",
        (ultimo, pron["media"].iloc[-1]), xytext=(8, 0),
        textcoords="offset points", color=COLOR_ESTIMACION,
        fontsize=13, fontweight="bold", va="center",
    )
    ax.annotate(
        "Estimación: intervalo 95%\n"
        "sigue subiendo fuera del gráfico:\n"
        f"techo de {pron['superior'].iloc[-1] / 1e6:,.1f} millones en "
        f"{ultimo:%m/%Y}",
        (ultimo, Y_MAX), xytext=(8, -6), textcoords="offset points",
        color=COLOR_ESTIMACION, fontsize=11, va="top",
    )

    ax.set_title(
        "El modelo se quedó en el nivel de la pandemia",
        loc="left", fontsize=18, fontweight="bold", color=COLOR_TEXTO, pad=30,
    )
    ax.text(
        0, 1.02,
        f"Viajeros mensuales (turistas + excursionistas). ARIMA{ORDEN} se equivoca "
        f"en promedio por {m['MAE'] / 1000:,.0f} mil viajeros al mes (MAE).",
        transform=ax.transAxes, fontsize=12, color=COLOR_HISTORIA,
    )
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v / 1000:,.0f} mil")
    )
    ax.set_ylim(0, Y_MAX)
    ax.set_xlim(historia.index[0], ultimo + pd.DateOffset(months=26))
    # El margen derecho es solo para las etiquetas, no lleva anos en el eje
    ax.set_xticks(pd.date_range(historia.index[0], ultimo, freq="YS"))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"{pd.Timestamp(plt.matplotlib.dates.num2date(v)).year}"
    ))
    for lado in ["top", "right"]:
        ax.spines[lado].set_visible(False)
    ax.grid(axis="y", color="#D4E2D6", lw=0.8)
    ax.tick_params(colors=COLOR_TEXTO)

    fig.tight_layout()
    SALIDA.mkdir(exist_ok=True)
    ruta = SALIDA / "07_pronostico_intervalo.png"
    fig.savefig(ruta, dpi=200, facecolor="white")
    plt.close(fig)
    return ruta


def main():
    serie = cargar_serie_total()
    train, test = dividir_serie(serie)
    pron = pronosticar(train, test)
    m = metricas(test, pron)

    print(f"Entrenamiento: {train.index.min():%Y-%m} a {train.index.max():%Y-%m} ({len(train)} meses)")
    print(f"Prueba: {test.index.min():%Y-%m} a {test.index.max():%Y-%m} ({len(test)} meses)")
    print(f"MAE={m['MAE']:,.0f}  RMSE={m['RMSE']:,.0f}  RMSE/promedio={m['RMSE_pct_promedio']:.1f}%")
    print(f"Meses reales dentro del intervalo 95%: {m['cobertura_95']:.0f}%")
    print("Figura:", graficar(train, test, pron, m))


if __name__ == "__main__":
    main()
