-- 03_total_histograma.sql
-- Objetivo: distribucion del total pagado por viaje, en intervalos de 2
-- dolares hasta 150 (pregunta 6). Lo que pasa de 150 se junta en el ultimo
-- intervalo para que la cola no aplaste el resto de la grafica.
-- Fuente: vista viajes_validos.
select
    tipo,
    least(floor(total_amount / 2) * 2, 150) as desde_dolares,
    count(*) as viajes,
    100.0 * count(*) / sum(count(*)) over (partition by tipo) as pct_del_tipo
from viajes_validos
group by tipo, desde_dolares
order by tipo desc, desde_dolares;
