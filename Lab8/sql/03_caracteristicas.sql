-- 03_caracteristicas.sql
-- Objetivo: distribucion de distancia, duracion y velocidad de los viajes de
-- cada tipo (pregunta 3), con percentiles exactos.
-- Fuente: vista viajes_validos, solo viajes medibles (sin proveedor 7, con
-- duracion entre 0 y 24 horas y distancia entre 0 y 100 millas).
with medibles as (
    select
        tipo,
        trip_distance as distancia_millas,
        duracion_min,
        trip_distance / (duracion_min / 60) as velocidad_mph
    from viajes_validos
    where medible
),
largo as (
    unpivot medibles
    on distancia_millas, duracion_min, velocidad_mph
    into name variable value valor
)
select
    variable,
    tipo,
    count(*) as viajes,
    quantile_cont(valor, 0.10) as p10,
    quantile_cont(valor, 0.25) as p25,
    quantile_cont(valor, 0.50) as mediana,
    quantile_cont(valor, 0.75) as p75,
    quantile_cont(valor, 0.90) as p90,
    quantile_cont(valor, 0.99) as p99
from largo
group by variable, tipo
order by variable, tipo desc;
