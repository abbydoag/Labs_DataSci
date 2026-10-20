# Lab 9 - Inciso 5: Cuadrante Comparativo del Laboratorio
# Responde con evidencia: ¿Cuál serie tiene mayor estacionalidad, crecimiento,
# volatilidad, y cuál fue más golpeada por la pandemia?
# Uso: Lab\ 1/.venv/bin/python Lab9/cuadrante_comparativo.py

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import linregress
from statsmodels.tsa.seasonal import STL

warnings.filterwarnings("ignore")

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "Lab 1" / "df" / "Base_Migracion_2009-2026jun.csv"
SALIDA = Path(__file__).resolve().parent / "figuras"

# Paleta consistente con pronostico.py
COLOR_HISTORIA = "#7F8F8B"
COLOR_OBSERVADO = "#0E4D45"
COLOR_ESTIMACION = "#3F8A26"
COLOR_TEXTO = "#1E2A28"
COLOR_ACENTO = "#C75C2E"  # Naranja para destacar ganadores


def cargar_datos():
    df = pd.read_csv(DATOS)
    df["Viajero"] = pd.to_numeric(df["Viajero"], errors="coerce")
    df = df[df["Tipo de Viajero"].isin(["Turista", "Excursionista"])].copy()
    df["Fecha"] = pd.to_datetime(
        dict(year=df["Año"], month=df["Mes cod"], day=1)
    )
    return df


def serie_mensual(df, filtro_col=None, filtro_val=None):
    """Construye serie mensual de viajeros internacionales."""
    d = df if filtro_col is None else df[df[filtro_col] == filtro_val]
    cal = pd.date_range(df["Fecha"].min(), df["Fecha"].max(), freq="MS")
    return (
        d.groupby("Fecha")["Viajero"]
        .sum()
        .reindex(cal, fill_value=0)
        .astype(float)
        .asfreq("MS")
    )


def fuerza_estacional(serie):
    """Fuerza de estacionalidad STL sobre log1p."""
    if len(serie) < 36:
        return np.nan
    stl = STL(np.log1p(serie), period=12, robust=True).fit()
    return max(0.0, 1 - np.var(stl.resid) / np.var(stl.seasonal + stl.resid))


def crecimiento_anual(serie):
    """Crecimiento anual pre-COVID (2009-2019) por regresión en tendencia."""
    pre = serie.loc[:"2019-12-01"]
    if len(pre) < 24:
        return np.nan
    x = np.arange(len(pre))
    reg = linregress(x, np.log1p(pre.to_numpy()))
    return 100 * (np.exp(12 * reg.slope) - 1)


def volatilidad_mensual(serie):
    """Volatilidad: desviación estándar de retornos log."""
    return 100 * np.std(np.diff(np.log1p(serie.to_numpy())), ddof=1)


def impacto_pandemia(serie):
    """Impacto 2020 vs 2019 en porcentaje."""
    t2019 = serie.loc["2019"].sum()
    t2020 = serie.loc["2020"].sum()
    if t2019 == 0:
        return np.nan
    return 100 * (t2020 / t2019 - 1)


def construir_tabla_comparativa():
    """Tabla comparativa de las 7 series del grupo."""
    df = cargar_datos()

    top3_paises = (
        df[df["Año"] <= 2022]
        .groupby("País")["Viajero"]
        .sum()
        .nlargest(3)
        .index.tolist()
    )
    top3_regiones = (
        df.groupby("Región dos")["Viajero"].sum().nlargest(3).index.tolist()
    )

    series = {"Total (T+E)": serie_mensual(df)}
    series.update(
        {p: serie_mensual(df, "País", p).loc[:"2022-12-01"] for p in top3_paises}
    )
    series.update(
        {r: serie_mensual(df, "Región dos", r) for r in top3_regiones}
    )

    filas = []
    for nombre, s in series.items():
        f_all = fuerza_estacional(s)
        f_pre = fuerza_estacional(s.loc[:"2019-12-01"])
        f_post = fuerza_estacional(s.loc["2022-01-01":])
        filas.append(
            {
                "Serie": nombre,
                "Fuerza completa": f_all,
                "Fuerza pre-pandemia": f_pre,
                "Fuerza post-pandemia": f_post,
                "Crecimiento anual %": crecimiento_anual(s),
                "Volatilidad %": volatilidad_mensual(s),
                "Impacto pandemia %": impacto_pandemia(s),
            }
        )
    return pd.DataFrame(filas)


