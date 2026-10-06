-- 02_resumen_green.sql
-- Objetivo: perfil de cada columna de los taxis green: minimo, maximo, valores
-- distintos aproximados, cuartiles y porcentaje de nulos (3.4 y 3.6).
-- Fuente: data/raw/green/*/*.parquet, directo.
summarize select * from read_parquet('data/raw/green/*/*.parquet', union_by_name = true);
