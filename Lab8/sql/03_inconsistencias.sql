-- 03_inconsistencias.sql
-- Objetivo: registros que contradicen una regla entre columnas (pregunta 7).
-- Fuente: vista viajes_validos. Reglas:
--   total distinto de la suma de componentes (mas de un centavo);
--   cargo de aeropuerto sin salir de JFK (zona 132) ni LaGuardia (138), que
--   segun el diccionario es el unico caso en que se cobra;
--   velocidad promedio mayor a 80 mph en un viaje medible;
--   propina registrada en un viaje pagado en efectivo, que el diccionario
--   dice que no se registra.
select
    tipo,
    count(*) as viajes,
    count_if(abs(total_amount - (fare_amount + extra + mta_tax + tip_amount + tolls_amount
        + improvement_surcharge + coalesce(congestion_surcharge, 0) + coalesce(Airport_fee, 0)
        + cbd_congestion_fee + coalesce(ehail_fee, 0))) > 0.01) as total_no_cuadra,
    count_if(Airport_fee > 0) as con_cargo_aeropuerto,
    count_if(Airport_fee > 0 and PULocationID not in (132, 138)) as cargo_aeropuerto_fuera,
    count_if(medible) as medibles,
    count_if(medible and trip_distance / (duracion_min / 60) > 80) as mas_de_80_mph,
    count_if(payment_type = 2) as en_efectivo,
    count_if(payment_type = 2 and tip_amount > 0) as efectivo_con_propina
from viajes_validos
group by tipo
order by tipo desc;
