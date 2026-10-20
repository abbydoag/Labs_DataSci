# Lab 9 - Inciso 6: Comparativa de modelos
# Contrasta el desempeno de los 5 algoritmos entrenados en el Lab 1 usando
# las metricas adecuadas (MAE, RMSE en prueba; AIC/BIC solo para ARIMA).
# Uso: Lab\ 1/.venv/bin/python Lab9/modelos_comparativa.py

from pathlib import Path
import warnings
import logging

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.holtwinters import SimpleExpSmoothing
from prophet import Prophet

warnings.filterwarnings("ignore")
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
logging.getLogger("prophet").setLevel(logging.WARNING)

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "Lab 1" / "df" / "Base_Migracion_2009-2026jun.csv"
SALIDA = Path(__file__).resolve().parent / "figuras"

PROPORCION_TRAIN = 0.70
ORDEN_ARIMA = (0, 1, 1)

# Paleta consistente con pronostico.py y cuadrante_comparativo.py
COLOR_BASE = "#7F8F8B"
COLOR_TEXTO = "#1E2A28"
COLOR_ACENTO = "#0E4D45"  # Ganador
COLOR_SECUNDARIO = "#3F8A26"


def cargar_serie_total():
    df = pd.read_csv(DATOS)
    df["Viajero"] = pd.to_numeric(df["Viajero"], errors="coerce")
    df = df[df["Tipo de Viajero"].isin(["Turista", "Excursionista"])].copy()
    df["Fecha"] = pd.to_datetime(
        dict(year=df["Año"], month=df["Mes cod"], day=1)
    )
    calendario = pd.date_range(df["Fecha"].min(), df["Fecha"].max(), freq="MS")
    return (
        df.groupby("Fecha")["Viajero"]
        .sum()
        .reindex(calendario, fill_value=0)
        .astype(float)
        .asfreq("MS")
    )


def dividir_serie(serie, proporcion=PROPORCION_TRAIN):
    corte = int(np.floor(len(serie) * proporcion))
    return serie.iloc[:corte].copy(), serie.iloc[corte:].copy()


def entrenar_modelos(train, test):
    """Reentrena los 5 modelos con las especificaciones exactas del Lab 1."""
    resultados = {}

    # ARIMA(0,1,1) sobre log1p
    y_train_log = np.log1p(train)
    ajuste = ARIMA(
        y_train_log,
        order=ORDEN_ARIMA,
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit()
    pron_log = ajuste.forecast(steps=len(test))
    pron = pd.Series(
        np.maximum(0, np.expm1(np.asarray(pron_log))), index=test.index
    )
    resultados["ARIMA(0,1,1)"] = {
        "pron": pron,
        "MAE": mean_absolute_error(test, pron),
        "RMSE": np.sqrt(mean_squared_error(test, pron)),
        "AIC": ajuste.aic,
        "BIC": ajuste.bic,
    }

    # Holt-Winters damped + estacionalidad aditiva
    hw = ExponentialSmoothing(
        train,
        trend="add",
        damped_trend=True,
        seasonal="add",
        seasonal_periods=12,
        initialization_method="estimated",
    ).fit(optimized=True)
    pron_hw = hw.forecast(len(test)).clip(lower=0)
    resultados["Holt-Winters"] = {
        "pron": pron_hw,
        "MAE": mean_absolute_error(test, pron_hw),
        "RMSE": np.sqrt(mean_squared_error(test, pron_hw)),
        "AIC": np.nan,
        "BIC": np.nan,
    }

    # Suavizamiento exponencial simple
    ses = SimpleExpSmoothing(
        train, initialization_method="estimated"
    ).fit(optimized=True)
    pron_ses = ses.forecast(len(test)).clip(lower=0)
    resultados["Suavizamiento\nexponencial"] = {
        "pron": pron_ses,
        "MAE": mean_absolute_error(test, pron_ses),
        "RMSE": np.sqrt(mean_squared_error(test, pron_ses)),
        "AIC": np.nan,
        "BIC": np.nan,
    }

    # Seasonal naive
    patron_12 = train.iloc[-12:].to_numpy()
    pron_sn = pd.Series(
        np.resize(patron_12, len(test)), index=test.index
    )
    resultados["Seasonal naive"] = {
        "pron": pron_sn,
        "MAE": mean_absolute_error(test, pron_sn),
        "RMSE": np.sqrt(mean_squared_error(test, pron_sn)),
        "AIC": np.nan,
        "BIC": np.nan,
    }

    # Prophet con estacionalidad anual aditiva
    prophet_train = train.rename_axis("ds").reset_index(name="y")
    pm = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="additive",
        changepoint_prior_scale=0.10,
        interval_width=0.95,
    )
    pm.fit(prophet_train)
    prophet_fcst = pm.predict(pd.DataFrame({"ds": test.index}))
    pron_pr = pd.Series(
        np.maximum(0, prophet_fcst["yhat"].to_numpy()), index=test.index
    )
    resultados["Prophet"] = {
        "pron": pron_pr,
        "MAE": mean_absolute_error(test, pron_pr),
        "RMSE": np.sqrt(mean_squared_error(test, pron_pr)),
        "AIC": np.nan,
        "BIC": np.nan,
    }

    return resultados


def construir_tabla(resultados):
    filas = []
    for nombre, r in resultados.items():
        filas.append(
            {
                "Modelo": nombre.replace("\n", " "),
                "MAE": r["MAE"],
                "RMSE": r["RMSE"],
                "AIC": r["AIC"],
                "BIC": r["BIC"],
            }
        )
    return (
        pd.DataFrame(filas)
        .sort_values(["RMSE", "MAE"])
        .reset_index(drop=True)
    )


