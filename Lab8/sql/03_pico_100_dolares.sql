-- 03_pico_100_dolares.sql
-- Objetivo: que viajes forman el pequeno pico de la distribucion del total
-- entre 100 y 102 dolares en los amarillos (pregunta 6).
-- Fuente: vista viajes_validos. RatecodeID 2 es la tarifa fija de JFK.
select
    RatecodeID,
    count(*) as viajes,
    100.0 * count(*) / sum(count(*)) over () as pct_del_pico,
    median(fare_amount) as tarifa_mediana,
    median(tolls_amount) as peajes_mediana,
    median(tip_amount) as propina_mediana,
    median(total_amount) as total_mediano
from viajes_validos
where tipo = 'yellow'
  and total_amount >= 100
  and total_amount < 102
group by RatecodeID
order by viajes desc;
