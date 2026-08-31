# Laboratorios de Data Science — Semestre II 2026

Laboratorios 1 y 2 sobre series de tiempo aplicadas a datos de migracion de
Guatemala (INGUAT). Laboratorio 3 sobre reconocimiento de imagenes del alfabeto
de Lenguaje de Senas Americano (ASL). Laboratorio 4 sobre analisis geoespacial
de la cianobacteria en los lagos de Atitlan y Amatitlan con imagenes Sentinel-2.
Laboratorio 5 sobre mineria de textos y analisis de sentimiento aplicados a la
clasificacion de tweets que se refieren o no a un desastre real.

## Estructura del proyecto

```
├── Lab 1/                      # Laboratorio 1: Análisis exploratorio y modelado clásico
│   ├── Lab1.ipynb              # Notebook principal (ARIMA, Holt-Winters, Prophet)
│   └── Datos/                  # Base_Migracion_2009-2026jun.csv
│
├── Lab2/                       # Laboratorio 2: Deep Learning (LSTM) y catch22
│   ├── LSTM_Regiones.ipynb     # LSTM + catch22 para series de Región dos
│   ├── LSMT_TotalMensual.ipynb # LSTM + catch22 para serie total mensual
│   ├── lab2-seriepaises.ipynb  # LSTM + catch22 para series de País
│   └── df/                     # Datos fuente
│
├── Lab3/                       # Laboratorio 3: CNN para el alfabeto ASL
│   ├── Lab3.ipynb              # Indice y guia de reproduccion
│   ├── 01_EDA.ipynb            # Analisis exploratorio (ejercicios 1 y 2)
│   ├── 02_Preprocesamiento.ipynb # Preprocesamiento de imagenes (ejercicio 3)
│   ├── 03_Modelos_y_Plan.ipynb # Arquitecturas y plan de procesamiento
│   ├── requirements.txt        # Dependencias del laboratorio
│   └── data/                   # Datos derivados, no se versionan
│
├── Lab4/                       # Laboratorio 4: cianobacteria en Atitlan y Amatitlan
│   │
│   │   # Parte 1: analisis geoespacial
│   ├── Lab4.ipynb              # Indice y guia de reproduccion
│   ├── 01_Descarga_Datos.ipynb # API de Sentinel-2 y descarga (ejercicios 1 y 2)
│   ├── 02_Indices.ipynb        # Cianobacteria, NDVI y NDWI (ejercicio 3)
│   ├── 03_Analisis_Temporal.ipynb      # Evolucion y picos (ejercicio 4)
│   ├── 04_Analisis_Espacial.ipynb      # Mapas y persistencia (ejercicio 5)
│   ├── 05_Correlaciones_y_Comparacion.ipynb # Correlaciones y lagos (ejercicios 6 y 7)
│   ├── 06_Analisis_Adicional.ipynb     # Exploratorio adicional (ejercicio 8)
│   ├── Informe_Lab4.pdf        # Informe para publico no tecnico
│   │
│   │   # Parte 2: modelos de aprendizaje automatico
│   ├── Lab4_Parte2.ipynb       # Indice y resultados principales
│   ├── 07_PrepDatos_ML.ipynb   # Conjunto de datos y exploratorio (ejercicio 1)
│   ├── 08_VarRespuesta_SelVar_DivDatos.ipynb # Respuesta y predictoras (ejercicios 2 y 3)
│   ├── 09_Modelos_ML.ipynb     # Los tres modelos y su evaluacion (ejercicios 4 y 5)
│   ├── 10_Validacion_Espacial_Temporal.ipynb # Bloques y fechas (ejercicio 6)
│   ├── 11_Generalizacion_Lagos.ipynb   # Transferencia entre lagos (ejercicio 7)
│   ├── 12_Interpretabilidad.ipynb      # Importancia y SHAP (ejercicio 8)
│   ├── 13_Mapas_Predictivos.ipynb      # Mapas de probabilidad (ejercicio 9)
│   ├── 14_Conclusiones.ipynb   # Analisis y limitaciones (ejercicio 10)
│   ├── Informe_Lab4_Parte2.pdf # Informe tecnico de la Parte 2
│   │
│   ├── src/                    # Codigo compartido por los notebooks
│   ├── geojson/                # Poligonos de los dos lagos
│   ├── requirements.txt        # Dependencias del laboratorio
│   └── data/                   # Escenas y derivados, no se versionan
└── Lab5/                       # Laboratorio 5: clasificacion de tweets sobre desastres
    ├── Lab5.ipynb              # Limpieza, frecuencias, n-gramas, modelos y funcion (ejercicios 1 a 7)
    ├── 08_Analisis_Sentimiento.ipynb    # Polaridad con VADER y decision sobre los emoticones (ejercicio 8)
    ├── 09_Tweets_Extremos.ipynb         # Los diez extremos y el contraste entre categorias (ejercicio 9)
    ├── 10_Modelo_con_Negatividad.ipynb  # Variable de negatividad y reentrenamiento (ejercicio 10)
    ├── Informe_Lab5.pdf        # Informe con los once ejercicios (ejercicio 11)
    ├── informe.py              # Script que regenera el informe
    ├── src/                    # Codigo compartido por los cuadernos 08 al 10
    ├── requirements.txt        # Dependencias del laboratorio
    ├── data/                   # train.csv y test.csv de Kaggle
    └── processed/              # Corpus limpio y puntuaciones de sentimiento
```

