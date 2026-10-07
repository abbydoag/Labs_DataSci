-- 07_metodo_pago.sql
-- Objetivo: distribución de métodos de pago (Indicador 6).
-- Fuente: viajes_validos
with pagos as (
    select
        tipo,
        case when payment_type in (1, 2) then 'tarjeta'
             when payment_type in (3, 4) then 'efectivo'
             else 'otro' end as pago,
        count(*) as viajes
    from viajes_validos
    where medible
    group by tipo, pago
)
select
    tipo,
    pago,
    viajes,
    round(100.0 * viajes / sum(viajes) over (partition by tipo), 1) as porcentaje
from pagos
order by tipo, viajes desc;
