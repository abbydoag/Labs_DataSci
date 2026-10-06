-- 02_duplicados.sql
-- Objetivo: filas repetidas exactamente igual en todas sus columnas (3.6).
-- Fuente: data/raw/<tipo>/*/*.parquet, directo, un tipo a la vez porque sus
-- columnas no son las mismas. group by all agrupa por todas las columnas de
-- select *, asi que cada grupo con mas de una fila es un duplicado exacto.
select
    'yellow' as tipo,
    count(*) as grupos_repetidos,
    coalesce(sum(n), 0) as filas_en_grupos,
    coalesce(sum(n - 1), 0) as filas_sobrantes
from (
    select *, count(*) as n
    from read_parquet('data/raw/yellow/*/*.parquet', union_by_name = true)
    group by all
    having count(*) > 1
)
union all
select
    'green',
    count(*),
    coalesce(sum(n), 0),
    coalesce(sum(n - 1), 0)
from (
    select *, count(*) as n
    from read_parquet('data/raw/green/*/*.parquet', union_by_name = true)
    group by all
    having count(*) > 1
);
