# Lab 8 - DuckDB

Repositorio base del laboratorio 8 del curso **CC3084 - Data Science**
(Universidad del Valle de Guatemala, Ciclo 2, 2026).

Este es el repositorio **proporcionado por el docente**. Contiene la estructura
del proyecto, el ambiente de ejecucion basado en Docker y un script que descarga
los datos de **2026**. Todo lo demas debe ser construido por cada equipo.

## Trabajo con fork

El laboratorio se desarrolla y se entrega sobre un **fork** de este repositorio.
No se trabaja directamente sobre el repositorio del docente.

1. Realice un fork de este repositorio:
   <https://github.com/menene/duckdb>

2. Clone **su propio fork** (no el del docente):

   ```bash
   git clone https://github.com/<su-usuario>/duckdb.git
   cd duckdb
   ```

3. Opcional, para recibir correcciones publicadas por el docente:

   ```bash
   git remote add upstream https://github.com/menene/duckdb.git
   git fetch upstream
   ```

Realice commits frecuentes y descriptivos: el historial del repositorio es parte
de la evaluacion. **La entrega del laboratorio es la URL de su fork.**

## Estructura

```text
duckdb/
|
+-- data/
|   +-- raw/
|   +-- processed/
|
+-- notebooks/
|
+-- scripts/
|
+-- sql/
|
+-- docs/
|
+-- Dockerfile
+-- metabase.Dockerfile
+-- docker-compose.yml
+-- README.md
```

## Requisitos

- Docker, con Docker Compose
- Git

La primera construccion del ambiente descarga varios cientos de MB y puede
tardar algunos minutos.

Considere el espacio en disco: las imagenes de Docker ocupan unos 3 GB y los
datos de los tres anios del laboratorio superan 1.5 GB, a los que se suma la
base materializada del Ejercicio 6. Se recomienda tener al menos 10 GB libres.

## Datos

El repositorio incluye `scripts/download_data.py`, que descarga los archivos de
2026 publicados por la TLC (`--help` muestra las opciones disponibles). Los
archivos se guardan en `data/raw/<tipo>/<anio>/`.

La TLC publica cada mes con varias semanas de atraso, por lo que los ultimos
meses de 2026 todavia no existen. El script consulta al servidor que meses estan
publicados, de modo que vuelve a ejecutarse sin problema conforme aparezcan
nuevos archivos.

Los datos descargados **no deben incluirse en el repositorio Git**. El archivo
`.gitignore` ya esta configurado para evitarlo.

Fuente de datos: NYC TLC Trip Record Data
<https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page>

Dentro de los contenedores, la carpeta `data/` del proyecto esta montada en
`/workspace/data`. Esa es la ruta que deben usar las herramientas que corren
dentro del ambiente, no la ruta de su computadora.

> **Nota sobre DuckDB:** un archivo `.duckdb` admite un solo proceso con permiso
> de escritura a la vez. Si conecta una herramienta externa a su base de datos,
> use el modo de solo lectura (`read_only`) en esa conexion; de lo contrario los
> demas procesos no podran abrir el archivo.

## Material a entregar

Al finalizar, su fork debe contener:

- el codigo fuente modificado y los scripts de descarga;
- las consultas SQL desarrolladas;
- el notebook o notebooks utilizados;
- la documentacion de las consultas;
- los scripts utilizados para los benchmarks;
- el codigo de los indicadores y visualizaciones;
- el tablero o la evidencia del tablero desarrollado;
- este `README.md`, completado segun la siguiente seccion.

Los archivos de datos descargados **no** deben incluirse.

---

# Documentacion del equipo

Las siguientes secciones deben ser completadas por cada equipo. El README final
debe permitir que una persona que no participo en el desarrollo pueda levantar el
ambiente, descargar los datos, ejecutar el analisis, reproducir los benchmarks y
generar los resultados principales.

**Equipo:** Abby Donis (22440), Hansel Lopez (19026), Fabian Prado (23427)

**Repositorio.** El laboratorio vive en la carpeta `Lab8/` del repositorio de laboratorios
del equipo, no en un fork aparte. El primer commit de la carpeta
(`chore: repositorio base del Lab8 proporcionado por el docente`) es una copia sin cambios de
`menene/duckdb`, y cada modificacion posterior esta en commits separados: el historial
muestra que traia el repositorio base y que cambio el equipo. Todas las rutas de este README
son relativas a `Lab8/`.

**Estado.**

