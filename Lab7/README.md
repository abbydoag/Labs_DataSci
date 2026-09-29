# Lab 7: Spark MLlib

Análisis de salarios con datos de la ENEIC (Guatemala). Segmentación con KMeans, regresión lineal y Random Forest usando PySpark.

**Equipo:** Abby Donis (22440), Hansel Lopez (19026), Fabian Prado (23427)

## Estructura

```
Lab7/
├── 04_Segmentacion.ipynb      KMeans sobre edad, antigüedad, horas
├── 05_Regresion_Lineal.ipynb  Pipeline de regresión lineal
├── 06_Random_Forest.ipynb     Pipeline de Random Forest
├── 07_Evaluacion_2026.ipynb   Evaluación de ambos modelos sobre 2026T1
├── 08_Analisis_Errores.ipynb  Gráficos de residuos y análisis por deciles
├── Lab7.ipynb                 Incisos 1-3 (Colab, versión vieja)
├── src/
│   ├── config.py              Rutas, constantes, etiquetas
│   ├── datos.py               Carga y filtrado de Excels a Parquet
│   └── modelos.py             Pipeline compartido, métricas, grilla
├── processed/                 Parquets generados (2025 y 2026)
├── modelos/                   Modelos entrenados guardados
├── figuras/                   Gráficos generados
├── *.xlsx                     Bases de Personas ENEIC
└── requirements.txt
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m ipykernel install --user --name="lab7" --display-name="Python (Lab 7)"
```

**Java:** PySpark 3.5 requiere Java 17. Si tienes otra versión:

```bash
export JAVA_HOME=/opt/homebrew/opt/openjdk@17  # macOS
```

## Ejecución

Los notebooks se ejecutan en orden: 04 → 05 → 06 → 07 → 08.

El inciso 4 genera `processed/eneic_2025.parquet` y `processed/eneic_2026.parquet` si no existen (tarda ~2 min). Los incisos siguientes leen de ahí.

Para ejecutar desde terminal:

```bash
export JAVA_HOME=/opt/homebrew/opt/openjdk@17
jupyter nbconvert --to notebook --execute --inplace 06_Random_Forest.ipynb
```

## Datos

- **Train:** 2025T1-T3 (40,361 registros después de filtros)
- **Validación:** 2025T4 (12,664 registros)
- **Prueba final:** 2026T1

Población: asalariados de 15+ años con salario positivo.

## Modelos

| Modelo | RMSE validación | R2 validación |
|--------|----------------|---------------|
| Referencia (media) | 2,889 | -0.003 |
| Regresión lineal | 2,186 | 0.426 |
| Random Forest | 1,987 | 0.523 |

Random Forest gana porque captura interacciones (educación × categoría ocupacional) que el lineal no puede.
