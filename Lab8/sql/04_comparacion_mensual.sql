-- 04_comparacion_mensual.sql
-- Objetivo: viajes por dia de cada mes, 2024 y 2026, por tipo (5).
-- Fuente: data/raw/*/*/*.parquet, directo.
-- Se restringe a enero-agosto porque 2026 solo tiene esos meses publicados.
select
    split_part(filename, '/', -3) as tipo,
    split_part(filename, '/', -2) as anio,
    cast(extract(month from coalesce(tpep_pickup_datetime, lpep_pickup_datetime)) as integer) as mes,
    count(*) / any_value(
        extract(day from last_day(coalesce(tpep_pickup_datetime, lpep_pickup_datetime)))
    ) as viajes_por_dia
from read_parquet('data/raw/*/*/*.parquet', union_by_name = true, filename = true)
where split_part(filename, '/', -2) in ('2024', '2026')
  and extract(month from coalesce(tpep_pickup_datetime, lpep_pickup_datetime)) between 1 and 8
group by tipo, anio, mes
order by tipo desc, mes, anio;
