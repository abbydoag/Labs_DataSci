-- 02_costo_conteo.sql
-- Objetivo: tiempo de contar los registros de los amarillos (3.9). DuckDB lo
-- resuelve con el numero de filas que trae el pie de cada archivo.
-- Fuente: data/raw/yellow/*/*.parquet, directo.
select count(*) as registros
from read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true);
