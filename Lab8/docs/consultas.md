# Documentacion de las consultas

Cada consulta del laboratorio vive en su propio archivo de `sql/` y los cuadernos la
ejecutan por nombre con `scripts/consultas.py`, asi que la consulta documentada aqui y la
que produce el resultado son la misma. El SQL de cada seccion es copia del archivo; si
alguna vez difieren, manda el archivo.

Para cada consulta: objetivo, archivos fuente, resultado obtenido, decision tomada a partir
del resultado y el SQL completo. Los resultados son de la corrida del 2026-10-06 sobre
enero a agosto de 2026 (16 archivos, 30,040,469 viajes).

Convenciones de todas las consultas:

- Las rutas son relativas a la raiz del laboratorio. `consultas.conectar()` fija
  `file_search_path` para que funcionen desde cualquier carpeta; desde la consola de
  DuckDB hay que abrirla en la raiz.
- Se lee con `union_by_name = true` porque el esquema cambia en junio de 2026 (columna
  `request_source`).
- El tipo de taxi sale de la ruta del archivo (`data/raw/<tipo>/<anio>/`), con
  `filename = true` y `split_part`.

## Vistas comunes

### `00_vistas.sql`

- **Objetivo:** vistas sobre los archivos Parquet de data/raw para que las consultas de analisis no repitan rutas ni nombres distintos por tipo.
- **Fuente:** data/raw/yellow/*/*.parquet, data/raw/green/*/*.parquet y data/raw/zonas/taxi_zone_lookup.csv.
- **Resultado:** Cinco vistas: `yellow`, `green`, `viajes` (los dos tipos con las fechas renombradas a `pickup_datetime` y `dropoff_datetime`), `viajes_validos` y `zonas`. No copian datos. `viajes_validos` deja fuera los montos negativos y los viajes fuera del mes de su archivo (29,877,234 viajes de 2026 quedan) y agrega mes, hora, dia de la semana, duracion y la marca `medible`.
- **Decision:** Las consultas de analisis leen `viajes_validos`. Un anio nuevo en `data/raw` entra en las vistas sin tocar ninguna consulta.

```sql
-- 00_vistas.sql
-- Objetivo: vistas sobre los archivos Parquet de data/raw para que las
-- consultas de analisis no repitan rutas ni nombres distintos por tipo.
-- Fuente: data/raw/yellow/*/*.parquet, data/raw/green/*/*.parquet y
-- data/raw/zonas/taxi_zone_lookup.csv.
--
-- Una vista no copia datos: guarda la consulta, y cada vez que se usa DuckDB
-- vuelve a leer los archivos. Por eso un mes o un anio nuevo que caiga en
-- data/raw/<tipo>/<anio>/ entra solo, sin tocar ninguna consulta.
--
-- Las rutas son relativas a la raiz del laboratorio. scripts/consultas.py fija
-- file_search_path para que funcionen desde cualquier carpeta; desde la
-- consola de DuckDB hay que abrirla en la raiz del laboratorio.
--
-- union_by_name = true: desde junio de 2026 los archivos traen una columna
-- nueva (request_source). Sin esta opcion DuckDB toma el esquema del primer
-- archivo y la columna desaparece sin ningun aviso.
-- filename = true: agrega la ruta del archivo de origen a cada fila, para
-- poder comparar la fecha del viaje con el mes del archivo.

create or replace view yellow as
select *
from read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true, filename = true);

create or replace view green as
select *
from read_parquet('data/raw/green/*/*.parquet', union_by_name = true, filename = true);

-- Amarillos y verdes en una sola vista. Las fechas tienen prefijo distinto
-- (tpep_ en amarillos, lpep_ en verdes) y se renombran a un nombre comun.
-- union all by name deja en nulo las columnas que solo tiene un tipo:
-- Airport_fee en amarillos, ehail_fee y trip_type en verdes.
create or replace view viajes as
select 'yellow' as tipo,
       * rename (tpep_pickup_datetime as pickup_datetime,
                 tpep_dropoff_datetime as dropoff_datetime)
from yellow
union all by name
select 'green' as tipo,
       * rename (lpep_pickup_datetime as pickup_datetime,
                 lpep_dropoff_datetime as dropoff_datetime)
from green;

-- Viajes validos para el analisis, con las decisiones del cuaderno 02.
-- Quedan fuera los montos negativos (reversiones de cobro del proveedor 2) y
-- los viajes cuya fecha de inicio no cae en el mes de su archivo (244 en 2026,
-- 21 de ellos con fechas de 2001 a 2009). Los demas problemas no se borran:
-- se filtran solo en el analisis al que afectan, con la columna medible.
--
-- medible: el viaje sirve para duracion, distancia y velocidad. No lo es si
-- es del proveedor 7 (no registra la hora de llegada), si la duracion no es
-- positiva o pasa de 24 horas, o si la distancia es cero o pasa de 100 millas.
create or replace view viajes_validos as
select
    *,
    year(pickup_datetime) as anio,
    month(pickup_datetime) as mes,
    hour(pickup_datetime) as hora,
    isodow(pickup_datetime) as dia_semana,  -- 1 lunes, 7 domingo
    date_diff('second', pickup_datetime, dropoff_datetime) / 60.0 as duracion_min,
    (VendorID <> 7
     and dropoff_datetime > pickup_datetime
     and dropoff_datetime - pickup_datetime <= interval 24 hours
     and trip_distance > 0
     and trip_distance <= 100) as medible
from viajes
where fare_amount >= 0
  and total_amount >= 0
  and strftime(pickup_datetime, '%Y-%m') = regexp_extract(filename, '(\d{4}-\d{2})\.parquet$', 1);

-- Tabla de zonas de la TLC (265 zonas) para traducir PULocationID y
-- DOLocationID a barrio y zona.
create or replace view zonas as
select *
from read_csv('data/raw/zonas/taxi_zone_lookup.csv');
```

## Ejercicio 2: verificacion de la descarga

### `01_filas_por_archivo.sql`

- **Objetivo:** registros, tamanio y programa que escribio cada archivo descargado, leyendo solo el pie de metadatos de cada Parquet.
- **Fuente:** data/raw/*/*/*.parquet, directo, sin vistas.
- **Resultado:** 16 archivos con pie Parquet valido: 29,703,355 filas de amarillos (3,336,716 en agosto a 4,090,836 en mayo) y 337,114 de verdes (37,373 a 44,921). Escritos por parquet-cpp-arrow 16.1.0 de enero a mayo, 21.0.0 de junio a agosto y 24.0.0 en abril de amarillos.
- **Decision:** La descarga se da por completa: ningun mes se sale del patron de sus vecinos.