## Laboratorio 3: datos y entorno

El dataset ASL Alphabet (`grassknoted/asl-alphabet`, 87,000 imagenes, cerca de
1 GB) **no esta en el repositorio**. Se descarga con la API de Kaggle hacia
`~/.cache/kagglehub`, fuera del proyecto. Hace falta un token propio en
`~/.kaggle/access_token`, generado en kaggle.com/settings.

Los notebooks se corren en orden. `01_EDA.ipynb` descarga el dataset y deja la
division en `data/division.csv`, `02_Preprocesamiento.ipynb` genera los tensores
en `data/procesado/` y `03_Modelos_y_Plan.ipynb` los consume.

El laboratorio trae su propio entorno virtual con Python 3.13.5. Desde la
carpeta `Lab3`:

```
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

`requirements.txt` fija solo las dependencias que los notebooks importan. En
Jupyter o VS Code hay que seleccionar el interprete `.venv` antes de correr las
celdas. El entorno no se versiona, esta en el `.gitignore`.

Los modelos usan PyTorch con backend MPS, disponible en equipos Apple con chip
propio. Si no hay MPS el codigo cae a CPU sin cambios.

## Laboratorio 4: datos y entorno

Las imagenes vienen de la coleccion `SENTINEL2_L1C` del Copernicus Data Space
Ecosystem, accedida por programa con el modulo `openeo`. Se usan exclusivamente
las 22 fechas que fija el enunciado, 11 por lago. La eleccion de L1C sobre L2A
es un resultado del propio laboratorio y esta explicada en `Lab4/Lab4.ipynb`: el
script de cianobacteria esta calibrado para L1C y sobre L2A el indice se rompe
en agua muy clara.

No se descargan escenas completas. Para cada fecha se pide al servidor un cubo
recortado al rectangulo del lago, limitado a un solo dia y a 10 de las 13 bandas,
a 20 metros por pixel. Los GeoTIFF resultantes **no se versionan**: son varios
cientos de MB y se reconstruyen con el modulo de descarga. `Lab4/data/` esta en
el `.gitignore`.

El indice de cianobacteria usa el script oficial CyanoLakes Chlorophyll-a de
Sentinel Hub, traducido a Python en `src/indices.py` sin cambiar ninguna formula
ni ningun umbral. Se traduce para obtener el valor numerico del indice, que el
script original no devuelve, y para que el calculo quede reproducible.

El laboratorio trae su propio entorno virtual con Python 3.13.5. Desde la
carpeta `Lab4`:

```
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

