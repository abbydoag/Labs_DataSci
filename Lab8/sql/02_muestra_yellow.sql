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