```sql
-- 01_filas_por_archivo.sql
-- Objetivo: registros, tamanio y programa que escribio cada archivo
-- descargado, leyendo solo el pie de metadatos de cada Parquet.
-- Fuente: data/raw/*/*/*.parquet, directo, sin vistas.
-- Uso: verificacion de completitud (ejercicio 2.7). No recorre los datos, por
-- eso tarda milisegundos aunque los archivos sumen cientos de MB. Un archivo
-- truncado no tiene pie valido y la consulta fallaria al intentar leerlo.
select
    split_part(file_name, '/', -3) as tipo,
    cast(split_part(file_name, '/', -2) as integer) as anio,
    cast(regexp_extract(file_name, '-(\d{2})\.parquet$', 1) as integer) as mes,
    regexp_extract(file_name, '[^/]+$') as archivo,
    num_rows as filas,
    num_row_groups as grupos_de_filas,
    file_size_bytes as bytes,
    created_by as escrito_por
from parquet_file_metadata('data/raw/*/*/*.parquet')
order by tipo desc, anio, mes;
```

## Ejercicio 3: consultas directas sobre los Parquet

### `02_archivos.sql`

- **Objetivo:** cuantos archivos Parquet hay por tipo de taxi y que meses cubren (3.1).
- **Fuente:** data/raw/*/*/*.parquet, listados con glob(); no abre ningun archivo.
- **Resultado:** 8 archivos de amarillos y 8 de verdes, de 2026-01 a 2026-08.
- **Decision:** Coincide con lo publicado por la TLC; no falta ni sobra ningun mes.

```sql
-- 02_archivos.sql
-- Objetivo: cuantos archivos Parquet hay por tipo de taxi y que meses cubren (3.1).
-- Fuente: data/raw/*/*/*.parquet, listados con glob(); no abre ningun archivo.
select
    split_part(file, '/', -3) as tipo,
    count(*) as archivos,
    min(regexp_extract(file, '(\d{4}-\d{2})\.parquet$', 1)) as primer_mes,
    max(regexp_extract(file, '(\d{4}-\d{2})\.parquet$', 1)) as ultimo_mes
from glob('data/raw/*/*/*.parquet')
group by tipo
order by tipo desc;
```

### `02_registros.sql`

- **Objetivo:** cuantos registros hay por tipo de taxi (3.2).
- **Fuente:** data/raw/*/*/*.parquet, directo. El tipo sale de la ruta del archivo.
- **Resultado:** 29,703,355 amarillos (98.9%) y 337,114 verdes (1.1%), igual a la suma de los metadatos.
- **Decision:** Toda comparacion entre tipos se hace por separado y en porcentajes.

```sql
-- 02_registros.sql
-- Objetivo: cuantos registros hay por tipo de taxi (3.2).
-- Fuente: data/raw/*/*/*.parquet, directo. El tipo sale de la ruta del archivo.
select
    split_part(filename, '/', -3) as tipo,
    count(*) as registros
from read_parquet('data/raw/*/*/*.parquet', union_by_name = true, filename = true)
group by tipo
order by tipo desc;
```

### `02_esquema.sql`

- **Objetivo:** columnas de cada tipo de taxi (3.3), su tipo fisico y logico dentro del Parquet (3.4) y en cuantos archivos aparece cada una.
- **Fuente:** parquet_schema() sobre data/raw/*/*/*.parquet; lee solo los pies. tipos_distintos > 1 significaria que una columna cambia de tipo entre meses.
- **Resultado:** 21 columnas en amarillos y 22 en verdes, 18 nombres en comun. `request_source` solo en los 3 archivos de junio a agosto. Ninguna columna cambia de tipo entre archivos.
- **Decision:** Leer siempre con `union_by_name = true` y unificar `tpep_` y `lpep_` en la vista `viajes`.

```sql
-- 02_esquema.sql
-- Objetivo: columnas de cada tipo de taxi (3.3), su tipo fisico y logico dentro
-- del Parquet (3.4) y en cuantos archivos aparece cada una.
-- Fuente: parquet_schema() sobre data/raw/*/*/*.parquet; lee solo los pies.
-- tipos_distintos > 1 significaria que una columna cambia de tipo entre meses.
select
    split_part(file_name, '/', -3) as tipo,
    name as columna,
    min(type) as tipo_fisico,
    min(coalesce(logical_type, converted_type)) as tipo_logico,
    count(distinct type) as tipos_distintos,
    count(distinct file_name) as archivos,
    min(regexp_extract(file_name, '(\d{4}-\d{2})\.parquet$', 1)) as desde
from parquet_schema('data/raw/*/*/*.parquet')
where name <> 'schema'
group by tipo, columna
order by tipo desc, archivos desc, columna;
```

### `02_tipos_duckdb.sql`

- **Objetivo:** tipo con el que DuckDB expone cada columna al leer los archivos (3.4).
- **Fuente:** data/raw/*/*/*.parquet, directo. Con union_by_name las columnas de amarillos y verdes quedan en una sola lista, en el orden en que aparecen.
- **Resultado:** Fechas TIMESTAMP (sin zona horaria), montos y distancia DOUBLE, zonas INTEGER, codigos BIGINT.
- **Decision:** Las fechas se usan como hora local de Nueva York. Los codigos se tratan como categorias.

```sql
-- 02_tipos_duckdb.sql
-- Objetivo: tipo con el que DuckDB expone cada columna al leer los archivos (3.4).
-- Fuente: data/raw/*/*/*.parquet, directo. Con union_by_name las columnas de
-- amarillos y verdes quedan en una sola lista, en el orden en que aparecen.
select
    column_name as columna,
    column_type as tipo_duckdb
from (describe select * from read_parquet('data/raw/*/*/*.parquet', union_by_name = true));
```

### `02_muestra_yellow.sql`

