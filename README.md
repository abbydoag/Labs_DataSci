# Laboratorios de Data Science — Semestre II 2026

Laboratorios 1 y 2 sobre series de tiempo aplicadas a datos de migracion de
Guatemala (INGUAT). Laboratorio 3 sobre reconocimiento de imagenes del alfabeto
de Lenguaje de Senas Americano (ASL). Laboratorio 4 sobre analisis geoespacial
de la cianobacteria en los lagos de Atitlan y Amatitlan con imagenes Sentinel-2.
Laboratorio 5 sobre mineria de textos y analisis de sentimiento aplicados a la
clasificacion de tweets que se refieren o no a un desastre real. Laboratorio 6
sobre analisis de redes sociales en YouTube. Laboratorio 7 sobre prediccion de
salarios con Spark MLlib. Laboratorio 8 sobre analisis de viajes de taxis NYC
con DuckDB y Docker. Laboratorio 9 sobre visualizacion estatica aplicada al
Lab 1.

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
    │
├── Lab6/                       # Laboratorio 6: analisis de redes sociales en YouTube
│   ├── Lab6.ipynb              # Ejercicios 1-4: carga, limpieza, exploratorio, red bipartita
│   ├── 05_Proyecciones.ipynb  # Ejercicio 5: proyecciones autor-autor y video-video
│   ├── 06_Topologia.ipynb      # Ejercicio 6: topologia, fragmentacion, aislamiento
│   ├── 07_Comunidades.ipynb    # Ejercicio 7: deteccion de comunidades (Louvain)
│   ├── 08_Centralidad.ipynb    # Ejercicio 8: centralidad, autores puente, videos articuladores
│   ├── 09_Sentimiento.ipynb    # Ejercicio 9: analisis de sentimiento con lexico en espanol
│   ├── 10_Conclusiones.ipynb   # Ejercicio 10: interpretacion, limitaciones, conclusiones
│   ├── src/                    # Codigo compartido (config, datos, texto, sentimiento, redes)
│   ├── requirements.txt        # Dependencias del laboratorio
│   ├── youtube_videos.csv      # 293 videos con 20 variables
│   ├── youtube_comments.csv    # 406 comentarios con 17 variables
│   ├── processed/              # Tablas de nodos y aristas de las redes
│   └── figuras/                # Visualizaciones generadas por los notebooks
│
├── Lab7/                       # Laboratorio 7: prediccion de salarios con Spark MLlib
│   ├── 04_Segmentacion.ipynb   # KMeans sobre edad, antigüedad, horas
│   ├── 05_Regresion_Lineal.ipynb  # Pipeline de regresion lineal
│   ├── 06_Random_Forest.ipynb  # Pipeline de Random Forest
│   ├── 07_Evaluacion_2026.ipynb   # Evaluacion de ambos modelos sobre 2026T1
│   ├── 08_Analisis_Errores.ipynb  # Graficos de residuos y analisis por deciles
│   ├── src/                    # Codigo compartido (config, datos, modelos)
│   ├── requirements.txt        # Dependencias del laboratorio
│   ├── Base-de-datos-Personas-ENEIC-*.xlsx  # Bases de datos ENEIC 2025-2026
│   ├── processed/              # Parquets generados (2025 y 2026)
│   ├── modelos/                # Modelos entrenados guardados
│   └── figuras/                # Graficos generados
│
├── Lab8/                       # Laboratorio 8: analisis de taxis NYC con DuckDB
│   ├── Dockerfile              # Imagen Python 3.11.14 + DuckDB 1.5.5
│   ├── metabase.Dockerfile     # Imagen Metabase v0.63.19 + driver DuckDB
│   ├── docker-compose.yml      # Servicios lab (JupyterLab) y metabase
│   ├── notebooks/              # Cuadernos 01-08 (ambiente, consultas, exploratorio, benchmark, indicadores, analisis completo, discusion)
│   ├── sql/                    # Consultas SQL (vistas, ejercicios 2-8)
│   ├── scripts/                # download_data.py, consultas.py
│   ├── docs/                   # consultas.md, tablero.md
│   ├── data/raw/               # Datos de TLC (Parquet), no se versionan
│   ├── data/processed/         # Figuras y benchmark, se regeneran
│   └── requirements.txt        # Dependencias del laboratorio
│
└── Lab9/                       # Laboratorio 9: visualizacion estatica (infografia del Lab 1)
    ├── pronostico.py           # Inciso 7: proyeccion visual del modelo ganador (ARIMA)
    ├── cuadrante_comparativo.py # Inciso 5: cuadrante comparativo de series
    ├── modelos_comparativa.py  # Inciso 6: comparativa de modelos (MAE, RMSE)
    ├── figuras/                # Figuras PNG de los incisos 5, 6 y 7
    └── Laboratorio 9. Visualización. 2026.pdf  # Instrucciones del laboratorio
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