| Ejercicio | Estado | Donde |
|---|---|---|
| 1. Ambiente | Listo | Este README y `notebooks/01_Ambiente_y_Descarga.ipynb` |
| 2. Sistema de descarga | Listo | `scripts/download_data.py` y cuaderno 01 |
| 3. Consultas directas sobre Parquet | Listo | `notebooks/02_Consultas_Parquet.ipynb`, `sql/02_*.sql` |
| 4. Analisis exploratorio | Listo | `notebooks/03_Exploratorio.ipynb`, `sql/03_*.sql` |
| 5. Incorporacion de 2024 | Listo | `notebooks/04_Incorporacion_2024.ipynb`, `sql/04_*.sql` |
| 6. Benchmark Parquet vs DuckDB | Listo | `notebooks/05_Benchmark.ipynb`, `data/processed/benchmark.csv` |
| 7. Indicadores y tablero | Listo | `notebooks/06_Indicadores.ipynb`, `sql/07_*.sql`, `docs/tablero.md` |
| 8. Analisis completo (2024-2025-2026) | Listo | `notebooks/07_Analisis_Completo.ipynb`, `sql/08_*.sql` |
| 9. Discusion | Listo | `notebooks/08_Discusion.ipynb` |

## Estructura del proyecto y proposito de cada carpeta

| Carpeta o archivo | Proposito |
|---|---|
| `data/raw/` | Los datos tal como los publica la fuente: Parquet de la TLC en `data/raw/<tipo>/<anio>/` y la tabla de zonas en `data/raw/zonas/`. Nunca se modifican; si algo sale mal se borran y se vuelven a descargar. No se versionan |
| `data/processed/` | Todo lo que se deriva de los datos: las figuras de los cuadernos (`data/processed/figuras/`) y, en el ejercicio 6, la base materializada de DuckDB. Se regenera, asi que tampoco se versiona |
| `notebooks/` | El analisis: un cuaderno numerado por ejercicio, cada uno con un archivo `_notes.md` que registra datos usados, decisiones, hallazgos y lo aprendido |
| `scripts/` | Codigo Python reutilizable: `download_data.py` (descarga y verificacion) y `consultas.py` (conexion a DuckDB y ejecucion de los archivos de `sql/`) |
| `sql/` | Una consulta por archivo, con objetivo y fuente en el encabezado. `00_vistas.sql` define las vistas comunes; el prefijo de las demas es el cuaderno que las usa |
| `docs/` | `consultas.md`: objetivo, fuente, resultado, decision y SQL de cada consulta |
| `Dockerfile`, `requirements.txt` | Imagen del servicio `lab`: Python 3.11.14 y versiones fijas de DuckDB, pandas, pyarrow, matplotlib, requests y JupyterLab |
| `metabase.Dockerfile` | Imagen de Metabase v0.63.19 con el driver de DuckDB 1.5.5.0 |
| `docker-compose.yml` | Levanta los dos servicios y monta las carpetas del proyecto dentro de los contenedores |

La separacion tiene un motivo. Lo que entra (`data/raw`) nunca se mezcla con lo que se
produce (`data/processed`), asi que borrar lo derivado no cuesta nada. El SQL vive aparte del
Python, para que la consulta documentada y la ejecutada sean la misma. Y todo lo que pesa o
se puede regenerar queda fuera de Git.

## Como levantar el ambiente

Requisitos: Docker Desktop con Docker Compose y unos 10 GB libres. Las dos imagenes ocupan
1.16 GB (`lab`) y 1.83 GB (`metabase`), y los datos de 2026 unos 500 MB.

```bash
cd Lab8
docker compose up -d --build
docker compose ps
```

La primera construccion descarga la imagen de Python, la de Java (Temurin 21), Metabase y el
driver de DuckDB, y tarda varios minutos. Las siguientes reutilizan las imagenes.

| Servicio | Direccion | Que es |
|---|---|---|
| `lab` | http://localhost:8888 | JupyterLab, sin contrasena y publicado solo en 127.0.0.1 |
| `metabase` | http://localhost:3000 | Metabase con el driver de DuckDB, para el tablero del ejercicio 7 |

Para comprobar que funcionan:

```bash
curl -s http://localhost:3000/api/health
docker compose exec lab python -c "import duckdb; print(duckdb.__version__)"
```

La primera debe responder `{"status":"ok"}` y la segunda `1.5.5`. El cuaderno 01 hace la
misma verificacion de los dos servicios desde dentro del contenedor `lab`.

Herramientas disponibles (1.4): en `lab`, Python 3.11.14, DuckDB 1.5.5, pandas 3.0.6, pyarrow
25.0.1, matplotlib 3.11.2, requests 2.34.2, JupyterLab 4.6.4 y `curl`; en `metabase`, Java 21,
Metabase v0.63.19 y el driver de DuckDB 1.5.5.0. DuckDB tiene la misma version en los dos lados
porque un archivo `.duckdb` escrito por una version no siempre lo abre otra.

`docker compose down` apaga los servicios. Los datos se conservan porque `data/` es una carpeta
del proyecto montada en el contenedor, y la configuracion de Metabase vive en el volumen
`metabase-data`.

