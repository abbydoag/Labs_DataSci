-- 02_calidad.sql
-- Objetivo: cuantos registros tienen cada problema de calidad, por tipo de
-- taxi (3.6). Cada columna cuenta una regla; un registro puede caer en varias.
-- Fuente: data/raw/*/*/*.parquet, directo.
-- Las fechas tienen prefijo distinto por tipo (tpep_, lpep_); con
-- union_by_name la del otro tipo queda nula y coalesce toma la que existe.
with v as (
    select
        split_part(filename, '/', -3) as tipo,
        regexp_extract(filename, '(\d{4}-\d{2})\.parquet$', 1) as mes_archivo,
        coalesce(tpep_pickup_datetime, lpep_pickup_datetime) as inicio,
        coalesce(tpep_dropoff_datetime, lpep_dropoff_datetime) as fin,
        *
    from read_parquet('data/raw/*/*/*.parquet', union_by_name = true, filename = true)
)
select
    tipo,
    count(*) as registros,
    count_if(strftime(inicio, '%Y-%m') <> mes_archivo) as inicio_fuera_del_mes_del_archivo,
    count_if(fin < inicio) as fin_antes_del_inicio,
    count_if(fin = inicio) as duracion_cero,
    count_if(fin - inicio > interval 24 hours) as duracion_mayor_24h,
    count_if(trip_distance = 0) as distancia_cero,
    count_if(trip_distance > 100) as distancia_mayor_100_millas,
    count_if(fare_amount < 0) as tarifa_negativa,
    count_if(total_amount < 0) as total_negativo,
    count_if(tip_amount < 0) as propina_negativa,
    count_if(passenger_count is null) as pasajeros_nulo,
    count_if(passenger_count = 0) as pasajeros_cero,
    count_if(RatecodeID = 99) as codigo_tarifa_99,
    count_if(payment_type is null or payment_type = 0) as pago_sin_tipo,
    count_if(PULocationID in (264, 265) or DOLocationID in (264, 265)) as zona_desconocida
from v
group by tipo
order by tipo desc;
