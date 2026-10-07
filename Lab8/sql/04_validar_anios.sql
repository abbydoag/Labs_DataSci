-- 04_validar_anios.sql
-- Objetivo: comprobar que DuckDB ve los archivos de 2024 y 2026 juntos (5.6).
-- Fuente: data/raw/*/*/*.parquet, directo.
select
    split_part(file_name, '/', -3) as tipo,
    split_part(file_name, '/', -2) as anio,
    count(*) as archivos,
    min(regexp_extract(file_name, '(\d{4}-\d{2})\.parquet$', 1)) as primer_mes,
    max(regexp_extract(file_name, '(\d{4}-\d{2})\.parquet$', 1)) as ultimo_mes,
    sum(num_rows) as registros
from parquet_file_metadata('data/raw/*/*/*.parquet')
group by tipo, anio
order by tipo desc, anio;
