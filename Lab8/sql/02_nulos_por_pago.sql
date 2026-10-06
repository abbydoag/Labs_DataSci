-- 02_nulos_por_pago.sql
-- Objetivo: ver si los nulos de pasajeros, codigo de tarifa y recargos estan
-- repartidos al azar o concentrados en un tipo de pago (3.6).
-- Fuente: data/raw/*/*/*.parquet, directo.
select
    split_part(filename, '/', -3) as tipo,
    payment_type,
    count(*) as registros,
    count(*) - count(passenger_count) as sin_pasajeros,
    count(*) - count(RatecodeID) as sin_codigo_tarifa,
    count(*) - count(store_and_fwd_flag) as sin_store_and_fwd,
    count(*) - count(congestion_surcharge) as sin_recargo_congestion
from read_parquet('data/raw/*/*/*.parquet', union_by_name = true, filename = true)
group by all
order by tipo desc, payment_type nulls last;
