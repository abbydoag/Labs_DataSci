-- 02_esquema.sql
-- Objetivo: columnas de cada tipo de taxi (3.3), su tipo fisico y logico dentro
-- del Parquet (3.4) y en cuantos archivos aparece cada una.
-- Fuente: parquet_schema() sobre data/raw/*/*/*.parquet; lee solo los pies.
-- tipos_distintos > 1 significaria que una columna cambia de tipo entre meses.
select
    split_part(file_name, '/', -3) as tipo,
    name as columna,
    min(type) as tipo_fisico,
    min(coalesce(logical_type, converted_type)) as tipo_logico,
    count(distinct type) as tipos_distintos,
    count(distinct file_name) as archivos,
    min(regexp_extract(file_name, '(\d{4}-\d{2})\.parquet$', 1)) as desde
from parquet_schema('data/raw/*/*/*.parquet')
where name <> 'schema'
group by tipo, columna
order by tipo desc, archivos desc, columna;
