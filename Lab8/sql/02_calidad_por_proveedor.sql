-- 02_calidad_por_proveedor.sql
-- Objetivo: ver si los problemas de calidad estan repartidos entre los
-- proveedores de tecnologia (VendorID) o concentrados en alguno (3.6).
-- Fuente: data/raw/*/*/*.parquet, directo.
-- VendorID segun el diccionario de la TLC: 1 Creative Mobile Technologies,
-- 2 Curb Mobility, 6 Myle Technologies, 7 Helix.
select
    split_part(filename, '/', -3) as tipo,
    VendorID,
    count(*) as registros,
    count_if(coalesce(tpep_dropoff_datetime, lpep_dropoff_datetime)
             = coalesce(tpep_pickup_datetime, lpep_pickup_datetime)) as duracion_cero,
    count_if(trip_distance = 0) as distancia_cero,
    count_if(fare_amount < 0) as tarifa_negativa,
    count_if(RatecodeID = 99) as codigo_tarifa_99,
    count_if(payment_type is null or payment_type = 0) as pago_sin_tipo,
    count_if(passenger_count = 0) as pasajeros_cero
from read_parquet('data/raw/*/*/*.parquet', union_by_name = true, filename = true)
group by all
order by tipo desc, VendorID;
