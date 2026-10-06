-- 03_hora_dia.sql
-- Objetivo: viajes promedio por hora en cada dia de la semana, por tipo de
-- taxi (pregunta 2). Se divide entre cuantas veces aparece cada dia de la
-- semana en el periodo, porque de enero a agosto de 2026 algunos dias se
-- repiten 35 veces y otros 34.
-- Fuente: vista viajes_validos sobre data/raw.
with conteo as (
    select tipo, dia_semana, hora, count(*) as viajes
    from viajes_validos
    group by tipo, dia_semana, hora
),
dias as (
    select tipo, dia_semana, count(distinct cast(pickup_datetime as date)) as dias
    from viajes_validos
    group by tipo, dia_semana
)
select
    conteo.tipo,
    conteo.dia_semana,
    conteo.hora,
    conteo.viajes,
    dias.dias,
    conteo.viajes / dias.dias as viajes_por_hora
from conteo
join dias using (tipo, dia_semana)
order by conteo.tipo desc, conteo.dia_semana, conteo.hora;
