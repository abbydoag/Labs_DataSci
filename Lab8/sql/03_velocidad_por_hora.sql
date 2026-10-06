-- 03_velocidad_por_hora.sql
-- Objetivo: velocidad, duracion y distancia medianas segun la hora de salida
-- (pregunta 3). La velocidad es la de todo el viaje: distancia del taximetro
-- entre el tiempo con el taximetro encendido.
-- Fuente: vista viajes_validos, solo viajes medibles.
select
    tipo,
    hora,
    count(*) as viajes,
    median(trip_distance / (duracion_min / 60)) as velocidad_mediana_mph,
    median(duracion_min) as duracion_mediana_min,
    median(trip_distance) as distancia_mediana_millas
from viajes_validos
where medible
group by tipo, hora
order by tipo desc, hora;