def graficar_comparativa(tabla, promedio_test):
    """Barras MAE y RMSE por modelo, con etiqueta directa y acento en ganador."""
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12})
    fig, ax = plt.subplots(figsize=(13, 6), dpi=200)

    n = len(tabla)
    y = np.arange(n)
    ancho = 0.38

    mae_vals = tabla["MAE"].values
    rmse_vals = tabla["RMSE"].values
    nombres = tabla["Modelo"].values

    ganador = 0  # ya viene ordenado de menor a mayor RMSE

    # RMSE barras (mas claras, detras)
    ax.barh(
        y - ancho / 2,
        rmse_vals,
        ancho,
        color=[COLOR_ACENTO if i == ganador else COLOR_SECUNDARIO for i in range(n)],
        alpha=0.85,
        label="RMSE",
    )
    # MAE barras (mas oscuras, delante)
    ax.barh(
        y + ancho / 2,
        mae_vals,
        ancho,
        color=[COLOR_TEXTO if i == ganador else COLOR_BASE for i in range(n)],
        alpha=0.85,
        label="MAE",
    )

    # Etiquetas directas
    for i in range(n):
        etiqueta = " ← GANADOR" if i == ganador else ""
        ax.text(
            rmse_vals[i] + 3_000,
            y[i] - ancho / 2,
            f"RMSE: {rmse_vals[i]:,.0f}{etiqueta}",
            va="center",
            fontsize=10,
            fontweight="bold" if i == ganador else "normal",
            color=COLOR_ACENTO if i == ganador else COLOR_TEXTO,
        )
        ax.text(
            mae_vals[i] + 3_000,
            y[i] + ancho / 2,
            f"MAE: {mae_vals[i]:,.0f}",
            va="center",
            fontsize=10,
            color=COLOR_TEXTO,
        )

    ax.set_yticks(y)
    ax.set_yticklabels(nombres)
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"{v / 1000:,.0f} mil")
    )
    ax.set_xlabel("Viajeros/mes (error absoluto)")
    ax.invert_yaxis()
    for lado in ["top", "right"]:
        ax.spines[lado].set_visible(False)
    ax.grid(axis="x", color="#D4E2D6", lw=0.6)

    # Tabla AIC/BIC a la derecha (solo para ARIMA)
    info = tabla[tabla["AIC"].notna()]
    if len(info) > 0:
        tabla_txt = "Modelo con\ninformacion criterio:\n"
        for _, r in info.iterrows():
            tabla_txt += (
                f"{r['Modelo']} — AIC {r['AIC']:.1f}, BIC {r['BIC']:.1f}\n"
            )
        ax.text(
            1.01,
            0.02,
            tabla_txt.strip(),
            transform=ax.transAxes,
            fontsize=9,
            color=COLOR_TEXTO,
            va="bottom",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#F0F3F1", edgecolor="none"),
        )

    ax.set_title(
        "Desempeno comparativo de modelos (prueba 30%)",
        loc="left",
        fontsize=16,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=14,
    )
    rmse_ganador = rmse_vals[ganador]
    pct = 100 * rmse_ganador / promedio_test
    ax.text(
        0,
        1.03,
        f"El mejor modelo se equivoca ~{mae_vals[ganador] / 1000:,.0f} mil "
        f"viajeros/mes (MAE). RMSE = {rmse_ganador / 1000:,.0f} mil "
        f"({pct:.0f}% del promedio mensual de prueba).",
        transform=ax.transAxes,
        fontsize=11,
        color=COLOR_BASE,
    )

    fig.tight_layout()
    SALIDA.mkdir(exist_ok=True)
    ruta = SALIDA / "06_modelos_comparativa.png"
    fig.savefig(ruta, dpi=200, facecolor="white")
    plt.close(fig)
    return ruta


def main():
    serie = cargar_serie_total()
    train, test = dividir_serie(serie)

    print(f"Entrenamiento: {train.index.min():%Y-%m} a {train.index.max():%Y-%m} ({len(train)} meses)")
    print(f"Prueba: {test.index.min():%Y-%m} a {test.index.max():%Y-%m} ({len(test)} meses)")
    print(f"Promedio prueba: {test.mean():,.0f} viajeros/mes")
    print()
    print("Reentrenando los 5 modelos del Lab 1...")

    resultados = entrenar_modelos(train, test)
    tabla = construir_tabla(resultados)

    print()
    print(tabla.to_string(index=False, float_format="%.0f"))

    # Verificar fidelidad con Lab 1
    esperado = {
        "ARIMA(0, 1, 1)": (156000, 170738),
        "Holt-Winters": (178240, 191180),
        "Suavizamiento exponencial": (165373, 180598),
        "Seasonal naive": (207322, 219664),
        "Prophet": (226349, 244790),
    }
    print()
    print("Verificacion de fidelidad con Lab 1 (tolerancia 1%):")
    todo_ok = True
    for _, r in tabla.iterrows():
        if r["Modelo"] in esperado:
            e_mae, e_rmse = esperado[r["Modelo"]]
            tol_mae = abs(r["MAE"] - e_mae) / e_mae
            tol_rmse = abs(r["RMSE"] - e_rmse) / e_rmse
            ok = tol_mae < 0.01 and tol_rmse < 0.01
            status = "OK" if ok else "DIFERENTE"
            if not ok:
                todo_ok = False
            print(
                f"  {r['Modelo']:28s} MAE {r['MAE']:>10,.0f} (exp {e_mae:>10,}) "
                f"RMSE {r['RMSE']:>10,.0f} (exp {e_rmse:>10,}) [{status}]"
            )
    if todo_ok:
        print("  Todos los valores reproducen fielmente el Lab 1.")

    print()
    print("Figura:", graficar_comparativa(tabla, test.mean()))


if __name__ == "__main__":
    main()
