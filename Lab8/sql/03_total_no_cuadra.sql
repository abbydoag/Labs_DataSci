-- 03_total_no_cuadra.sql
-- Objetivo: en cuantos viajes el total no es la suma de sus componentes y de
-- quien vienen (pregunta 7). Componentes: tarifa, extras, impuesto MTA,
-- propina, peajes, recargo de mejora, recargo de congestion, cargo de
-- aeropuerto, cargo de la zona central y ehail_fee.
-- Fuente: vista viajes_validos.
with v as (
    select
        tipo,
        VendorID,
        payment_type = 0 or payment_type is null as flex_fare,
        total_amount - (fare_amount + extra + mta_tax + tip_amount + tolls_amount
            + improvement_surcharge + coalesce(congestion_surcharge, 0)
            + coalesce(Airport_fee, 0) + cbd_congestion_fee + coalesce(ehail_fee, 0)) as diferencia
    from viajes_validos
)
select
    tipo,
    VendorID,
    flex_fare,
    count(*) as viajes,
    count_if(abs(diferencia) > 0.01) as no_cuadra,
    100.0 * count_if(abs(diferencia) > 0.01) / count(*) as pct_no_cuadra,
    median(diferencia) filter (where abs(diferencia) > 0.01) as diferencia_mediana
from v
group by tipo, VendorID, flex_fare
order by tipo desc, VendorID, flex_fare;