**Por que un ambiente reproducible (1.6).** El `Dockerfile` fija la version de Python y de cada
paquete, y `docker compose` levanta los mismos servicios en cualquier computadora con un solo
comando. Eso evita que un resultado dependa de lo que cada quien tenga instalado, que el tablero
deje de abrir la base de DuckDB por una diferencia de version y que alguien no pueda correr el
analisis por una dependencia que falta. Junto con los datos fuera de Git y un script que los
vuelve a bajar, cualquier persona reconstruye el mismo punto de partida.

## Como descargar los datos

```bash
docker compose exec lab python scripts/download_data.py              # baja 2024, 2025 y 2026
docker compose exec lab python scripts/download_data.py --anios 2024 # solo 2024
docker compose exec lab python scripts/download_data.py --verificar  # compara disco y servidor
```

El script tambien corre fuera de Docker con cualquier Python que tenga `requests`, desde
cualquier carpeta. Soporta multiples anios (2024, 2025, 2026) mediante `--anios`. Pregunta al
servidor de la TLC que meses estan publicados, omite los archivos que ya existen, descarga
sobre un archivo temporal `.part` que solo se renombra al terminar y deja todo en
`data/raw/<tipo>/<anio>/`. Al 2026-10-06 estan publicados enero a agosto de 2026, y los 12
meses de 2024 y 2025. Los meses faltantes responden 403 y se reportan como no publicados; al
volver a correr el script se bajan cuando aparezcan.

**Cambios al script del docente (2.6).**

| Problema en el script original | Cambio |
|---|---|
| `DIR_DESTINO = Path("data/raw")` dependia del directorio de trabajo: corrido desde `notebooks/` escribia en `notebooks/data/raw` | La ruta se resuelve desde la ubicacion del archivo |
| `esta_publicado` trataba cualquier error de red como "no publicado", y un mes podia quedar fuera sin aviso | `tamanio_publicado` solo trata 403 y 404 como no publicado; cualquier otro error cuenta como fallo |
| Nada comparaba lo descargado con lo publicado | El tamanio recibido se compara con el `Content-Length` del servidor y se reintenta si no coincide |
| No habia forma de revisar una descarga sin repetirla | Opcion `--verificar`: compara mes a mes el tamanio en disco con el del servidor |
| El analisis necesita pasar de zona a barrio | El script baja tambien `taxi_zone_lookup.csv` |

**Como se determino que la descarga esta completa (2.7).** Con tres pruebas: que meses estan
publicados se le pregunta al servidor; cada archivo publicado debe pesar en disco exactamente
lo que anuncia el servidor; y cada archivo debe tener un pie Parquet legible con un numero de
registros en linea con los meses vecinos. El cuaderno 01 corre las tres y repite la descarga
para comprobar que no se vuelve a bajar ningun archivo.

<!-- TODO (Ejercicios 5.1 y 8.1) -->

## Como ejecutar el analisis

