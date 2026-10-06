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
