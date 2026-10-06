-- 03_zonas_principales.sql
-- Objetivo: las ocho zonas donde mas viajes empiezan, por tipo de taxi
-- (pregunta 4).
-- Fuente: vista viajes_validos unida con la vista zonas por PULocationID.
with conteo as (
    select v.tipo, z.Zone as zona, z.Borough as barrio, count(*) as viajes
    from viajes_validos v
    left join zonas z on v.PULocationID = z.LocationID
    group by v.tipo, zona, barrio
)
select
    tipo,
    zona,
    barrio,
    viajes,
    100.0 * viajes / sum(viajes) over (partition by tipo) as pct_del_tipo
from conteo
qualify row_number() over (partition by tipo order by viajes desc) <= 8
order by tipo desc, viajes desc;
