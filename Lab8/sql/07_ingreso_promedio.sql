-- 07_ingreso_promedio.sql
-- Objetivo: ingreso promedio por viaje según tipo (Indicador 2).
-- Fuente: viajes_validos
select
    tipo,
    avg(total_amount) as ingreso_promedio
from viajes_validos
where medible and total_amount > 0
group by tipo
order by tipo;
