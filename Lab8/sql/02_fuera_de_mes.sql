-- 02_fuera_de_mes.sql
-- Objetivo: de los viajes cuya fecha de inicio no cae en el mes de su archivo,
-- a que mes corresponden y en que archivos estan (3.6).
-- Fuente: data/raw/*/*/*.parquet, directo.
with v as (
    select
        split_part(filename, '/', -3) as tipo,
        regexp_extract(filename, '(\d{4}-\d{2})\.parquet$', 1) as mes_archivo,
        strftime(coalesce(tpep_pickup_datetime, lpep_pickup_datetime), '%Y-%m') as mes_inicio
    from read_parquet('data/raw/*/*/*.parquet', union_by_name = true, filename = true)
)
select
    tipo,
    mes_inicio,
    count(*) as registros,
    string_agg(distinct mes_archivo, ', ' order by mes_archivo) as archivos
from v
where mes_inicio <> mes_archivo
group by tipo, mes_inicio
order by tipo desc, mes_inicio;
