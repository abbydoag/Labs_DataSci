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
- **Resultado:** Cuatro vistas: `yellow`, `green`, `viajes` (los dos tipos con las fechas renombradas a `pickup_datetime` y `dropoff_datetime`) y `zonas`. No copian datos.
- **Decision:** Los cuadernos 03 en adelante consultan `viajes`. Un anio nuevo en `data/raw` entra en las vistas sin tocar ninguna consulta.

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
