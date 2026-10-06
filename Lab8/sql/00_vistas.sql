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
