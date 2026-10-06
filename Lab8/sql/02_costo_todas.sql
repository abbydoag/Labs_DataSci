-- 02_costo_todas.sql
-- Objetivo: el mismo calculo (maximo) sobre las 21 columnas, para comparar con
-- la consulta de una sola columna (3.9).
-- Fuente: data/raw/yellow/*/*.parquet, directo.
select max(columns(*))
from read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true);
