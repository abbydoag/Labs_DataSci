# Laboratorios de Data Science — Semestre II 2026

Laboratorios 1 y 2 sobre series de tiempo aplicadas a datos de migracion de
Guatemala (INGUAT). Laboratorio 3 sobre reconocimiento de imagenes del alfabeto
de Lenguaje de Senas Americano (ASL). Laboratorio 4 sobre analisis geoespacial
de la cianobacteria en los lagos de Atitlan y Amatitlan con imagenes Sentinel-2.

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
└── Lab4/                       # Laboratorio 4: cianobacteria en Atitlan y Amatitlan
    ├── Lab4.ipynb              # Indice y guia de reproduccion
    ├── 01_Descarga_Datos.ipynb # API de Sentinel-2 y descarga (ejercicios 1 y 2)
    ├── 02_Indices.ipynb        # Cianobacteria, NDVI y NDWI (ejercicio 3)
    ├── 03_Analisis_Temporal.ipynb      # Evolucion y picos (ejercicio 4)
    ├── 04_Analisis_Espacial.ipynb      # Mapas y persistencia (ejercicio 5)
    ├── 05_Correlaciones_y_Comparacion.ipynb # Correlaciones y lagos (ejercicios 6 y 7)
    ├── 06_Analisis_Adicional.ipynb     # Exploratorio adicional (ejercicio 8)
    ├── Informe_Lab4.pdf        # Informe para publico no tecnico
    ├── src/                    # Codigo compartido por los notebooks
    ├── geojson/                # Poligonos de los dos lagos
    ├── requirements.txt        # Dependencias del laboratorio
    └── data/                   # Escenas y derivados, no se versionan
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

Las imagenes vienen de la coleccion `SENTINEL2_L2A` del Copernicus Data Space
Ecosystem, accedida por programa con el modulo `openeo`. Se usan exclusivamente
las 22 fechas que fija el enunciado, 11 por lago.

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

## Nota sobre los informes

Para los laboratorios 1 a 3 no se incluye un archivo PDF por separado. Los
notebooks (`.ipynb`) ya contienen el analisis completo con explicaciones,
interpretaciones, graficas y conclusiones integradas en celdas markdown,
cumpliendo con lo indicado en las instrucciones del laboratorio.

El laboratorio 4 si incluye `Lab4/Informe_Lab4.pdf`, porque el enunciado pide
expresamente un informe dirigido a ambientalistas sin conocimientos de
programacion. Ese documento resume los hallazgos sin codigo; el detalle tecnico
sigue estando en los notebooks.
