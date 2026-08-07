# Laboratorios de Data Science — Semestre II 2026

Laboratorios 1 y 2 sobre series de tiempo aplicadas a datos de migracion de
Guatemala (INGUAT). Laboratorio 3 sobre reconocimiento de imagenes del alfabeto
de Lenguaje de Senas Americano (ASL).

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
└── Lab3/                       # Laboratorio 3: CNN para el alfabeto ASL
    ├── Lab3.ipynb              # Indice y guia de reproduccion
    ├── 01_EDA.ipynb            # Analisis exploratorio (ejercicios 1 y 2)
    ├── 02_Preprocesamiento.ipynb # Preprocesamiento de imagenes (ejercicio 3)
    ├── 03_Modelos_y_Plan.ipynb # Arquitecturas y plan de procesamiento
    ├── requirements.txt        # Dependencias del laboratorio
    └── data/                   # Datos derivados, no se versionan
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

## Nota sobre el informe

No se incluye un archivo PDF por separado. Los notebooks (`.ipynb`) ya contienen el análisis completo con explicaciones, interpretaciones, gráficas y conclusiones integradas en celdas markdown, cumpliendo con lo indicado en las instrucciones del laboratorio.