Los cuadernos se corren en orden, dentro del contenedor `lab`, desde JupyterLab
(http://localhost:8888) o desde la terminal:

```bash
docker compose exec lab jupyter nbconvert --to notebook --execute --inplace notebooks/01_Ambiente_y_Descarga.ipynb
docker compose exec lab jupyter nbconvert --to notebook --execute --inplace notebooks/02_Consultas_Parquet.ipynb
docker compose exec lab jupyter nbconvert --to notebook --execute --inplace notebooks/03_Exploratorio.ipynb
docker compose exec lab jupyter nbconvert --to notebook --execute --inplace notebooks/04_Incorporacion_2024.ipynb
docker compose exec lab jupyter nbconvert --to notebook --execute --inplace notebooks/05_Benchmark.ipynb
docker compose exec lab jupyter nbconvert --to notebook --execute --inplace notebooks/06_Indicadores.ipynb
docker compose exec lab jupyter nbconvert --to notebook --execute --inplace notebooks/07_Analisis_Completo.ipynb
docker compose exec lab jupyter nbconvert --to notebook --execute --inplace notebooks/08_Discusion.ipynb
```

| Cuaderno | Ejercicio | Que responde | Tiempo aproximado |
|---|---|---|---|
| `01_Ambiente_y_Descarga` | 1 y 2 | Si los servicios funcionan y si la descarga esta completa. Si no hay datos, los baja | 10 s, o 40 s con la descarga |
| `02_Consultas_Parquet` | 3 | Archivos, registros, columnas, tipos, muestra, calidad y costo de leer Parquet directo | 25 s |
| `03_Exploratorio` | 4 | Siete preguntas sobre tiempo, caracteristicas, geografia, pago, montos y atipicos | 25 s |
| `04_Incorporacion_2024` | 5 | Como incorporar 2024 sin romper las consultas existentes | 30 s |
| `05_Benchmark` | 6 | Comparacion de rendimiento entre Parquet directo y tabla materializada | 45 s |
| `06_Indicadores` | 7 | Seis indicadores clave con visualizaciones para el tablero | 20 s |
| `07_Analisis_Completo` | 8 | Evolucion de indicadores a lo largo de 2024-2025-2026 | 35 s |
| `08_Discusion` | 9 | Reflexion sobre DuckDB, ventajas, limitaciones y aprendizajes | 5 s |

Los tiempos son de una Mac de 10 nucleos con 8 GB asignados a Docker.

Las consultas tambien se pueden correr sueltas. `consultas.conectar()` abre DuckDB en memoria
con las vistas de `sql/00_vistas.sql`, y `consultas.correr` ejecuta un archivo de `sql/`:

```bash
docker compose exec -w /workspace/scripts lab python -c "import consultas; print(consultas.correr(consultas.conectar(), '03_barrios.sql'))"
```

## Como reproducir los benchmarks

El benchmark compara consultar Parquet directamente vs tabla materializada en DuckDB.
Se ejecuta en el cuaderno `05_Benchmark.ipynb` y los resultados se guardan en
`data/processed/benchmark.csv`.

**Resultados principales:**

| Escenario | Consultas | Parquet (ms) | Tabla (ms) | Veces mas rapido |
|---|---|---|---|---|
| Solo 2026 (29.7M filas) | conteo_por_mes | 245.3 | 12.4 | 19.78x |
| Solo 2026 | distancia_mediana | 892.1 | 45.6 | 19.56x |
| Solo 2026 | pago_mas_usado | 312.7 | 18.9 | 16.54x |
| Solo 2026 | velocidad_por_hora | 1,234.5 | 67.8 | 18.21x |
| 2024+2026 (71M filas) | conteo_por_mes | 567.8 | 28.9 | 19.65x |
| 2024+2026 | distancia_mediana | 2,134.6 | 112.3 | 19.01x |
| 2024+2026 | pago_mas_usado | 723.4 | 41.2 | 17.56x |
| 2024+2026 | velocidad_por_hora | 2,987.3 | 156.7 | 19.06x |

**Conclusion:** La tabla materializada es 16-20x mas rapida, pero tarda 12-28s en crearse.
Conviene para consultas repetidas (tableros), no para exploracion.

## Como generar los resultados principales

Las figuras de los ejercicios 1 a 8 las escriben los cuadernos en `data/processed/figuras/` y
las tablas de resultados quedan en las salidas de cada cuaderno. Los hallazgos principales del
exploratorio, con sus cifras, estan en la seccion 8 de `notebooks/03_Exploratorio.ipynb`: los
amarillos y los verdes atienden mercados distintos (86.6% de los amarillos sale de Manhattan;
39.1% de los verdes, de East Harlem), la duracion de un viaje casi no cambia con la hora pero la
velocidad se reduce a la mitad, el verano baja 18.5% los viajes diarios de los amarillos, el
total no coincide con la suma de sus componentes en 36.9% de los amarillos por como reportan
algunos proveedores, y la propina solo existe en los datos cuando se paga con tarjeta.

**Resultados del analisis completo (2024-2025-2026):**

1. **Crecimiento sostenido:** Los viajes crecieron +3.6% en amarillos y +3.0% en verdes de 2024 a 2025
2. **Aumento de tarifas:** El ingreso promedio subio +1.3% en amarillos y +1.6% en verdes
3. **Segmentacion estable:** La brecha amarillos vs verdes se mantiene constante (13x volumen, 21% precio)

**Tablero en Metabase:**

El tablero contiene 6 indicadores principales documentados en `docs/tablero.md`:
- Viajes diarios por tipo
- Ingreso promedio por viaje
- Propina por metodo de pago
- Velocidad por hora del dia
- Metodo de pago mas usado
- Viajes por dia de semana

**Cambios adicionales al script (ejercicios 5 y 8).**

| Cambio | Motivo |
|---|---|
| `ANIO = 2026` reemplazado por `ANIOS = (2024, 2025, 2026)` | Soportar multiples anios |
| Argumento `--anios 2024 2025` agregado | Permitir descargar solo anios especificos |
| Funciones `construir_nombre`, `construir_url`, `ruta_destino`, `descargar`, `verificar` ahora reciben `anio` como parametro | Generalizar para cualquier anio |
| `imprimir_verificacion` itera sobre `anios` | Verificar multiples anios simultaneamente |

Las vistas no requirieron cambios porque usan glob patterns (`data/raw/*/*/*.parquet`) que
capturan automaticamente cualquier anio. La vista `viajes_validos` extrae el anio del nombre
del archivo con `split_part(filename, '/', -2)`, por lo que funciona con 2024, 2025, 2026 o
cualquier otro anio.
