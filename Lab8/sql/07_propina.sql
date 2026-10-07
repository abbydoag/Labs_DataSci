-- 07_propina.sql
-- Objetivo: propina promedio según tipo de pago (Indicador 3).
-- Fuente: viajes_validos
select
    tipo,
    case when payment_type in (1, 2) then 'tarjeta'
         when payment_type in (3, 4) then 'efectivo'
         else 'otro' end as pago,
    avg(tip_amount) as propina_promedio
from viajes_validos
where medible
group by tipo, pago
order by tipo, pago;