- **Objetivo:** muestra reproducible de unos diez viajes de taxis yellow (3.5).
- **Fuente:** data/raw/yellow/*/*.parquet, directo. Se usa bernoulli con semilla y no reservoir: en DuckDB 1.5.5, reservoir(5 rows) devolvio solo viajes de enero con cualquier semilla, una muestra que no representa el anio. Bernoulli decide fila por fila con la misma probabilidad, asi que cubre todos los meses.
- **Resultado:** 15 viajes repartidos de enero a agosto; se ven filas Flex Fare sin pasajeros y un viaje del proveedor 7 con duracion cero.
- **Decision:** Muestrear con bernoulli y semilla: `reservoir(5 rows)` devolvio solo viajes de enero.

```sql
-- 02_muestra_yellow.sql
-- Objetivo: muestra reproducible de unos diez viajes de taxis yellow (3.5).
-- Fuente: data/raw/yellow/*/*.parquet, directo.
-- Se usa bernoulli con semilla y no reservoir: en DuckDB 1.5.5,
-- reservoir(5 rows) devolvio solo viajes de enero con cualquier semilla, una
-- muestra que no representa el anio. Bernoulli decide fila por fila con la
-- misma probabilidad, asi que cubre todos los meses.
select *
from read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true)
using sample 0.00003 percent (bernoulli, 42)
order by tpep_pickup_datetime;
```

### `02_muestra_green.sql`

- **Objetivo:** muestra reproducible de unos diez viajes de taxis green (3.5).
- **Fuente:** data/raw/green/*/*.parquet, directo. Se usa bernoulli con semilla y no reservoir: en DuckDB 1.5.5, reservoir(5 rows) devolvio solo viajes de enero con cualquier semilla, una muestra que no representa el anio. Bernoulli decide fila por fila con la misma probabilidad, asi que cubre todos los meses.
- **Resultado:** 13 viajes repartidos de enero a agosto; dos del proveedor 6 sin tipo de pago.
- **Decision:** Igual que la muestra de amarillos.

```sql
-- 02_muestra_green.sql
-- Objetivo: muestra reproducible de unos diez viajes de taxis green (3.5).
-- Fuente: data/raw/green/*/*.parquet, directo.
-- Se usa bernoulli con semilla y no reservoir: en DuckDB 1.5.5,
-- reservoir(5 rows) devolvio solo viajes de enero con cualquier semilla, una
-- muestra que no representa el anio. Bernoulli decide fila por fila con la
-- misma probabilidad, asi que cubre todos los meses.
select *
from read_parquet('data/raw/green/*/*.parquet', union_by_name = true)
using sample 0.003 percent (bernoulli, 42)
order by lpep_pickup_datetime;
```

### `02_resumen_yellow.sql`

- **Objetivo:** perfil de cada columna de los taxis yellow: minimo, maximo, valores distintos aproximados, cuartiles y porcentaje de nulos (3.4 y 3.6).
- **Fuente:** data/raw/yellow/*/*.parquet, directo.
- **Resultado:** Fechas desde 2001, distancia maxima de 328,522 millas, montos negativos en todas las columnas de dinero, 25.98% de nulos en pasajeros, codigo de tarifa, store_and_fwd, recargo de congestion y cargo de aeropuerto.
- **Decision:** Revisar cada rango imposible con una regla de calidad (02_calidad.sql). Las medianas de SUMMARIZE son aproximadas y no se reportan como resultado.

```sql
-- 02_resumen_yellow.sql
-- Objetivo: perfil de cada columna de los taxis yellow: minimo, maximo, valores
-- distintos aproximados, cuartiles y porcentaje de nulos (3.4 y 3.6).
-- Fuente: data/raw/yellow/*/*.parquet, directo.
summarize select * from read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true);
```

### `02_resumen_green.sql`

- **Objetivo:** perfil de cada columna de los taxis green: minimo, maximo, valores distintos aproximados, cuartiles y porcentaje de nulos (3.4 y 3.6).
- **Fuente:** data/raw/green/*/*.parquet, directo.
- **Resultado:** Fechas desde 2008, distancia maxima de 179,831 millas, 14.47% de nulos en las mismas columnas, `ehail_fee` 100% nula.
- **Decision:** `ehail_fee` se ignora en todo el analisis.

```sql
-- 02_resumen_green.sql
-- Objetivo: perfil de cada columna de los taxis green: minimo, maximo, valores
-- distintos aproximados, cuartiles y porcentaje de nulos (3.4 y 3.6).
-- Fuente: data/raw/green/*/*.parquet, directo.
summarize select * from read_parquet('data/raw/green/*/*.parquet', union_by_name = true);
```

### `02_calidad.sql`

- **Objetivo:** cuantos registros tienen cada problema de calidad, por tipo de taxi (3.6). Cada columna cuenta una regla; un registro puede caer en varias.
- **Fuente:** data/raw/*/*/*.parquet, directo. Las fechas tienen prefijo distinto por tipo (tpep_, lpep_); con union_by_name la del otro tipo queda nula y coalesce toma la que existe.
- **Resultado:** 2 problemas grandes (pasajeros nulos y pago sin tipo, 25.98% y 14.47%), 7 moderados (distancia cero 3.2% y 3.6%, codigo 99 2.59% en amarillos, duracion cero 1.25% en amarillos, zona desconocida, tarifa y total negativos, cero pasajeros) y 5 marginales.
- **Decision:** Cada problema se filtra solo en los analisis a los que afecta (tabla de decisiones en el cuaderno 02, seccion 8).

```sql
-- 02_calidad.sql
-- Objetivo: cuantos registros tienen cada problema de calidad, por tipo de
-- taxi (3.6). Cada columna cuenta una regla; un registro puede caer en varias.
-- Fuente: data/raw/*/*/*.parquet, directo.
-- Las fechas tienen prefijo distinto por tipo (tpep_, lpep_); con
-- union_by_name la del otro tipo queda nula y coalesce toma la que existe.
with v as (
    select
        split_part(filename, '/', -3) as tipo,
        regexp_extract(filename, '(\d{4}-\d{2})\.parquet$', 1) as mes_archivo,
        coalesce(tpep_pickup_datetime, lpep_pickup_datetime) as inicio,
        coalesce(tpep_dropoff_datetime, lpep_dropoff_datetime) as fin,
        *
    from read_parquet('data/raw/*/*/*.parquet', union_by_name = true, filename = true)
)
select
    tipo,
    count(*) as registros,
    count_if(strftime(inicio, '%Y-%m') <> mes_archivo) as inicio_fuera_del_mes_del_archivo,
    count_if(fin < inicio) as fin_antes_del_inicio,
    count_if(fin = inicio) as duracion_cero,
    count_if(fin - inicio > interval 24 hours) as duracion_mayor_24h,
    count_if(trip_distance = 0) as distancia_cero,
    count_if(trip_distance > 100) as distancia_mayor_100_millas,
    count_if(fare_amount < 0) as tarifa_negativa,
    count_if(total_amount < 0) as total_negativo,
    count_if(tip_amount < 0) as propina_negativa,
    count_if(passenger_count is null) as pasajeros_nulo,
    count_if(passenger_count = 0) as pasajeros_cero,
    count_if(RatecodeID = 99) as codigo_tarifa_99,
    count_if(payment_type is null or payment_type = 0) as pago_sin_tipo,
    count_if(PULocationID in (264, 265) or DOLocationID in (264, 265)) as zona_desconocida
from v
group by tipo
order by tipo desc;
```

### `02_nulos_por_pago.sql`

- **Objetivo:** ver si los nulos de pasajeros, codigo de tarifa y recargos estan repartidos al azar o concentrados en un tipo de pago (3.6).
- **Fuente:** data/raw/*/*/*.parquet, directo.
- **Resultado:** Todos los nulos de pasajeros, codigo de tarifa, store_and_fwd y recargo estan en `payment_type` 0 (amarillos, 7,716,688) o nulo (verdes, 48,775). Ningun otro tipo de pago tiene nulos.
- **Decision:** Son viajes Flex Fare, no registros danados: se conservan y quedan fuera solo de los analisis de pasajeros, codigo de tarifa o recargos.

```sql
-- 02_nulos_por_pago.sql
-- Objetivo: ver si los nulos de pasajeros, codigo de tarifa y recargos estan
-- repartidos al azar o concentrados en un tipo de pago (3.6).
-- Fuente: data/raw/*/*/*.parquet, directo.
select
    split_part(filename, '/', -3) as tipo,
    payment_type,
    count(*) as registros,
    count(*) - count(passenger_count) as sin_pasajeros,
    count(*) - count(RatecodeID) as sin_codigo_tarifa,
    count(*) - count(store_and_fwd_flag) as sin_store_and_fwd,
    count(*) - count(congestion_surcharge) as sin_recargo_congestion
from read_parquet('data/raw/*/*/*.parquet', union_by_name = true, filename = true)
group by all
order by tipo desc, payment_type nulls last;
```