El acceso a Sentinel-2 necesita una cuenta gratuita del Copernicus Data Space
Ecosystem. La autenticacion es un flujo de codigo de dispositivo que se confirma
una vez en el navegador; `openeo` guarda el token y las corridas siguientes no
piden nada. **No hay ninguna contrasena en el repositorio.**

```
.venv/bin/python -m src.descarga --login   # autenticar una vez
.venv/bin/python -m src.descarga           # bajar las 22 escenas
.venv/bin/python -m src.descarga --estado  # ver que hay en disco
```

Los notebooks se corren en orden despues de la descarga.

## Laboratorio 4, Parte 2: modelos de aprendizaje automatico

La segunda parte usa los rasters de la primera para entrenar modelos que
identifiquen zonas con alta presencia de cianobacteria. Es un problema de
clasificacion binaria: dado el espectro de un pixel de agua, se predice si supera
o no el nivel de vigilancia de 10 ug/L de la OMS.

El conjunto de datos tiene 3,759,121 observaciones, una por pixel de agua valida
en cada una de las 22 escenas, de las que el 1.18% son positivas. Se construye
con `datos.construir_dataset_ml()` y no se versiona.

Lo que decide este laboratorio es la fuga de datos. La etiqueta se construye
umbralando la clorofila, la clorofila es un polinomio del NDCI y el NDCI sale de
B04 y B05, asi que al despejar resulta que "chl > 10" equivale exactamente a
"B05 > 1.636 * B04": una desigualdad lineal entre dos columnas de la tabla. Un
modelo que reciba esas dos bandas devuelve un ROC-AUC de 1.0000 sin haber
aprendido nada. Por eso quedan fuera B04, B05, el NDCI, la clorofila, el NDVI y
el FAI, y el conjunto final tiene 16 predictoras. La lista de exclusiones con su
motivo esta en `src/ml.py`.

Gana XGBoost, con recall de 0.9729 y precision de 0.8429 sobre el conjunto de
prueba con la prevalencia real. Se compara con F2 y no con F1 porque el falso
negativo es el error grave: un falso positivo manda a alguien a muestrear una
zona limpia y se corrige en dias, mientras que una floracion no detectada no
genera ninguna senal que permita corregirla.

Las cinco dependencias que agrega la Parte 2 —scikit-learn, xgboost, shap,
geopandas y pyarrow— ya estan en `requirements.txt`. Los cuadernos 07 al 14 se
corren en orden despues de los seis de la Parte 1.

## Laboratorio 5: datos y entorno

El conjunto es *Natural Language Processing with Disaster Tweets* de Kaggle:
7,613 tweets etiquetados segun se refieran o no a un desastre real. Es pequeno,
1.4 MB, asi que `Lab5/data/` **si se versiona** y no hace falta descargar nada.
En `Lab5/processed/` quedan el corpus ya limpio y las puntuaciones de
sentimiento, que los cuadernos 08 al 10 leen en lugar de recalcular.

El laboratorio trae su propio entorno virtual con Python 3.13.5. Desde la
carpeta `Lab5`:

