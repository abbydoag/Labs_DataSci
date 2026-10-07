-- 04_indice_mensual.sql
-- Objetivo: viajes por dia de 2026 como indice con el mismo mes de 2024 = 100.
-- Fuente: data/raw/*/{2024,2026}/*.parquet, directo.
-- Se restringe a enero-agosto.
with mensual as (
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
)
select
    m.tipo,
    m.anio,
    m.mes,
    m.viajes_por_dia,
    100.0 * m.viajes_por_dia / b.viajes_por_dia as indice_2024_100
from mensual m
join mensual b on m.tipo = b.tipo and m.mes = b.mes and b.anio = '2024'
order by m.tipo desc, m.mes, m.anio;
