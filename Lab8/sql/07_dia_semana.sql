-- 07_dia_semana.sql
-- Objetivo: viajes promedio por día de semana (Indicador 7).
-- Fuente: viajes_validos
select
    tipo,
    dia_semana,
    count(*) / count(distinct cast(pickup_datetime as date)) as viajes_promedio
from viajes_validos
where medible
group by tipo, dia_semana
order by tipo, dia_semana;
