-- 03_composicion.sql
-- Objetivo: de que se compone el total pagado en promedio, por tipo de taxi
-- (pregunta 6).
-- Fuente: vista viajes_validos, solo viajes cuyo total coincide con la suma de
-- sus componentes (diferencia de un centavo o menos). En los demas el desglose
-- no es confiable (ver 03_total_no_cuadra.sql).
with v as (
    select
        *,
        fare_amount + extra + mta_tax + tip_amount + tolls_amount + improvement_surcharge
            + coalesce(congestion_surcharge, 0) + coalesce(Airport_fee, 0)
            + cbd_congestion_fee + coalesce(ehail_fee, 0) as suma_componentes
    from viajes_validos
)
select
    tipo,
    count(*) as viajes,
    avg(fare_amount) as tarifa,
    avg(tip_amount) as propina,
    avg(coalesce(congestion_surcharge, 0)) as recargo_congestion,
    avg(cbd_congestion_fee) as cargo_zona_central,
    avg(coalesce(Airport_fee, 0)) as cargo_aeropuerto,
    avg(tolls_amount) as peajes,
    avg(extra) as extras,
    avg(mta_tax + improvement_surcharge) as impuesto_y_mejora,
    avg(total_amount) as total
from v
where abs(total_amount - suma_componentes) <= 0.01
group by tipo
order by tipo desc;