### `02_calidad_por_proveedor.sql`

- **Objetivo:** ver si los problemas de calidad estan repartidos entre los proveedores de tecnologia (VendorID) o concentrados en alguno (3.6).
- **Fuente:** data/raw/*/*/*.parquet, directo. VendorID segun el diccionario de la TLC: 1 Creative Mobile Technologies, 2 Curb Mobility, 6 Myle Technologies, 7 Helix.
- **Resultado:** Proveedor 7: 100% de sus 367,120 viajes con duracion cero. Proveedor 1: 769,133 de los 769,693 codigos 99. Proveedor 2: todas las tarifas negativas. Proveedor 6: nunca reporta tipo de pago.
- **Decision:** El proveedor 7 queda fuera de duracion y velocidad; el codigo 99 se trata como desconocido.

```sql
-- 02_calidad_por_proveedor.sql
-- Objetivo: ver si los problemas de calidad estan repartidos entre los
-- proveedores de tecnologia (VendorID) o concentrados en alguno (3.6).
-- Fuente: data/raw/*/*/*.parquet, directo.
-- VendorID segun el diccionario de la TLC: 1 Creative Mobile Technologies,
-- 2 Curb Mobility, 6 Myle Technologies, 7 Helix.
select
    split_part(filename, '/', -3) as tipo,
    VendorID,
    count(*) as registros,
    count_if(coalesce(tpep_dropoff_datetime, lpep_dropoff_datetime)
             = coalesce(tpep_pickup_datetime, lpep_pickup_datetime)) as duracion_cero,
    count_if(trip_distance = 0) as distancia_cero,
    count_if(fare_amount < 0) as tarifa_negativa,
    count_if(RatecodeID = 99) as codigo_tarifa_99,
    count_if(payment_type is null or payment_type = 0) as pago_sin_tipo,
    count_if(passenger_count = 0) as pasajeros_cero
from read_parquet('data/raw/*/*/*.parquet', union_by_name = true, filename = true)
group by all
order by tipo desc, VendorID;
```

### `02_negativos_por_pago.sql`

- **Objetivo:** con que tipo de pago y proveedor vienen los viajes con tarifa negativa, para saber si son errores de captura o ajustes (3.6).
- **Fuente:** data/raw/*/*/*.parquet, directo. payment_type segun el diccionario de la TLC: 0 Flex Fare, 1 tarjeta, 2 efectivo, 3 sin cargo, 4 disputa, 5 desconocido, 6 viaje anulado.
- **Resultado:** Todas las tarifas negativas son del proveedor 2. En amarillos: 100,849 en disputa, 35,068 en efectivo, 17,726 sin cargo, con medianas de -12.80, -13.50 y -10.00.
- **Decision:** Se tratan como reversiones de cobro y quedan fuera de todo el analisis.

```sql
-- 02_negativos_por_pago.sql
-- Objetivo: con que tipo de pago y proveedor vienen los viajes con tarifa
-- negativa, para saber si son errores de captura o ajustes (3.6).
-- Fuente: data/raw/*/*/*.parquet, directo.
-- payment_type segun el diccionario de la TLC: 0 Flex Fare, 1 tarjeta,
-- 2 efectivo, 3 sin cargo, 4 disputa, 5 desconocido, 6 viaje anulado.
select
    split_part(filename, '/', -3) as tipo,
    VendorID,
    payment_type,
    count(*) as registros,
    round(median(fare_amount), 2) as tarifa_mediana
from read_parquet('data/raw/*/*/*.parquet', union_by_name = true, filename = true)
where fare_amount < 0
group by all
order by tipo desc, registros desc;
```

### `02_fuera_de_mes.sql`

- **Objetivo:** de los viajes cuya fecha de inicio no cae en el mes de su archivo, a que mes corresponden y en que archivos estan (3.6).
- **Fuente:** data/raw/*/*/*.parquet, directo.
- **Resultado:** 244 viajes fuera del mes de su archivo: 223 en un mes vecino y 21 con fechas de 2001, 2008 o 2009.
- **Decision:** Se excluyen; el mes de cada viaje se toma solo cuando coincide con el de su archivo.

```sql
-- 02_fuera_de_mes.sql
-- Objetivo: de los viajes cuya fecha de inicio no cae en el mes de su archivo,
-- a que mes corresponden y en que archivos estan (3.6).
-- Fuente: data/raw/*/*/*.parquet, directo.
with v as (
    select
        split_part(filename, '/', -3) as tipo,
        regexp_extract(filename, '(\d{4}-\d{2})\.parquet$', 1) as mes_archivo,
        strftime(coalesce(tpep_pickup_datetime, lpep_pickup_datetime), '%Y-%m') as mes_inicio
    from read_parquet('data/raw/*/*/*.parquet', union_by_name = true, filename = true)
)
select
    tipo,
    mes_inicio,
    count(*) as registros,
    string_agg(distinct mes_archivo, ', ' order by mes_archivo) as archivos
from v
where mes_inicio <> mes_archivo
group by tipo, mes_inicio
order by tipo desc, mes_inicio;
```

### `02_duplicados.sql`

- **Objetivo:** filas repetidas exactamente igual en todas sus columnas (3.6).
- **Fuente:** data/raw/<tipo>/*/*.parquet, directo, un tipo a la vez porque sus columnas no son las mismas. group by all agrupa por todas las columnas de select *, asi que cada grupo con mas de una fila es un duplicado exacto.
- **Resultado:** 7 pares de filas identicas en amarillos, 0 en verdes.
- **Decision:** Se dejan: 7 filas de 29.7 millones no cambian ningun resultado.

```sql
-- 02_duplicados.sql
-- Objetivo: filas repetidas exactamente igual en todas sus columnas (3.6).
-- Fuente: data/raw/<tipo>/*/*.parquet, directo, un tipo a la vez porque sus
-- columnas no son las mismas. group by all agrupa por todas las columnas de
-- select *, asi que cada grupo con mas de una fila es un duplicado exacto.
select
    'yellow' as tipo,
    count(*) as grupos_repetidos,
    coalesce(sum(n), 0) as filas_en_grupos,
    coalesce(sum(n - 1), 0) as filas_sobrantes
from (
    select *, count(*) as n
    from read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true)
    group by all
    having count(*) > 1
)
union all
select
    'green',
    count(*),
    coalesce(sum(n), 0),
    coalesce(sum(n - 1), 0)
