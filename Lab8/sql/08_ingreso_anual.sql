-- 08_ingreso_anual.sql
-- Objetivo: ingreso promedio por año y tipo (8.4).
-- Fuente: viajes_validos
select
    tipo,
    anio,
    avg(total_amount) as ingreso_promedio
from viajes_validos
where medible and total_amount > 0
group by tipo, anio
order by tipo, anio;
