-- 01_filas_por_archivo.sql
-- Objetivo: registros, tamanio y programa que escribio cada archivo
-- descargado, leyendo solo el pie de metadatos de cada Parquet.
-- Fuente: data/raw/*/*/*.parquet, directo, sin vistas.
-- Uso: verificacion de completitud (ejercicio 2.7). No recorre los datos, por
-- eso tarda milisegundos aunque los archivos sumen cientos de MB. Un archivo
-- truncado no tiene pie valido y la consulta fallaria al intentar leerlo.
select
    split_part(file_name, '/', -3) as tipo,
    cast(split_part(file_name, '/', -2) as integer) as anio,
    cast(regexp_extract(file_name, '-(\d{2})\.parquet$', 1) as integer) as mes,
    regexp_extract(file_name, '[^/]+$') as archivo,
    num_rows as filas,
    num_row_groups as grupos_de_filas,
    file_size_bytes as bytes,
    created_by as escrito_por
from parquet_file_metadata('data/raw/*/*/*.parquet')
order by tipo desc, anio, mes;