from (
    select *, count(*) as n
    from read_parquet('data/raw/green/*/*.parquet', union_by_name = true)
    group by all
    having count(*) > 1
);
```

### `02_costo_conteo.sql`

- **Objetivo:** tiempo de contar los registros de los amarillos (3.9). DuckDB lo resuelve con el numero de filas que trae el pie de cada archivo.
- **Fuente:** data/raw/yellow/*/*.parquet, directo.
- **Resultado:** Unos 4 ms para contar 29.7 millones de filas.
- **Decision:** Los conteos totales se pueden pedir sin preocuparse por el costo.

```sql
-- 02_costo_conteo.sql
-- Objetivo: tiempo de contar los registros de los amarillos (3.9). DuckDB lo
-- resuelve con el numero de filas que trae el pie de cada archivo.
-- Fuente: data/raw/yellow/*/*.parquet, directo.
select count(*) as registros
from read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true);
```

### `02_costo_una_columna.sql`

- **Objetivo:** tiempo de un calculo que necesita una sola columna (3.9). Solo se lee fare_amount; las otras 20 columnas no salen del disco.
- **Fuente:** data/raw/yellow/*/*.parquet, directo.
- **Resultado:** Entre 40 y 50 ms: solo se lee `fare_amount`.
- **Decision:** Las consultas del exploratorio piden solo las columnas que usan.

```sql
-- 02_costo_una_columna.sql
-- Objetivo: tiempo de un calculo que necesita una sola columna (3.9). Solo se
-- lee fare_amount; las otras 20 columnas no salen del disco.
-- Fuente: data/raw/yellow/*/*.parquet, directo.
select max(fare_amount) as tarifa_maxima
from read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true);
```

### `02_costo_filtro.sql`

