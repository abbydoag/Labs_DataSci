# Notas: 02_Consultas_Parquet.ipynb

## Objetivo

Que contienen los archivos Parquet de 2026 y que problemas de calidad tienen, si se
consultan directo con DuckDB sin importarlos antes a ninguna tabla?

## Datos usados

| Tabla o archivo | Fuente | Filas x columnas | Fecha de obtencion | Notas |
|---|---|---|---|---|
| `data/raw/yellow/2026/*.parquet` | NYC TLC, descargados por el cuaderno 01 | 29,703,355 x 21 | 2026-10-06 | `request_source` solo de junio a agosto |
| `data/raw/green/2026/*.parquet` | NYC TLC, descargados por el cuaderno 01 | 337,114 x 22 | 2026-10-06 | `ehail_fee` siempre nula |
| Diccionarios de datos yellow y green de la TLC | nyc.gov, version del 18 de marzo de 2025 | no aplica | 2026-10-06 | Codigos de VendorID, RatecodeID, payment_type y trip_type |

## Supuestos

- Las fechas sin zona horaria son hora local de Nueva York.
- Los codigos se interpretan con el diccionario de marzo de 2025, el mas reciente publicado.
  `request_source` y `ehail_fee` no aparecen en el.
- Las tarifas negativas son reversiones de un cobro (inferido de su tipo de pago y su
  valor tipico, no documentado por la TLC).

## Decisiones

- Leer siempre con `union_by_name = true` | sin la opcion DuckDB usa el esquema del primer
  archivo y `request_source` desaparece sin aviso | leer con el esquema por defecto.
- Muestra con `bernoulli` y semilla | `reservoir(5 rows)` devolvio solo filas de enero con
  tres semillas distintas | `reservoir` o `limit`.
- Una consulta por archivo en `sql/` y el cuaderno la imprime antes del resultado | la
  consulta documentada y la ejecutada son la misma | SQL escrito dentro del cuaderno.
- Medir tiempos con el menor de 3 corridas | la primera paga la lectura en frio del disco |
  una sola corrida.
- Magnitud de los problemas: marginal < 0.1%, moderado < 5%, grande >= 5% | decide si se
  filtra en todo el analisis o solo donde afecta | filtrar todo lo sospechoso.
- Tabla de decisiones de limpieza para el cuaderno 03: ver la seccion 8 del cuaderno.

## Hallazgos

- 16 archivos, 30,040,469 registros: 29,703,355 amarillos (98.9%) y 337,114 verdes.
- 21 columnas en amarillos, 22 en verdes, 18 nombres en comun. Ninguna cambia de tipo.
- Flex Fare (`payment_type` 0 en amarillos, nulo en verdes): 7,716,688 amarillos (25.98%) y
  48,775 verdes (14.47%), sin pasajeros, codigo de tarifa, store_and_fwd ni recargo.
- Proveedor 7: 100% de sus 367,120 viajes con duracion cero.
- Proveedor 1: 769,133 de los 769,693 codigos de tarifa 99 (14.1% de sus viajes).
- Proveedor 2: todas las tarifas negativas; en amarillos 100,849 en disputa, 35,068 en
  efectivo, 17,726 sin cargo, medianas de -12.80, -13.50 y -10.00.
- 244 viajes fuera del mes de su archivo (223 en un mes vecino, 21 con fechas de 2001,
  2008 o 2009).
- 7 duplicados exactos en amarillos, 0 en verdes.
- Costo de leer directo: contar unos 4 ms, una columna 40 a 50 ms, 21 columnas unos 0.6 s.

## Aprendido

- `parquet_schema`, `parquet_file_metadata` y `glob` responden leyendo solo pies o nombres
  de archivo.
- `union_by_name` no es opcional cuando la fuente cambia de esquema: el modo por defecto
  pierde columnas en silencio.
- `group by all` con `select *, count(*)` agrupa por todas las columnas; con solo el
  agregado en el select no agrupa por nada.
- Un "muestreo al azar" puede no serlo: hay que revisar como se reparte la muestra.
- `SUMMARIZE` da medianas y distintos aproximados, que cambian un poco entre corridas.
- El plan de `explain` muestra que columnas y filtros llegan a `READ_PARQUET`.

## Pendientes y dudas

- Significado de `request_source` (valores A, CC, HV0003, HV0005, EH0004, EH0010):
  no esta en el diccionario.
- Si las reversiones del proveedor 2 tienen un viaje original positivo que se cancela con
  ellas: sin identificador de viaje no se puede emparejar.

## Registro

- 2026-10-06: consultas de exploracion, perfil y calidad; cuaderno ejecutado en el
  contenedor `lab`.
