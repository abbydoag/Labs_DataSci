-- 07_velocidad_hora.sql
-- Objetivo: velocidad promedio por hora del día (Indicador 4).
-- Fuente: viajes_validos
select
    tipo,
    hora,
    avg(trip_distance / (duracion_min / 60)) as velocidad_mph
from viajes_validos
where medible and duracion_min > 0
group by tipo, hora
order by tipo, hora;