```
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

`Lab5.ipynb` cubre los ejercicios 1 al 7 y se corre solo. Los cuadernos 08, 09 y
10 cubren el resto y se corren en ese orden, porque el 08 escribe el archivo de
sentimiento que los otros dos consumen. El informe se regenera al final:

```
.venv/bin/python informe.py
```

El analisis de polaridad usa **VADER** (Hutto y Gilbert, 2014) a traves del
paquete `vaderSentiment`, que trae el lexico incluido y no descarga nada en
tiempo de ejecucion. **TextBlob** entra solo como lexico de contraste, para
comprobar que las conclusiones no dependen de haber elegido uno en particular.
Las figuras se escriben en `Lab5/figuras/`, que esta en el `.gitignore` porque
se regeneran corriendo los cuadernos.

### Dos decisiones que conviene conocer antes de reejecutar

La primera es que **hay dos limpiezas distintas y es a proposito**. La del
ejercicio 3 deja el texto en minusculas, sin puntuacion, sin digitos y sin
palabras vacias, y es la que alimenta a los clasificadores. Para el analisis de
sentimiento se usa una segunda, mucho mas suave, que conserva mayusculas,
signos de admiracion, negaciones y emoticones. La diferencia no es cosmetica: el
7.46% de los tweets cambia de signo segun cual de las dos reciba VADER, porque
al borrar las negaciones `not bad` se contabiliza como `bad`.

La segunda es que **el corpus versionado no esta lematizado**. El ejercicio 3
envuelve al lematizador de WordNet en un `try` que cae a la identidad si el
corpus no esta descargado, y en el entorno donde se corrio esa fue la rama que
se tomo. Comprobado sobre las 7,613 filas, `texto.limpieza_clasificacion` con
`lematizar=False` reproduce el 99.92% del corpus guardado y con `lematizar=True`
solo el 40.18%. Por eso el interruptor viene desactivado: si se lematizara en
`src` pero no en `processed`, el texto de un tweet nuevo dejaria de parecerse al
de entrenamiento y la funcion de clasificacion perderia exactitud sin aviso.

### Resultados principales

El mejor modelo es la **regresion logistica** con TF-IDF de unigramas y
bigramas, F1 de 0.7581. La seleccion merece una nota: sobre la particion 80/20
con semilla 42 ganaba Naive Bayes con F1 de 0.7734, pero al promediar sobre
quince particiones el orden se invierte y la regresion logistica gana por 1.4
puntos, muy por encima de la desviacion de ambos. La ventaja de Naive Bayes
existia solo en esa particion.

Los tweets de desastre **si son mas negativos**, con un efecto moderado: la
probabilidad de que uno tomado al azar sea mas negativo que uno de la otra
categoria es 0.6297 contra el 0.50 del azar. Los dos lexicos coinciden en la
direccion.

La variable de negatividad del ejercicio 10 **no mejora el clasificador**. Sobre
los mismos tweets de validacion arregla 30 clasificaciones y rompe 26 (McNemar,
p = 0.689). La razon es que las palabras que aportan negatividad en este corpus
—`fire`, `disaster`, `bomb`, `killed`— son el vocabulario de desastre, que el
TF-IDF ya usa como predictoras con pesos aprendidos de los datos: la negatividad
no es informacion nueva sino una version comprimida de la que el modelo ya
tenia.

## Nota sobre los informes

Para los laboratorios 1 a 3 no se incluye un archivo PDF por separado. Los
notebooks (`.ipynb`) ya contienen el analisis completo con explicaciones,
interpretaciones, graficas y conclusiones integradas en celdas markdown,
cumpliendo con lo indicado en las instrucciones del laboratorio.

El laboratorio 4 si incluye dos PDF. `Lab4/Informe_Lab4.pdf` corresponde a la
Parte 1 y esta dirigido a ambientalistas sin conocimientos de programacion, como
pide ese enunciado: resume los hallazgos sin codigo. `Lab4/Informe_Lab4_Parte2.pdf`
corresponde a la Parte 2 y es tecnico, con las tablas de metricas, la comparacion
de las estrategias de validacion, la interpretacion con SHAP y los mapas
predictivos. Los dos se regeneran con `informe.py` e `informe_parte2.py`
respectivamente. El detalle completo sigue estando en los notebooks.

El laboratorio 5 tambien incluye PDF. `Lab5/Informe_Lab5.pdf` recoge los once
ejercicios del enunciado —la descripcion del conjunto, la limpieza, las
frecuencias y los n-gramas, los tres modelos, la funcion de clasificacion, el
analisis de sentimiento, los tweets extremos y la variable de negatividad— con
sus tablas y figuras referenciadas en el texto. Se regenera con `informe.py`, que
recalcula todas las cifras desde `data/` y `processed/` para que el documento no
pueda desincronizarse de los datos.
