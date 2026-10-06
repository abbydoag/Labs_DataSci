-- 02_archivos.sql
-- Objetivo: cuantos archivos Parquet hay por tipo de taxi y que meses cubren (3.1).
-- Fuente: data/raw/*/*/*.parquet, listados con glob(); no abre ningun archivo.
select
    split_part(file, '/', -3) as tipo,
    count(*) as archivos,
    min(regexp_extract(file, '(\d{4}-\d{2})\.parquet$', 1)) as primer_mes,
    max(regexp_extract(file, '(\d{4}-\d{2})\.parquet$', 1)) as ultimo_mes
from glob('data/raw/*/*/*.parquet')
group by tipo
order by tipo desc;
