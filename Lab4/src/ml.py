"""Aprendizaje automatico de la Parte 2 del Laboratorio 4.

Concentra lo que comparten los cuadernos 08 al 14: la variable respuesta, el
conjunto de predictoras libre de fuga, la ingenieria de caracteristicas, los
bloques espaciales y las metricas de evaluacion.

El punto delicado de toda la Parte 2 esta en `PREDICTORAS`. La etiqueta se
construye umbralando la clorofila, la clorofila es un polinomio del NDCI y el
NDCI sale de B04 y B05. Al despejar, `chl > 10` es identico a
`(B05 - B04) / (B05 + B04) > 0.2413494`, es decir `B05 > 1.636 * B04`: una sola
desigualdad lineal entre dos bandas. Cualquier modelo que reciba esas dos
bandas no predice nada, recalcula la etiqueta. Por eso B04, B05 y todo lo que
se derive de ellas quedan fuera, y el modulo expone la lista de exclusiones con
su motivo para que ningun cuaderno la reconstruya a mano.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import indices as ix

# --- Variable respuesta ----------------------------------------------------

# Nivel de vigilancia de la OMS para aguas recreativas con dominancia de
# cianobacteria. Es el mismo umbral que usa la Parte 1, definido en
# `indices.UMBRAL_ALTO_CHL`, y se importa de ahi para que las dos partes del
# laboratorio no puedan desincronizarse.
UMBRAL_CHL = ix.UMBRAL_ALTO_CHL

RESPUESTA = "alta_cianobacteria"

# NDCI equivalente al umbral de clorofila. Es la raiz real del polinomio
# 826.57*n^3 - 176.43*n^2 + 19*n + 4.071 = 10, y sirve para mostrar de forma
# explicita por que B04 y B05 no pueden ser predictoras.
UMBRAL_NDCI = 0.2413494071927058


def variable_respuesta(tabla: pd.DataFrame) -> pd.Series:
    """Etiqueta binaria: 1 si el pixel supera el umbral de la OMS."""
    return (tabla["chl"] > UMBRAL_CHL).astype("int8")


# --- Exclusiones por fuga de datos -----------------------------------------

# Cada entrada dice por que la variable no puede entrar al modelo. La cadena se
# imprime tal cual en el cuaderno 08, para que la justificacion viva junto a la
# regla y no en un comentario suelto.
EXCLUIDAS = {
    "chl": "Es la variable con la que se construye la respuesta.",
    "ndci": "chl es un polinomio del NDCI: la respuesta es NDCI > 0.2413.",
    "B04": "Denominador y numerador del NDCI. Con B05 reconstruye la etiqueta.",
    "B05": "Denominador y numerador del NDCI. Con B04 reconstruye la etiqueta.",
    "ndvi": "Se calcula con B04, una de las dos bandas que arman la respuesta.",
    "fai": "Se calcula con B04, una de las dos bandas que arman la respuesta.",
    "B10": (
        "Banda de cirrus. Se uso para filtrar nube, asi que por construccion "
        "vale menos de 0.01 en toda observacion que sobrevivio: no aporta."
    ),
    "lago": (
        "No es fuga, pero se deja fuera a proposito: con 10.7% de positivos en "
        "Amatitlan contra 0.04% en Atitlan, el modelo aprenderia el nombre del "
        "lago en vez de la senal espectral y el ejercicio 7 perderia sentido."
    ),
    "fecha": "Se reserva como variable de agrupacion para la validacion temporal.",
}


# --- Predictoras -----------------------------------------------------------

# Bandas que sobreviven al filtro de fuga. B04 y B05 quedaron fuera; B07 se
# conserva porque es borde rojo (783 nm) y no entra en ninguna formula de la
# respuesta, asi que aporta senal de clorofila obtenida de forma independiente.
BANDAS = ["B02", "B03", "B07", "B08", "B8A", "B11", "B12"]

# Indices y razones construidos solo con bandas permitidas.
DERIVADAS = [
    "ndwi",
    "mndwi",
    "ndmi",
    "razon_azul_verde",
    "nd_borde_verde",
    "brillo_visible",
]

# Caracteristicas espaciales. El enunciado las admite de forma explicita en el
# inciso 3.2.
ESPACIALES = ["x", "y", "dist_orilla_m"]

PREDICTORAS = BANDAS + DERIVADAS + ESPACIALES

# Que representa cada predictora y por que podria ayudar. Alimenta la tabla del
# inciso 3.2.
DESCRIPCION = {
    "B02": ("banda", "Azul, 490 nm. La clorofila-a absorbe con fuerza en el azul, "
                     "asi que el agua con mas fitoplancton se oscurece aqui."),
    "B03": ("banda", "Verde, 560 nm. Maximo de reflectancia del fitoplancton: "
                     "es la banda donde una floracion se ve verde."),
    "B07": ("banda", "Borde rojo, 783 nm. Reflectancia alta sobre agua cargada de "
                     "algas y casi nula sobre agua limpia. Es la senal de clorofila "
                     "mas fuerte que queda tras excluir B04 y B05."),
    "B08": ("banda", "Infrarrojo cercano, 842 nm. El agua limpia lo absorbe casi "
                     "por completo; lo que refleje delata material en suspension "
                     "o algas flotando."),
    "B8A": ("banda", "Infrarrojo cercano estrecho, 865 nm. Igual que B08 pero en una "
                     "ventana sin vapor de agua, util para separar bruma de material."),
    "B11": ("banda", "Infrarrojo de onda corta, 1610 nm. El agua lo absorbe siempre, "
                     "asi que sirve de referencia para saber cuanto de la senal es "
                     "sedimento y no algas."),
    "B12": ("banda", "Infrarrojo de onda corta, 2190 nm. Misma funcion que B11, y "
                     "juntas discriminan turbidez mineral de turbidez biologica."),
    "ndwi": ("indice", "(B03 - B08) / (B03 + B08). Cuanto se parece el pixel a agua "
                       "limpia. Cae cuando la superficie se llena de material."),
    "mndwi": ("indice", "(B03 - B11) / (B03 + B11). Version del NDWI con el SWIR, "
                        "menos sensible a vegetacion y mas estable en la orilla."),
    "ndmi": ("indice", "(B08 - B11) / (B08 + B11). Contraste infrarrojo cercano "
                       "contra onda corta; sube con biomasa flotante."),
    "razon_azul_verde": ("indice", "B02 / B03. Es la forma clasica de estimar "
                                   "clorofila-a en color del oceano: la razon cae "
                                   "cuando el pigmento absorbe azul y refleja verde."),
    "nd_borde_verde": ("indice", "(B07 - B03) / (B07 + B03). Contraste entre el borde "
                                 "rojo y el verde, analogo al NDCI pero armado con "
                                 "bandas que no intervienen en la respuesta."),
    "brillo_visible": ("indice", "B02 + B03. Brillo total en el visible, proxy de "
                                 "turbidez general del agua."),
    "x": ("espacial", "Coordenada este en UTM 15N. Ubica el pixel dentro del lago."),
    "y": ("espacial", "Coordenada norte en UTM 15N. Ubica el pixel dentro del lago."),
    "dist_orilla_m": ("espacial", "Distancia al borde del espejo de agua, en metros. "
                                  "Las floraciones se concentran en bahias someras y "
                                  "cerca de las desembocaduras, no en el centro."),
}


def caracteristicas(tabla: pd.DataFrame) -> pd.DataFrame:
    """Agrega las variables derivadas de `DERIVADAS` a una tabla de pixeles.

    Todas se calculan solo con bandas permitidas. Se devuelve una copia para no
    modificar la tabla que recibe el cuaderno.
    """
    t = tabla.copy()

    def nd(a: pd.Series, b: pd.Series) -> pd.Series:
        suma = a + b
        return ((a - b) / suma.where(suma != 0, np.nan)).astype("float32")

    if "ndwi" not in t.columns:
        t["ndwi"] = nd(t["B03"], t["B08"])
    t["mndwi"] = nd(t["B03"], t["B11"])
    t["ndmi"] = nd(t["B08"], t["B11"])
    t["nd_borde_verde"] = nd(t["B07"], t["B03"])
    t["razon_azul_verde"] = (t["B02"] / t["B03"].where(t["B03"] != 0, np.nan)).astype("float32")
    t["brillo_visible"] = (t["B02"] + t["B03"]).astype("float32")

    return t


# --- Muestra de entrenamiento ----------------------------------------------


def submuestra_entrenamiento(
    X: pd.DataFrame,
    y: pd.Series,
    razon: float = 1.0,
    semilla: int = 42,
) -> tuple[pd.DataFrame, pd.Series]:
    """Conserva todos los positivos y topa los negativos a `razon` por positivo.

    Con 84 negativos por cada positivo, entrenar sobre los 2.6 millones de filas
    del conjunto de entrenamiento cuesta minutos por modelo y hay que repetirlo
    en la validacion espacial, en la temporal y en los dos experimentos entre
    lagos. Bajar los negativos no pierde informacion de la clase rara, que es la
    que escasea, y deja el entrenamiento en segundos.

    El conjunto de prueba nunca se toca: se evalua siempre con la prevalencia
    real, de modo que la precision y el recall que se reportan son los que
    tendria el modelo sobre el lago completo.
    """
    pos = y[y == 1].index
    neg = y[y == 0].index

    n_neg = min(len(neg), int(round(len(pos) * razon)))
    neg_muestra = pd.Index(
        pd.Series(neg).sample(n=n_neg, random_state=semilla).values
    )

    idx = pos.union(neg_muestra)
    return X.loc[idx], y.loc[idx]


# --- Bloques espaciales ----------------------------------------------------


def asignar_bloques(tabla: pd.DataFrame, lado_m: float = 1000.0) -> pd.Series:
    """Etiqueta de bloque espacial de cada observacion.

    Las coordenadas ya vienen en EPSG:32615 (WGS 84 / UTM 15N), que es el
    sistema que pide el inciso 6.1 y en el que openEO entrego los rasters, asi
    que no hay que reproyectar nada: basta dividir metros entre metros.

    La etiqueta incluye el lago para que dos bloques de lagos distintos nunca
    compartan grupo, aunque cayeran en la misma celda de la cuadricula.
    """
    ix_x = np.floor(tabla["x"] / lado_m).astype("int64")
    ix_y = np.floor(tabla["y"] / lado_m).astype("int64")
    return tabla["lago"].astype(str) + "_" + ix_x.astype(str) + "_" + ix_y.astype(str)


def resumen_bloques(tabla: pd.DataFrame, lado_m: float = 1000.0) -> pd.DataFrame:
    """Cuantos bloques salen por lago y como se reparten las observaciones."""
    bloques = asignar_bloques(tabla, lado_m)
    t = tabla.assign(bloque=bloques)

    filas = []
    for lago, sub in t.groupby("lago"):
        por_bloque = sub.groupby("bloque").size()
        positivos = sub.groupby("bloque")[RESPUESTA].sum() if RESPUESTA in sub else None
        filas.append(
            {
                "lago": lago,
                "lado_m": lado_m,
                "bloques": len(por_bloque),
                "obs_min": int(por_bloque.min()),
                "obs_mediana": int(por_bloque.median()),
                "obs_max": int(por_bloque.max()),
                "bloques_con_positivos": (
                    int((positivos > 0).sum()) if positivos is not None else np.nan
                ),
            }
        )
    return pd.DataFrame(filas)


# --- Metricas --------------------------------------------------------------

ORDEN_METRICAS = ["Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "PR-AUC"]


def metricas(y_real, y_pred, y_prob) -> dict[str, float]:
    """Las cinco metricas que pide el inciso 5.1, mas el area bajo precision-recall.

    Se agrega PR-AUC porque con 1.18% de positivos la curva ROC se ve bien casi
    por construccion: la tasa de falsos positivos se divide entre 3.7 millones
    de negativos y casi cualquier modelo la deja cerca de cero. La curva
    precision-recall no tiene ese consuelo y es la que se usa en la literatura
    para clases raras.
    """
    from sklearn.metrics import (
        accuracy_score,
        average_precision_score,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )

    return {
        "Accuracy": accuracy_score(y_real, y_pred),
        "Precision": precision_score(y_real, y_pred, zero_division=0),
        "Recall": recall_score(y_real, y_pred, zero_division=0),
        "F1": f1_score(y_real, y_pred, zero_division=0),
        "ROC-AUC": roc_auc_score(y_real, y_prob),
        "PR-AUC": average_precision_score(y_real, y_prob),
    }


def tabla_metricas(resultados: dict[str, dict]) -> pd.DataFrame:
    """Convierte {modelo: metricas} en una tabla ordenada."""
    return (
        pd.DataFrame({n: {k: m[k] for k in ORDEN_METRICAS} for n, m in resultados.items()})
        .T[ORDEN_METRICAS]
        .round(4)
    )


# --- Protocolo de entrenamiento y evaluacion -------------------------------

# Hiperparametros elegidos en el cuaderno 9 con RandomizedSearchCV sobre el
# criterio PR-AUC. Se fijan aqui para que la validacion espacial, la temporal y
# los experimentos entre lagos comparen exactamente los mismos modelos y la
# unica diferencia entre corridas sea la particion de los datos.
HIPERPARAMETROS = {
    "Regresión Logística": {"C": 1.0, "l1_ratio": 1.0, "solver": "saga", "max_iter": 10000},
    "Random Forest": {
        "n_estimators": 300,
        "max_depth": 10,
        "min_samples_leaf": 5,
        "max_features": "log2",
    },
    "XGBoost": {
        "n_estimators": 400,
        "max_depth": 6,
        "learning_rate": 0.1,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "min_child_weight": 1,
        "tree_method": "hist",
        "eval_metric": "logloss",
    },
}

# La regresion logistica es la unica que necesita las variables estandarizadas.
NECESITA_ESCALA = {"Regresión Logística": True, "Random Forest": False, "XGBoost": False}


def construir_modelo(nombre: str, semilla: int = 42):
    """Instancia uno de los tres modelos con los hiperparametros del cuaderno 9."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from xgboost import XGBClassifier

    parametros = dict(HIPERPARAMETROS[nombre], random_state=semilla)
    if nombre == "Regresión Logística":
        return LogisticRegression(**parametros)
    if nombre == "Random Forest":
        return RandomForestClassifier(n_jobs=-1, **parametros)
    return XGBClassifier(n_jobs=-1, **parametros)


