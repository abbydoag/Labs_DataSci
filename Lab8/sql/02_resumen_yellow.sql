-- 02_resumen_yellow.sql
-- Objetivo: perfil de cada columna de los taxis yellow: minimo, maximo, valores
-- distintos aproximados, cuartiles y porcentaje de nulos (3.4 y 3.6).
-- Fuente: data/raw/yellow/*/*.parquet, directo.
summarize select * from read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true);
