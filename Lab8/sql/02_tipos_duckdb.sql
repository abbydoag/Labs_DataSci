-- 02_tipos_duckdb.sql
-- Objetivo: tipo con el que DuckDB expone cada columna al leer los archivos (3.4).
-- Fuente: data/raw/*/*/*.parquet, directo. Con union_by_name las columnas de
-- amarillos y verdes quedan en una sola lista, en el orden en que aparecen.
select
    column_name as columna,
    column_type as tipo_duckdb
from (describe select * from read_parquet('data/raw/*/*/*.parquet', union_by_name = true));