def graficar_cuadrante(tabla):
    """Figura 2×2: un cuadrante por pregunta."""
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12})
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=200)

    tabla_ord = tabla.set_index("Serie")

    # Panel 1: Estacionalidad (pre-pandemia, más justo)
    ax = axes[0, 0]
    datos = tabla_ord["Fuerza pre-pandemia"].dropna().sort_values()
    ganador_pos = int(np.argmax(datos.values))
    colores = [COLOR_HISTORIA] * len(datos)
    colores[ganador_pos] = COLOR_ACENTO
    datos.plot.barh(ax=ax, color=colores)
    ax.set_title("Mayor estacionalidad (pre-2020)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Fuerza estacional STL")
    ax.set_xlim(0, 1)
    for i, (val, nombre) in enumerate(zip(datos.values, datos.index)):
        if not np.isnan(val):
            ax.text(val + 0.02, i, f"{val:.2f}", va="center", fontsize=10)
    ax.text(
        0.5,
        -0.15,
        "Nota: medida 2009-19; ventana completa da ~0.05\n"
        "porque el crash 2020 queda en el residuo STL",
        transform=ax.transAxes,
        fontsize=9,
        color=COLOR_TEXTO,
        style="italic",
    )

    # Panel 2: Crecimiento pre-COVID
    ax = axes[0, 1]
    datos = tabla_ord["Crecimiento anual %"].dropna().sort_values()
    ganador_pos = int(np.argmax(datos.values))
    colores = [COLOR_HISTORIA] * len(datos)
    colores[ganador_pos] = COLOR_ACENTO
    datos.plot.barh(ax=ax, color=colores)
    ax.set_title("Mayor crecimiento (anual pre-COVID)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Crecimiento anualizado (%)")
    for i, (val, nombre) in enumerate(zip(datos.values, datos.index)):
        if not np.isnan(val):
            ax.text(val + 0.3, i, f"{val:+.1f}%", va="center", fontsize=10)

    # Panel 3: Volatilidad
    ax = axes[1, 0]
    datos = tabla_ord["Volatilidad %"].dropna().sort_values()
    ganador_pos = int(np.argmax(datos.values))
    colores = [COLOR_HISTORIA] * len(datos)
    colores[ganador_pos] = COLOR_ACENTO
    datos.plot.barh(ax=ax, color=colores)
    ax.set_title("Mayor volatilidad mensual", fontsize=13, fontweight="bold")
    ax.set_xlabel("Volatilidad log (%)")
    for i, (val, nombre) in enumerate(zip(datos.values, datos.index)):
        if not np.isnan(val):
            ax.text(val + 1, i, f"{val:.1f}%", va="center", fontsize=10)

    # Panel 4: Impacto pandemia
    ax = axes[1, 1]
    datos = tabla_ord["Impacto pandemia %"].dropna().sort_values()
    ganador_pos = int(np.argmin(datos.values))  # Más negativo = más golpeado
    colores = [COLOR_HISTORIA] * len(datos)
    colores[ganador_pos] = COLOR_ACENTO
    datos.plot.barh(ax=ax, color=colores)
    ax.set_title("Más golpeada por pandemia (2020 vs 2019)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Caída (%)")
    for i, (val, nombre) in enumerate(zip(datos.values, datos.index)):
        if not np.isnan(val):
            ax.text(val + 1, i, f"{val:+.1f}%", va="center", fontsize=10)

    for ax in axes.flat:
        ax.grid(axis="x", color="#D4E2D6", lw=0.6)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.suptitle(
        "Cuadrante Comparativo: series analizadas",
        fontsize=16,
        fontweight="bold",
        y=0.98,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    SALIDA.mkdir(exist_ok=True)
    ruta = SALIDA / "05_cuadrante_comparativo.png"
    fig.savefig(ruta, dpi=200, facecolor="white")
    plt.close(fig)
    return ruta


def main():
    tabla = construir_tabla_comparativa()
    print("Tabla comparativa:")
    print(
        tabla.to_string(
            float_format=lambda x: f"{x:.3f}" if not np.isnan(x) else "n/d",
            index=False,
        )
    )
    print()
    print("Respuestas con evidencia:")
    t = tabla.set_index("Serie")
    print(
        f"1. Mayor estacionalidad: {t['Fuerza pre-pandemia'].idxmax()} "
        f"({t['Fuerza pre-pandemia'].max():.2f})"
    )
    print(
        f"2. Mayor crecimiento: {t['Crecimiento anual %'].idxmax()} "
        f"({t['Crecimiento anual %'].max():+.1f}% anual)"
    )
    print(
        f"3. Mayor volatilidad: {t['Volatilidad %'].idxmax()} "
        f"({t['Volatilidad %'].max():.1f}%)"
    )
    print(
        f"4. Más golpeada por pandemia: {t['Impacto pandemia %'].idxmin()} "
        f"({t['Impacto pandemia %'].min():+.1f}%)"
    )
    print()
    print("Figura:", graficar_cuadrante(tabla))


if __name__ == "__main__":
    main()
