-- 08_evolucion_anual.sql
-- Objetivo: evolución anual de viajes por tipo (8.4).
-- Fuente: viajes_validos
select
    tipo,
    anio,
    count(*) as viajes
from viajes_validos
where medible
group by tipo, anio
order by tipo, anio;
