-- 07_viajes_diarios.sql
-- Objetivo: viajes diarios por tipo de taxi (Indicador 1).
-- Fuente: viajes_validos
select
    tipo,
    cast(pickup_datetime as date) as fecha,
    count(*) as viajes
from viajes_validos
where medible
group by tipo, fecha
order by tipo, fecha;
