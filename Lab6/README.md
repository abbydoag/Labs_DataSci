# Laboratorio 6 - Analisis de redes sociales

Analisis de la estructura de participacion en YouTube a partir de datos de videos y comentarios sobre temas guatemaltecos.

## Estructura

| Archivo | Contenido |
|---|---|
| `Lab6.ipynb` | Ejercicios 1-4: carga, limpieza, exploratorio, red bipartita |
| `05_Proyecciones.ipynb` | Ejercicio 5: proyecciones autor-autor y video-video |
| `06_Topologia.ipynb` | Ejercicio 6: topologia, fragmentacion, aislamiento |
| `07_Comunidades.ipynb` | Ejercicio 7: deteccion de comunidades (Louvain) |
| `08_Centralidad.ipynb` | Ejercicio 8: centralidad, autores puente, videos articuladores |
| `09_Sentimiento.ipynb` | Ejercicio 9: analisis de sentimiento con lexico en espanol |
| `10_Conclusiones.ipynb` | Ejercicio 10: interpretacion, limitaciones, conclusiones |

## Datos

- `youtube_videos.csv` - 293 videos con 20 variables
- `youtube_comments.csv` - 406 comentarios con 17 variables

## Codigo compartido (`src/`)

| Modulo | Funcion |
|---|---|
| `config.py` | Rutas, constantes, colores, semilla |
| `datos.py` | Carga, normalizacion, integracion de datos |
| `texto.py` | Texto original vs limpio, emojis, hashtags, bigramas |
| `sentimiento.py` | Lexico de polaridad en espanol (tipo VADER) |
| `redes.py` | Construccion de bipartita, proyecciones, metricas |

## Requisitos

Python 3.12+

```bash
python3 -m venv "Lab6/.venv"
source "Lab6/.venv/bin/activate"
pip install -r requirements.txt
```

Dependencias principales: `pandas`, `networkx`, `matplotlib`, `seaborn`, `nltk`, `wordcloud`, `numpy`, `scipy`.

## Ejecucion

Los notebooks deben ejecutarse en orden (1 a 10). Cada uno importa de `src/` y es reproducible.

```bash
# Opcion 1: Jupyter
jupyter notebook

# Opcion 2: Ejecutar todos desde terminal
for nb in Lab6.ipynb 05_Proyecciones.ipynb 06_Topologia.ipynb 07_Comunidades.ipynb 08_Centralidad.ipynb 09_Sentimiento.ipynb 10_Conclusiones.ipynb; do
    jupyter nbconvert --to notebook --execute --inplace "$nb"
done
```

## Outputs

- `processed/` - Tablas de nodos y aristas de las redes
- `figuras/` - Visualizaciones generadas por los notebooks
