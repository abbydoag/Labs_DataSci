-- 03_atipicos.sql
-- Objetivo: cuantos viajes quedan por encima del limite de Tukey (tercer
-- cuartil mas 1.5 veces el rango intercuartil) en total, distancia y
-- duracion, por tipo de taxi (pregunta 7).
-- Fuente: vista viajes_validos; distancia y duracion solo de viajes medibles.
with largo as (
    select tipo, 'total_dolares' as variable, total_amount as valor from viajes_validos
    union all
    select tipo, 'distancia_millas', trip_distance from viajes_validos where medible
    union all
    select tipo, 'duracion_min', duracion_min from viajes_validos where medible
),
limites as (
    select
        tipo,
        variable,
        quantile_cont(valor, 0.25) as q1,
        quantile_cont(valor, 0.75) as q3
    from largo
    group by tipo, variable
)
select
    l.variable,
    l.tipo,
    any_value(q1) as q1,
    any_value(q3) as q3,
    any_value(q3 + 1.5 * (q3 - q1)) as limite_superior,
    count(*) as viajes,
    count_if(l.valor > q3 + 1.5 * (q3 - q1)) as sobre_el_limite,
    100.0 * count_if(l.valor > q3 + 1.5 * (q3 - q1)) / count(*) as pct_sobre_el_limite
from largo l
join limites using (tipo, variable)
group by l.variable, l.tipo
order by l.variable, l.tipo desc;
