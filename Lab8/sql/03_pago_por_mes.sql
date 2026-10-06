-- 03_pago_por_mes.sql
-- Objetivo: como pagan los pasajeros de cada tipo de taxi, mes por mes
-- (pregunta 5).
-- Fuente: vista viajes_validos. payment_type segun el diccionario de la TLC:
-- 0 Flex Fare (en verdes llega nulo), 1 tarjeta, 2 efectivo; 3 sin cargo,
-- 4 disputa, 5 desconocido y 6 anulado se agrupan en "otro".
select
    tipo,
    mes,
    case
        when payment_type = 1 then 'tarjeta'
        when payment_type = 2 then 'efectivo'
        when payment_type = 0 or payment_type is null then 'flex fare'
        else 'otro'
    end as pago,
    count(*) as viajes,
    100.0 * count(*) / sum(count(*)) over (partition by tipo, mes) as pct_del_mes
from viajes_validos
group by tipo, mes, pago
order by tipo desc, mes, pago;