## Laboratorio 6: analisis de redes sociales en YouTube

El laboratorio analiza la estructura de participacion en YouTube a partir de
datos de videos y comentarios sobre temas guatemaltecos. Son 293 videos con 20
variables y 406 comentarios con 17 variables. Los archivos `youtube_videos.csv`
y `youtube_comments.csv` **si se versionan** porque son pequenos.

El laboratorio trae su propio entorno virtual con Python 3.12+. Desde la
carpeta `Lab6`:

```
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Dependencias principales: `pandas`, `networkx`, `matplotlib`, `seaborn`, `nltk`,
`wordcloud`, `numpy`, `scipy`.

Los notebooks se corren en orden (1 a 10). `Lab6.ipynb` cubre los ejercicios 1-4
(carga, limpieza, exploratorio, red bipartita). Los cuadernos 05-10 cubren
proyecciones, topologia, comunidades (Louvain), centralidad, sentimiento con
lexico en espanol y conclusiones. Cada uno importa de `src/` que contiene los
modulos compartidos: `config.py`, `datos.py`, `texto.py`, `sentimiento.py` y
`redes.py`.

Las figuras se escriben en `Lab6/figuras/` y las tablas de nodos y aristas en
`Lab6/processed/`, ambos versionados.

## Laboratorio 7: prediccion de salarios con Spark MLlib

Analisis de salarios con datos de la Encuesta Nacional de Ingresos y Gastos de
los Hogares (ENEIC) de Guatemala. Son 40,361 registros de 2025T1-T3 para
entrenamiento, 12,664 de 2025T4 para validacion y 2026T1 para prueba final.
Poblacion: asalariados de 15+ anios con salario positivo.

El laboratorio usa **PySpark 3.5** que requiere **Java 17**. Desde la carpeta
`Lab7`:

```
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
export JAVA_HOME=/opt/homebrew/opt/openjdk@17  # macOS
```

Los archivos Excel de ENEIC (`Base-de-datos-Personas-ENEIC-*.xlsx`) **si se
versionan**. Los notebooks se corren en orden: 04 (Segmentacion con KMeans) → 05
(Regresion Lineal) → 06 (Random Forest) → 07 (Evaluacion 2026) → 08 (Analisis
de Errores). El inciso 4 genera `processed/eneic_2025.parquet` y
`processed/eneic_2026.parquet` si no existen (tarda ~2 min).

**Modelos entrenados:**

| Modelo | RMSE validacion | R2 validacion |
|--------|----------------|---------------|
| Referencia (media) | 2,889 | -0.003 |
| Regresion lineal | 2,186 | 0.426 |
| Random Forest | 1,987 | 0.523 |

Random Forest gana porque captura interacciones (educacion x categoria
ocupacional) que el lineal no puede. Los modelos entrenados se guardan en
`Lab7/modelos/` y las figuras en `Lab7/figuras/`, ambos versionados.

## Laboratorio 8: analisis de viajes de taxis NYC con DuckDB

Analisis de los datos de NYC TLC Trip Record Data (2024-2026) usando DuckDB y
Docker. El laboratorio vive en la carpeta `Lab8/` del repositorio de
laboratorios del equipo, no en un fork aparte. El primer commit de la carpeta
es una copia sin cambios del repositorio base del docente (`menene/duckdb`).

Requisitos: **Docker Desktop** con Docker Compose y unos **10 GB libres**. Las
dos imagenes ocupan 1.16 GB (`lab`) y 1.83 GB (`metabase`), y los datos de
2026 unos 500 MB.

```
cd Lab8
docker compose up -d --build
docker compose ps
```

La primera construccion descarga la imagen de Python, la de Java (Temurin 21),
Metabase y el driver de DuckDB, y tarda varios minutos.

| Servicio | Direccion | Que es |
|---|---|---|
| `lab` | http://localhost:8888 | JupyterLab, sin contrasena |
| `metabase` | http://localhost:3000 | Metabase con driver DuckDB |

Herramientas disponibles: en `lab`, Python 3.11.14, DuckDB 1.5.5, pandas 3.0.6,
pyarrow 25.0.1, matplotlib 3.11.2, requests 2.34.2, JupyterLab 4.6.4; en
`metabase`, Java 21, Metabase v0.63.19 y el driver de DuckDB 1.5.5.0.

Los datos se descargan con `scripts/download_data.py` que consulta al servidor
de la TLC que meses estan publicados. Los archivos se guardan en
`data/raw/<tipo>/<anio>/` y **no se versionan**. El script tambien baja
`taxi_zone_lookup.csv`.

Los cuadernos se corren en orden dentro del contenedor `lab`, desde JupyterLab
o desde la terminal:

```
docker compose exec lab jupyter nbconvert --to notebook --execute --inplace notebooks/01_Ambiente_y_Descarga.ipynb
docker compose exec lab jupyter nbconvert --to notebook --execute --inplace notebooks/02_Consultas_Parquet.ipynb
# ... hasta 08_Discusion.ipynb
```

El benchmark compara consultar Parquet directamente vs tabla materializada en
DuckDB. La tabla materializada es 16-20x mas rapida, pero tarda 12-28s en
crearse. Conviene para consultas repetidas (tableros), no para exploracion.

El tablero en Metabase contiene 6 indicadores principales: viajes diarios por
tipo, ingreso promedio por viaje, propina por metodo de pago, velocidad por
hora del dia, metodo de pago mas usado y viajes por dia de semana.

## Laboratorio 9: visualizacion estatica

Infografia de una pagina que sintetiza el Lab 1 (series de tiempo de la Base de
Migracion 2009-2026, INGUAT/IGM) para un directivo no tecnico. Contiene el
codigo de los incisos 5, 6 y 7 (bloques 3 y 4).

El laboratorio usa el mismo entorno virtual del Lab 1. Desde la raiz del
repositorio:

```
Lab\ 1/.venv/bin/python Lab9/pronostico.py
```

Lee `Lab 1/df/Base_Migracion_2009-2026jun.csv` y genera
`Lab9/figuras/07_pronostico_intervalo.png`. El script `pronostico.py`
reconstruye la serie total (turistas + excursionistas), la division 70/30 y el
ARIMA(0,1,1) sobre log1p que gano en el Lab 1 por menor RMSE. El intervalo del
95% se calcula con `get_forecast().conf_int()` en escala log y se regresa a
viajeros.

El script `cuadrante_comparativo.py` responde con evidencia: cual serie tiene
mayor estacionalidad, crecimiento, volatilidad y cual fue mas golpeada por la
pandemia. El script `modelos_comparativa.py` contrasta el desempeno de los 5
algoritmos entrenados en el Lab 1 (ARIMA, Holt-Winters, Suavizamiento
exponencial, Seasonal naive, Prophet) usando MAE y RMSE.

Hallazgo del inciso 7: el modelo se entreno hasta marzo de 2021, en plena
pandemia, y proyecta un nivel plano de 88,319 viajeros al mes. La serie real se
recupero a 200-400 mil. El intervalo crece de forma exponencial al volver de la
escala log y llega a 20.6 millones en junio de 2026, por eso el eje se corta en
600 mil y el corte se rotula en la figura en lugar de ocultarlo.

Las figuras se escriben en `Lab9/figuras/` y **si se versionan** porque la
infografia y sus graficas son el entregable del laboratorio.

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