- **Objetivo:** una columna con un filtro por fecha (3.9). DuckDB pasa el filtro a la lectura y puede descartar grupos de filas cuyo rango de fechas, guardado en los metadatos, no puede cumplirlo.
- **Fuente:** data/raw/yellow/*/*.parquet, directo.
- **Resultado:** Un poco menos que sin filtro. El plan muestra `Projections: fare_amount` y el filtro de fecha dentro de `READ_PARQUET`.
- **Decision:** Filtrar por fecha en el SQL y no despues en pandas.

```sql
-- 02_costo_filtro.sql
-- Objetivo: una columna con un filtro por fecha (3.9). DuckDB pasa el filtro a
-- la lectura y puede descartar grupos de filas cuyo rango de fechas, guardado en los
-- metadatos, no puede cumplirlo.
-- Fuente: data/raw/yellow/*/*.parquet, directo.
select max(fare_amount) as tarifa_maxima_agosto
from read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true)
where tpep_pickup_datetime >= timestamp '2026-08-01';
```

### `02_costo_todas.sql`

- **Objetivo:** el mismo calculo (maximo) sobre las 21 columnas, para comparar con la consulta de una sola columna (3.9).
- **Fuente:** data/raw/yellow/*/*.parquet, directo.
- **Resultado:** Alrededor de 0.6 s, mas de diez veces una columna.
- **Decision:** Evitar `select *` sobre los Parquet.

```sql
-- 02_costo_todas.sql
-- Objetivo: el mismo calculo (maximo) sobre las 21 columnas, para comparar con
-- la consulta de una sola columna (3.9).
-- Fuente: data/raw/yellow/*/*.parquet, directo.
select max(columns(*))
from read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true);
```

## Ejercicio 4: analisis exploratorio

### `03_viajes_por_mes.sql`

- **Objetivo:** viajes por mes y por dia de cada tipo de taxi (pregunta 1). Se divide entre los dias del mes porque febrero tiene 28 y los demas 30 o 31.
- **Fuente:** vista viajes_validos (sql/00_vistas.sql) sobre data/raw.
- **Resultado:** Amarillos: 118,867 viajes por dia en enero, maximo de 131,482 en mayo y 107,167 en agosto. Verdes: 1,295 en enero, 1,469 en abril y 1,307 en agosto.
- **Decision:** Comparar meses por dia y con indice base enero. Agrupa por `mes` sin `anio`: al agregar otro anio hay que sumar `anio` a la agrupacion.

```sql
-- 03_viajes_por_mes.sql
-- Objetivo: viajes por mes y por dia de cada tipo de taxi (pregunta 1). Se
-- divide entre los dias del mes porque febrero tiene 28 y los demas 30 o 31.
-- Fuente: vista viajes_validos (sql/00_vistas.sql) sobre data/raw.
select
    tipo,
    mes,
    count(*) as viajes,
    any_value(day(last_day(pickup_datetime))) as dias,
    count(*) / any_value(day(last_day(pickup_datetime))) as viajes_por_dia
from viajes_validos
group by tipo, mes
order by tipo desc, mes;
```

### `03_hora_dia.sql`

- **Objetivo:** viajes promedio por hora en cada dia de la semana, por tipo de taxi (pregunta 2). Se divide entre cuantas veces aparece cada dia de la semana en el periodo, porque de enero a agosto de 2026 algunos dias se repiten 35 veces y otros 34.
- **Fuente:** vista viajes_validos sobre data/raw.
- **Resultado:** Hora mas fuerte: amarillos jueves 18:00 (10,000 viajes por hora), verdes jueves 17:00 (133). Fin de semana contra dia habil: amarillos -1.0%, verdes -24.0%.
- **Decision:** Tratar a los verdes como servicio de dias habiles al comparar con los amarillos.

```sql
-- 03_hora_dia.sql
-- Objetivo: viajes promedio por hora en cada dia de la semana, por tipo de
-- taxi (pregunta 2). Se divide entre cuantas veces aparece cada dia de la
-- semana en el periodo, porque de enero a agosto de 2026 algunos dias se
-- repiten 35 veces y otros 34.
-- Fuente: vista viajes_validos sobre data/raw.
with conteo as (
    select tipo, dia_semana, hora, count(*) as viajes
    from viajes_validos
    group by tipo, dia_semana, hora
),
dias as (
    select tipo, dia_semana, count(distinct cast(pickup_datetime as date)) as dias
    from viajes_validos
    group by tipo, dia_semana
)
select
    conteo.tipo,
    conteo.dia_semana,
    conteo.hora,
    conteo.viajes,
    dias.dias,
    conteo.viajes / dias.dias as viajes_por_hora
from conteo
join dias using (tipo, dia_semana)
order by conteo.tipo desc, conteo.dia_semana, conteo.hora;
```

### `03_caracteristicas.sql`

- **Objetivo:** distribucion de distancia, duracion y velocidad de los viajes de cada tipo (pregunta 3), con percentiles exactos.
- **Fuente:** vista viajes_validos, solo viajes medibles (sin proveedor 7, con duracion entre 0 y 24 horas y distancia entre 0 y 100 millas).
- **Resultado:** Medianas: amarillos 1.93 millas, 14.1 min, 9.3 mph; verdes 2.15 millas, 13.4 min, 10.0 mph. El 1% mas largo de los amarillos pasa de 19.6 millas y 72 minutos.
- **Decision:** Usar medianas y percentiles, no promedios, para estas tres variables.

```sql
-- 03_caracteristicas.sql
-- Objetivo: distribucion de distancia, duracion y velocidad de los viajes de
-- cada tipo (pregunta 3), con percentiles exactos.
-- Fuente: vista viajes_validos, solo viajes medibles (sin proveedor 7, con
-- duracion entre 0 y 24 horas y distancia entre 0 y 100 millas).
with medibles as (
    select
        tipo,
        trip_distance as distancia_millas,
        duracion_min,
        trip_distance / (duracion_min / 60) as velocidad_mph
    from viajes_validos
    where medible
),
largo as (
    unpivot medibles
    on distancia_millas, duracion_min, velocidad_mph
    into name variable value valor
)
select
    variable,
    tipo,
    count(*) as viajes,
    quantile_cont(valor, 0.10) as p10,
    quantile_cont(valor, 0.25) as p25,
    quantile_cont(valor, 0.50) as mediana,
    quantile_cont(valor, 0.75) as p75,
    quantile_cont(valor, 0.90) as p90,
    quantile_cont(valor, 0.99) as p99
from largo
group by variable, tipo
order by variable, tipo desc;
```

### `03_velocidad_por_hora.sql`

- **Objetivo:** velocidad, duracion y distancia medianas segun la hora de salida (pregunta 3). La velocidad es la de todo el viaje: distancia del taximetro entre el tiempo con el taximetro encendido.
- **Fuente:** vista viajes_validos, solo viajes medibles.
- **Resultado:** Amarillos: 16.0 mph a las 5:00 y 7.9 a las 15:00; la duracion mediana solo va de 13.6 a 15.3 min y la distancia baja de 3.71 a 1.73 millas.
- **Decision:** La hora del dia se analiza con la velocidad y la distancia, porque la duracion casi no cambia.

```sql
-- 03_velocidad_por_hora.sql
-- Objetivo: velocidad, duracion y distancia medianas segun la hora de salida
-- (pregunta 3). La velocidad es la de todo el viaje: distancia del taximetro
-- entre el tiempo con el taximetro encendido.
-- Fuente: vista viajes_validos, solo viajes medibles.
select
    tipo,
    hora,
    count(*) as viajes,
    median(trip_distance / (duracion_min / 60)) as velocidad_mediana_mph,
    median(duracion_min) as duracion_mediana_min,
    median(trip_distance) as distancia_mediana_millas
from viajes_validos
where medible
group by tipo, hora
order by tipo desc, hora;
```

### `03_barrios.sql`

- **Objetivo:** en que barrio empiezan los viajes de cada tipo de taxi (pregunta 4).
- **Fuente:** vista viajes_validos unida con la vista zonas (taxi_zone_lookup.csv) por PULocationID. Las zonas 264 y 265 aparecen como Unknown y N/A.
- **Resultado:** Salen de Manhattan 86.6% de los amarillos y 58.3% de los verdes; de Brooklyn 3.6% y 15.7%.
- **Decision:** Comparar amarillos y verdes siempre por separado: atienden zonas distintas.

```sql
-- 03_barrios.sql
-- Objetivo: en que barrio empiezan los viajes de cada tipo de taxi (pregunta 4).
-- Fuente: vista viajes_validos unida con la vista zonas (taxi_zone_lookup.csv)
-- por PULocationID. Las zonas 264 y 265 aparecen como Unknown y N/A.
select
    v.tipo,
    coalesce(z.Borough, 'sin zona') as barrio,
    count(*) as viajes,
    100.0 * count(*) / sum(count(*)) over (partition by v.tipo) as pct_del_tipo
from viajes_validos v
left join zonas z on v.PULocationID = z.LocationID
group by v.tipo, barrio
order by v.tipo desc, viajes desc;
```

### `03_zonas_principales.sql`

- **Objetivo:** las ocho zonas donde mas viajes empiezan, por tipo de taxi (pregunta 4).
- **Fuente:** vista viajes_validos unida con la vista zonas por PULocationID.
- **Resultado:** Amarillos: ninguna zona pasa de 4.4%; JFK tiene 3.9%. Verdes: East Harlem North y South suman 39.1%.
- **Decision:** Ningun ajuste: confirma la diferencia geografica entre servicios.

```sql
-- 03_zonas_principales.sql
-- Objetivo: las ocho zonas donde mas viajes empiezan, por tipo de taxi
-- (pregunta 4).
-- Fuente: vista viajes_validos unida con la vista zonas por PULocationID.
with conteo as (
    select v.tipo, z.Zone as zona, z.Borough as barrio, count(*) as viajes
    from viajes_validos v
    left join zonas z on v.PULocationID = z.LocationID
    group by v.tipo, zona, barrio
)
select
    tipo,
    zona,
    barrio,
    viajes,
    100.0 * viajes / sum(viajes) over (partition by tipo) as pct_del_tipo
from conteo
qualify row_number() over (partition by tipo order by viajes desc) <= 8
order by tipo desc, viajes desc;
```

### `03_pago_por_mes.sql`

- **Objetivo:** como pagan los pasajeros de cada tipo de taxi, mes por mes (pregunta 5).
- **Fuente:** vista viajes_validos. payment_type segun el diccionario de la TLC: 0 Flex Fare (en verdes llega nulo), 1 tarjeta, 2 efectivo; 3 sin cargo, 4 disputa, 5 desconocido y 6 anulado se agrupan en "otro".
- **Resultado:** Tarjeta 61% a 69% en amarillos y 64% a 67% en verdes; efectivo 7.9% a 9.8% contra 18.3% a 20.7%; Flex Fare amarillo de 21.0% a 30.3%.
- **Decision:** Agrupa por `mes` sin `anio`: al agregar otro anio hay que sumar `anio` a la agrupacion.

```sql
-- 03_pago_por_mes.sql
-- Objetivo: como pagan los pasajeros de cada tipo de taxi, mes por mes
-- (pregunta 5).
-- Fuente: vista viajes_validos. payment_type segun el diccionario de la TLC:
-- 0 Flex Fare (en verdes llega nulo), 1 tarjeta, 2 efectivo; 3 sin cargo,
-- 4 disputa, 5 desconocido y 6 anulado se agrupan en "otro".
select
    tipo,
    mes,
    case
        when payment_type = 1 then 'tarjeta'
        when payment_type = 2 then 'efectivo'
        when payment_type = 0 or payment_type is null then 'flex fare'
        else 'otro'
    end as pago,
    count(*) as viajes,
    100.0 * count(*) / sum(count(*)) over (partition by tipo, mes) as pct_del_mes
from viajes_validos
group by tipo, mes, pago
order by tipo desc, mes, pago;
```

### `03_propina.sql`

- **Objetivo:** que parte de los viajes deja propina y de cuanto, segun la forma de pago (pregunta 5).
- **Fuente:** vista viajes_validos. El diccionario de la TLC aclara que tip_amount solo registra propinas con tarjeta; las de efectivo no quedan. La propina como porcentaje de la tarifa se calcula solo con tarifa positiva.
- **Resultado:** Con tarjeta deja propina 91.1% de los amarillos (mediana 3.51 dolares, 27.3% de la tarifa) y 90.4% de los verdes. En efectivo, 0.01%.
- **Decision:** Cualquier analisis de propina se limita a pagos con tarjeta.

```sql
-- 03_propina.sql
-- Objetivo: que parte de los viajes deja propina y de cuanto, segun la forma
-- de pago (pregunta 5).
-- Fuente: vista viajes_validos. El diccionario de la TLC aclara que
-- tip_amount solo registra propinas con tarjeta; las de efectivo no quedan.
-- La propina como porcentaje de la tarifa se calcula solo con tarifa positiva.
select
    tipo,
    case
        when payment_type = 1 then 'tarjeta'
        when payment_type = 2 then 'efectivo'
        when payment_type = 0 or payment_type is null then 'flex fare'
        else 'otro'
    end as pago,
    count(*) as viajes,
    100.0 * count_if(tip_amount > 0) / count(*) as pct_con_propina,
    median(tip_amount) filter (where tip_amount > 0) as propina_mediana,
    median(100 * tip_amount / fare_amount) filter (where tip_amount > 0 and fare_amount > 0)
        as propina_pct_tarifa_mediana
from viajes_validos
group by tipo, pago
order by tipo desc, viajes desc;
```

### `03_total_histograma.sql`

- **Objetivo:** distribucion del total pagado por viaje, en intervalos de 2 dolares hasta 150 (pregunta 6). Lo que pasa de 150 se junta en el ultimo intervalo para que la cola no aplaste el resto de la grafica.
- **Fuente:** vista viajes_validos.
- **Resultado:** El intervalo mas comun es 16 a 18 dolares (9.0% amarillos, 10.8% verdes); cola larga con un pico de amarillos entre 100 y 102 dolares.
- **Decision:** Revisar el pico con 03_pico_100_dolares.sql.

```sql
-- 03_total_histograma.sql
-- Objetivo: distribucion del total pagado por viaje, en intervalos de 2
-- dolares hasta 150 (pregunta 6). Lo que pasa de 150 se junta en el ultimo
-- intervalo para que la cola no aplaste el resto de la grafica.
-- Fuente: vista viajes_validos.
select
    tipo,
    least(floor(total_amount / 2) * 2, 150) as desde_dolares,
    count(*) as viajes,
    100.0 * count(*) / sum(count(*)) over (partition by tipo) as pct_del_tipo
from viajes_validos
group by tipo, desde_dolares
order by tipo desc, desde_dolares;
```

### `03_pico_100_dolares.sql`

- **Objetivo:** que viajes forman el pequeno pico de la distribucion del total entre 100 y 102 dolares en los amarillos (pregunta 6).
- **Fuente:** vista viajes_validos. RatecodeID 2 es la tarifa fija de JFK.
- **Resultado:** 83.3% de los viajes del pico tienen tarifa fija de JFK: 70 de tarifa, 7.46 de peajes y 16.44 de propina, total mediano 100.65.
- **Decision:** El pico es la tarifa fija de JFK, no un error.

```sql
-- 03_pico_100_dolares.sql
-- Objetivo: que viajes forman el pequeno pico de la distribucion del total
-- entre 100 y 102 dolares en los amarillos (pregunta 6).
-- Fuente: vista viajes_validos. RatecodeID 2 es la tarifa fija de JFK.
select
    RatecodeID,
    count(*) as viajes,
    100.0 * count(*) / sum(count(*)) over () as pct_del_pico,
    median(fare_amount) as tarifa_mediana,
    median(tolls_amount) as peajes_mediana,
    median(tip_amount) as propina_mediana,
    median(total_amount) as total_mediano
from viajes_validos
where tipo = 'yellow'
  and total_amount >= 100
  and total_amount < 102
group by RatecodeID
order by viajes desc;
```

### `03_composicion.sql`

- **Objetivo:** de que se compone el total pagado en promedio, por tipo de taxi (pregunta 6).
- **Fuente:** vista viajes_validos, solo viajes cuyo total coincide con la suma de sus componentes (diferencia de un centavo o menos). En los demas el desglose no es confiable (ver 03_total_no_cuadra.sql).
- **Resultado:** Total promedio 30.19 dolares en amarillos y 25.11 en verdes; la tarifa es 69% y 75% del total; congestion y zona central suman 2.63 dolares en amarillos y 0.90 en verdes.
- **Decision:** El desglose solo se reporta para viajes donde cuadra, y se aclara que es sobre todo el proveedor 2.

```sql
-- 03_composicion.sql
-- Objetivo: de que se compone el total pagado en promedio, por tipo de taxi
-- (pregunta 6).
-- Fuente: vista viajes_validos, solo viajes cuyo total coincide con la suma de
-- sus componentes (diferencia de un centavo o menos). En los demas el desglose
-- no es confiable (ver 03_total_no_cuadra.sql).
with v as (
    select
        *,
        fare_amount + extra + mta_tax + tip_amount + tolls_amount + improvement_surcharge
            + coalesce(congestion_surcharge, 0) + coalesce(Airport_fee, 0)
            + cbd_congestion_fee + coalesce(ehail_fee, 0) as suma_componentes
    from viajes_validos
)
select
    tipo,
    count(*) as viajes,
    avg(fare_amount) as tarifa,
    avg(tip_amount) as propina,
    avg(coalesce(congestion_surcharge, 0)) as recargo_congestion,
    avg(cbd_congestion_fee) as cargo_zona_central,
    avg(coalesce(Airport_fee, 0)) as cargo_aeropuerto,
    avg(tolls_amount) as peajes,
    avg(extra) as extras,
    avg(mta_tax + improvement_surcharge) as impuesto_y_mejora,
    avg(total_amount) as total
from v
where abs(total_amount - suma_componentes) <= 0.01
group by tipo
order by tipo desc;
```

### `03_inconsistencias.sql`

- **Objetivo:** registros que contradicen una regla entre columnas (pregunta 7).
- **Fuente:** vista viajes_validos. Reglas: total distinto de la suma de componentes (mas de un centavo); cargo de aeropuerto sin salir de JFK (zona 132) ni LaGuardia (138), que segun el diccionario es el unico caso en que se cobra; velocidad promedio mayor a 80 mph en un viaje medible; propina registrada en un viaje pagado en efectivo, que el diccionario dice que no se registra.
- **Resultado:** Total distinto de la suma: 10,895,265 amarillos (36.9%) y 66,968 verdes (19.9%). Cargo de aeropuerto fuera del aeropuerto: 56,287. Mas de 80 mph: 7,210 y 1,087. Efectivo con propina: 182.
- **Decision:** Investigar el total que no cuadra por proveedor (03_total_no_cuadra.sql).

```sql
-- 03_inconsistencias.sql
-- Objetivo: registros que contradicen una regla entre columnas (pregunta 7).
-- Fuente: vista viajes_validos. Reglas:
--   total distinto de la suma de componentes (mas de un centavo);
--   cargo de aeropuerto sin salir de JFK (zona 132) ni LaGuardia (138), que
--   segun el diccionario es el unico caso en que se cobra;
--   velocidad promedio mayor a 80 mph en un viaje medible;
--   propina registrada en un viaje pagado en efectivo, que el diccionario
--   dice que no se registra.
select
    tipo,
    count(*) as viajes,
    count_if(abs(total_amount - (fare_amount + extra + mta_tax + tip_amount + tolls_amount
        + improvement_surcharge + coalesce(congestion_surcharge, 0) + coalesce(Airport_fee, 0)
        + cbd_congestion_fee + coalesce(ehail_fee, 0))) > 0.01) as total_no_cuadra,
    count_if(Airport_fee > 0) as con_cargo_aeropuerto,
    count_if(Airport_fee > 0 and PULocationID not in (132, 138)) as cargo_aeropuerto_fuera,
    count_if(medible) as medibles,
    count_if(medible and trip_distance / (duracion_min / 60) > 80) as mas_de_80_mph,
    count_if(payment_type = 2) as en_efectivo,
    count_if(payment_type = 2 and tip_amount > 0) as efectivo_con_propina
from viajes_validos
group by tipo
order by tipo desc;
```

### `03_total_no_cuadra.sql`

- **Objetivo:** en cuantos viajes el total no es la suma de sus componentes y de quien vienen (pregunta 7). Componentes: tarifa, extras, impuesto MTA, propina, peajes, recargo de mejora, recargo de congestion, cargo de aeropuerto, cargo de la zona central y ehail_fee.
- **Fuente:** vista viajes_validos.
- **Resultado:** Proveedor 2 sin Flex Fare: no cuadra 0.13% (amarillos) y 0.04% (verdes). Proveedor 1: 83.4%, con diferencia mediana de -3.25. Flex Fare: 88% a 98%. Proveedor 6: 100%.
- **Decision:** Usar `total_amount` tal como viene; el desglose solo donde cuadra.

```sql
-- 03_total_no_cuadra.sql
-- Objetivo: en cuantos viajes el total no es la suma de sus componentes y de
-- quien vienen (pregunta 7). Componentes: tarifa, extras, impuesto MTA,
-- propina, peajes, recargo de mejora, recargo de congestion, cargo de
-- aeropuerto, cargo de la zona central y ehail_fee.
-- Fuente: vista viajes_validos.
with v as (
    select
        tipo,
        VendorID,
        payment_type = 0 or payment_type is null as flex_fare,
        total_amount - (fare_amount + extra + mta_tax + tip_amount + tolls_amount
            + improvement_surcharge + coalesce(congestion_surcharge, 0)
            + coalesce(Airport_fee, 0) + cbd_congestion_fee + coalesce(ehail_fee, 0)) as diferencia
    from viajes_validos
)
select
    tipo,
    VendorID,
    flex_fare,
    count(*) as viajes,
    count_if(abs(diferencia) > 0.01) as no_cuadra,
    100.0 * count_if(abs(diferencia) > 0.01) / count(*) as pct_no_cuadra,
    median(diferencia) filter (where abs(diferencia) > 0.01) as diferencia_mediana
from v
group by tipo, VendorID, flex_fare
order by tipo desc, VendorID, flex_fare;
```

### `03_atipicos.sql`

- **Objetivo:** cuantos viajes quedan por encima del limite de Tukey (tercer cuartil mas 1.5 veces el rango intercuartil) en total, distancia y duracion, por tipo de taxi (pregunta 7).
- **Fuente:** vista viajes_validos; distancia y duracion solo de viajes medibles.
- **Resultado:** Sobre el limite de Tukey, amarillos: 8.5% por total (60.50 dolares), 10.9% por distancia (8.2 millas), 5.4% por duracion (42.7 min). Verdes: 6.8%, 10.2% y 7.1%.
- **Decision:** No usar Tukey para limpiar: marca demasiados viajes reales (ver 03_atipicos_por_tarifa.sql).

```sql
-- 03_atipicos.sql
-- Objetivo: cuantos viajes quedan por encima del limite de Tukey (tercer
-- cuartil mas 1.5 veces el rango intercuartil) en total, distancia y
-- duracion, por tipo de taxi (pregunta 7).
-- Fuente: vista viajes_validos; distancia y duracion solo de viajes medibles.
with largo as (
    select tipo, 'total_dolares' as variable, total_amount as valor from viajes_validos
    union all
    select tipo, 'distancia_millas', trip_distance from viajes_validos where medible
    union all
    select tipo, 'duracion_min', duracion_min from viajes_validos where medible
),
limites as (
    select
        tipo,
        variable,
        quantile_cont(valor, 0.25) as q1,
        quantile_cont(valor, 0.75) as q3
    from largo
    group by tipo, variable
)
select
    l.variable,
    l.tipo,
    any_value(q1) as q1,
    any_value(q3) as q3,
    any_value(q3 + 1.5 * (q3 - q1)) as limite_superior,
    count(*) as viajes,
    count_if(l.valor > q3 + 1.5 * (q3 - q1)) as sobre_el_limite,
    100.0 * count_if(l.valor > q3 + 1.5 * (q3 - q1)) / count(*) as pct_sobre_el_limite
from largo l
join limites using (tipo, variable)
group by l.variable, l.tipo
order by l.variable, l.tipo desc;
```

### `03_atipicos_por_tarifa.sql`

- **Objetivo:** con que codigo de tarifa vienen los viajes cuyo total pasa el limite de Tukey, para saber si son errores o viajes de otra clase (pregunta 7).
- **Fuente:** vista viajes_validos. RatecodeID segun el diccionario de la TLC: 1 estandar, 2 JFK, 3 Newark, 4 Nassau o Westchester, 5 negociada, 6 grupal, 99 desconocido; nulo en los viajes Flex Fare.
- **Resultado:** De los amarillos sobre el limite del total: 27.2% tarifa fija de JFK, 7.3% negociada, 2.7% Newark, 2.1% Nassau o Westchester y 42.6% estandar con tarifa mediana de 49.20.
- **Decision:** Los atipicos del total son viajes legitimos; no se eliminan.

```sql
-- 03_atipicos_por_tarifa.sql
-- Objetivo: con que codigo de tarifa vienen los viajes cuyo total pasa el
-- limite de Tukey, para saber si son errores o viajes de otra clase
-- (pregunta 7).
-- Fuente: vista viajes_validos. RatecodeID segun el diccionario de la TLC:
-- 1 estandar, 2 JFK, 3 Newark, 4 Nassau o Westchester, 5 negociada,
-- 6 grupal, 99 desconocido; nulo en los viajes Flex Fare.
with limites as (
    select
        tipo,
        quantile_cont(total_amount, 0.75)
            + 1.5 * (quantile_cont(total_amount, 0.75) - quantile_cont(total_amount, 0.25)) as limite
    from viajes_validos
    group by tipo
)
select
    v.tipo,
    case v.RatecodeID
        when 1 then '1 estandar'
        when 2 then '2 JFK'
        when 3 then '3 Newark'
        when 4 then '4 Nassau o Westchester'
        when 5 then '5 negociada'
        when 6 then '6 grupal'
        when 99 then '99 desconocido'
        else 'sin codigo (flex fare)'
    end as codigo_tarifa,
    count(*) as viajes,
    100.0 * count(*) / sum(count(*)) over (partition by v.tipo) as pct_de_los_atipicos,
    median(v.fare_amount) as tarifa_mediana,
    median(v.total_amount) as total_mediano
from viajes_validos v
join limites using (tipo)
where v.total_amount > limites.limite
group by v.tipo, codigo_tarifa
order by v.tipo desc, viajes desc;
```
