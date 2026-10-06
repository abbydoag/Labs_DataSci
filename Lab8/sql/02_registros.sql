-- 02_registros.sql
-- Objetivo: cuantos registros hay por tipo de taxi (3.2).
-- Fuente: data/raw/*/*/*.parquet, directo. El tipo sale de la ruta del archivo.
select
    split_part(filename, '/', -3) as tipo,
    count(*) as registros
from read_parquet('data/raw/*/*/*.parquet', union_by_name = true, filename = true)
group by tipo
order by tipo desc;