def entrenar_y_evaluar(
    nombre: str,
    X_ent: pd.DataFrame,
    y_ent: pd.Series,
    X_prueba: pd.DataFrame,
    y_prueba: pd.Series,
    semilla: int = 42,
    razon: float = 1.0,
) -> dict:
    """Entrena un modelo y lo evalua, con el mismo protocolo en todos los cuadernos.

    El protocolo tiene tres pasos y el orden importa:

    1. Se aparta el 30% del entrenamiento como validacion interna, **sin tocar
       su prevalencia**. Sirve solo para elegir el umbral.
    2. El 70% restante se submuestrea a `razon` negativos por positivo y ahi se
       ajusta el modelo.
    3. El umbral se elige maximizando F2 sobre la validacion interna, que si
       tiene la prevalencia real, y recien entonces se evalua sobre `X_prueba`.

    Elegir el umbral sobre la muestra balanceada seria un error: ahi la mitad de
    los pixeles son positivos y el corte optimo no se parece al que hace falta
    sobre un lago con 1.18%. Y elegirlo sobre `X_prueba` seria mirar la
    respuesta antes de contestar.
    """
    from sklearn.metrics import fbeta_score
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    # Si una particion se queda sin positivos no hay nada que aprender ni que
    # medir. Pasa en la validacion temporal de Atitlan, donde alguna fecha
    # aporta menos de diez pixeles positivos.
    if y_ent.sum() < 2 or y_prueba.sum() < 1:
        return {"valido": False, "n_pos_ent": int(y_ent.sum()), "n_pos_prueba": int(y_prueba.sum())}

    estratos = y_ent if y_ent.sum() >= 2 else None
    idx_fit, idx_val = train_test_split(
        y_ent.index, test_size=0.30, random_state=semilla, stratify=estratos
    )

    X_fit, y_fit = submuestra_entrenamiento(
        X_ent.loc[idx_fit], y_ent.loc[idx_fit], razon=razon, semilla=semilla
    )
    X_val, y_val = X_ent.loc[idx_val], y_ent.loc[idx_val]

    escalar = NECESITA_ESCALA[nombre]
    escalador = StandardScaler().fit(X_fit) if escalar else None

    def preparar(XX):
        return escalador.transform(XX) if escalar else XX

    modelo = construir_modelo(nombre, semilla)
    modelo.fit(preparar(X_fit), y_fit)

    prob_val = modelo.predict_proba(preparar(X_val))[:, 1]
    if y_val.sum() > 0:
        rejilla = np.linspace(0.05, 0.99, 95)
        puntajes = [
            fbeta_score(y_val, (prob_val >= u).astype(int), beta=2, zero_division=0)
            for u in rejilla
        ]
        umbral = float(rejilla[int(np.argmax(puntajes))])
    else:
        umbral = 0.5

    prob = modelo.predict_proba(preparar(X_prueba))[:, 1]
    pred = (prob >= umbral).astype(int)

    resultado = metricas(y_prueba, pred, prob)
    resultado["F2"] = fbeta_score(y_prueba, pred, beta=2, zero_division=0)
    resultado["umbral"] = umbral
    resultado["valido"] = True
    resultado["n_ent"] = len(y_fit)
    resultado["n_prueba"] = len(y_prueba)
    resultado["n_pos_prueba"] = int(y_prueba.sum())
    return resultado


def promedio_folds(folds: list[dict]) -> dict:
    """Media de las metricas sobre los folds validos, con su desviacion."""
    validos = [f for f in folds if f.get("valido")]
    if not validos:
        return {}
    salida = {}
    for clave in ORDEN_METRICAS + ["F2"]:
        valores = [f[clave] for f in validos]
        salida[clave] = float(np.mean(valores))
        salida[clave + "_sd"] = float(np.std(valores))
    salida["folds"] = len(validos)
    return salida
