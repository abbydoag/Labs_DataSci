-- 03_atipicos_por_tarifa.sql
-- Objetivo: con que codigo de tarifa vienen los viajes cuyo total pasa el
-- limite de Tukey, para saber si son errores o viajes de otra clase
-- (pregunta 7).
-- Fuente: vista viajes_validos. RatecodeID segun el diccionario de la TLC:
-- 1 estandar, 2 JFK, 3 Newark, 4 Nassau o Westchester, 5 negociada,
-- 6 grupal, 99 desconocido; nulo en los viajes Flex Fare.
with limites as (
    select
        tipo,
        quantile_cont(total_amount, 0.75)
            + 1.5 * (quantile_cont(total_amount, 0.75) - quantile_cont(total_amount, 0.25)) as limite
    from viajes_validos
    group by tipo
)
select
    v.tipo,
    case v.RatecodeID
        when 1 then '1 estandar'
        when 2 then '2 JFK'
        when 3 then '3 Newark'
        when 4 then '4 Nassau o Westchester'
        when 5 then '5 negociada'
        when 6 then '6 grupal'
        when 99 then '99 desconocido'
        else 'sin codigo (flex fare)'
    end as codigo_tarifa,
    count(*) as viajes,
    100.0 * count(*) / sum(count(*)) over (partition by v.tipo) as pct_de_los_atipicos,
    median(v.fare_amount) as tarifa_mediana,
    median(v.total_amount) as total_mediano
from viajes_validos v
join limites using (tipo)
where v.total_amount > limites.limite
group by v.tipo, codigo_tarifa
order by v.tipo desc, viajes desc;
