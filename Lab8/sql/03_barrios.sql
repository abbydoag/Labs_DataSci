-- 03_barrios.sql
-- Objetivo: en que barrio empiezan los viajes de cada tipo de taxi (pregunta 4).
-- Fuente: vista viajes_validos unida con la vista zonas (taxi_zone_lookup.csv)
-- por PULocationID. Las zonas 264 y 265 aparecen como Unknown y N/A.
select
    v.tipo,
    coalesce(z.Borough, 'sin zona') as barrio,
    count(*) as viajes,
    100.0 * count(*) / sum(count(*)) over (partition by v.tipo) as pct_del_tipo
from viajes_validos v
left join zonas z on v.PULocationID = z.LocationID
group by v.tipo, barrio
order by v.tipo desc, viajes desc;
