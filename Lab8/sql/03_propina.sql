-- 03_propina.sql
-- Objetivo: que parte de los viajes deja propina y de cuanto, segun la forma
-- de pago (pregunta 5).
-- Fuente: vista viajes_validos. El diccionario de la TLC aclara que
-- tip_amount solo registra propinas con tarjeta; las de efectivo no quedan.
-- La propina como porcentaje de la tarifa se calcula solo con tarifa positiva.
select
    tipo,
    case
        when payment_type = 1 then 'tarjeta'
        when payment_type = 2 then 'efectivo'
        when payment_type = 0 or payment_type is null then 'flex fare'
        else 'otro'
    end as pago,
    count(*) as viajes,
    100.0 * count_if(tip_amount > 0) / count(*) as pct_con_propina,
    median(tip_amount) filter (where tip_amount > 0) as propina_mediana,
    median(100 * tip_amount / fare_amount) filter (where tip_amount > 0 and fare_amount > 0)
        as propina_pct_tarifa_mediana
from viajes_validos
group by tipo, pago
order by tipo desc, viajes desc;
