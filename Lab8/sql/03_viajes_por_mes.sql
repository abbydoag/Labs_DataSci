-- 03_viajes_por_mes.sql
-- Objetivo: viajes por mes y por dia de cada tipo de taxi (pregunta 1). Se
-- divide entre los dias del mes porque febrero tiene 28 y los demas 30 o 31.
-- Fuente: vista viajes_validos (sql/00_vistas.sql) sobre data/raw.
select
    tipo,
    mes,
    count(*) as viajes,
    any_value(day(last_day(pickup_datetime))) as dias,
    count(*) / any_value(day(last_day(pickup_datetime))) as viajes_por_dia
from viajes_validos
group by tipo, mes
order by tipo desc, mes;
