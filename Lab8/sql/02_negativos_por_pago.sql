-- 02_negativos_por_pago.sql
-- Objetivo: con que tipo de pago y proveedor vienen los viajes con tarifa
-- negativa, para saber si son errores de captura o ajustes (3.6).
-- Fuente: data/raw/*/*/*.parquet, directo.
-- payment_type segun el diccionario de la TLC: 0 Flex Fare, 1 tarjeta,
-- 2 efectivo, 3 sin cargo, 4 disputa, 5 desconocido, 6 viaje anulado.
select
    split_part(filename, '/', -3) as tipo,
    VendorID,
    payment_type,
    count(*) as registros,
    round(median(fare_amount), 2) as tarifa_mediana
from read_parquet('data/raw/*/*/*.parquet', union_by_name = true, filename = true)
where fare_amount < 0
group by all
order by tipo desc, registros desc;
