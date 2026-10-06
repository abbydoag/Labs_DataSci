-- 02_costo_filtro.sql
-- Objetivo: una columna con un filtro por fecha (3.9). DuckDB pasa el filtro a
-- la lectura y puede descartar grupos de filas cuyo rango de fechas, guardado en los
-- metadatos, no puede cumplirlo.
-- Fuente: data/raw/yellow/*/*.parquet, directo.
select max(fare_amount) as tarifa_maxima_agosto
from read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true)
where tpep_pickup_datetime >= timestamp '2026-08-01';
