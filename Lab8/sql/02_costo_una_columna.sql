-- 02_costo_una_columna.sql
-- Objetivo: tiempo de un calculo que necesita una sola columna (3.9). Solo se
-- lee fare_amount; las otras 20 columnas no salen del disco.
-- Fuente: data/raw/yellow/*/*.parquet, directo.
select max(fare_amount) as tarifa_maxima
from read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true);
