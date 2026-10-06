# Notas: 03_Exploratorio.ipynb

## Objetivo

Como se comportan los viajes de taxi de enero a agosto de 2026 en el tiempo, en sus
caracteristicas, por tipo de taxi y por forma de pago, y que valores atipicos o
inconsistentes aparecen?

## Datos usados

| Tabla o archivo | Fuente | Filas x columnas | Fecha de obtencion | Notas |
|---|---|---|---|---|
| Vista `viajes_validos` (`sql/00_vistas.sql`) | Parquet de 2026 en `data/raw`, leidos en cada consulta | 29,877,234 x 31 | 2026-10-06 | 29,541,242 amarillos y 335,992 verdes; sin montos negativos ni viajes fuera del mes de su archivo |
| Vista `zonas` | `data/raw/zonas/taxi_zone_lookup.csv` (TLC) | 265 x 4 | 2026-10-06 | Barrio y zona de cada LocationID |

## Supuestos

- La hora de salida es hora local de Nueva York (las fechas no traen zona horaria).
- El barrio del viaje es el de la zona de salida.
- `tip_amount` solo registra propinas con tarjeta (diccionario de la TLC, marzo de 2025).
- La velocidad es el promedio del viaje completo: distancia del taximetro entre tiempo con
  el taximetro encendido.

## Decisiones

- Solo dos exclusiones globales en la vista (montos negativos y viajes fuera del mes de su
  archivo); el resto se filtra con `medible` donde afecta | conserva los conteos y no borra
  Flex Fare ni proveedores completos | una vista con todos los filtros juntos.
- Medianas y percentiles exactos en lugar de promedios | las colas llegan a 328,522 millas y
  7,053 dolares | promedios y desviaciones.
- Viajes por dia e indice con enero = 100 | meses de distinta duracion y volumenes 88 veces
  distintos entre tipos | conteos mensuales crudos.
- Mapa de calor con viajes promedio por hora (dividido entre las veces que aparece cada dia
  de la semana) | de enero a agosto hay dias de la semana que se repiten 35 veces y otros 34
  | conteos crudos por dia y hora.
- Composicion del total solo con viajes cuyo desglose cuadra | en 36.9% de los amarillos la
  suma de componentes no da el total | promediar todos los componentes de todos los viajes.
- Propina solo con tarjeta | el efectivo no la registra | propina promedio sobre todos.

## Hallazgos

- Viajes por dia: amarillos 118,867 (ene) a 131,482 (may, maximo) a 107,167 (ago), 18.5%
  menos que mayo; verdes 1,295 (ene) a 1,469 (abr) a 1,307 (ago).
- Hora mas fuerte: amarillos jueves 18:00 (10,000 viajes por hora), verdes jueves 17:00 (133).
  Fin de semana contra dia habil: amarillos -1.0%, verdes -24.0%.
- Viaje mediano: amarillos 1.93 millas, 14.1 min, 9.3 mph; verdes 2.15 millas, 13.4 min,
  10.0 mph.
- Amarillos a las 5:00: 16.0 mph, 3.71 millas, 13.6 min; a las 15:00: 7.9 mph, 1.73 millas,
  15.3 min.
- Salidas desde Manhattan: 86.6% amarillos, 58.3% verdes. East Harlem North y South: 39.1% de
  los verdes. JFK: 3.9% de los amarillos.
- Efectivo: verdes 18.3% a 20.7%, amarillos 7.9% a 9.8%. Flex Fare amarillos 21.0% a 30.3%.
- Propina con tarjeta: 91.1% de los amarillos, mediana 3.51 dolares (27.3% de la tarifa).
  Efectivo con propina: 182 viajes.
- Pico del total en 100 a 102 dolares: 83.3% tarifa fija de JFK (70 + 7.46 de peajes +
  16.44 de propina).
- Total distinto de la suma de componentes: 36.9% de los amarillos y 19.9% de los verdes;
  proveedor 2 normal cuadra en 99.87%; proveedor 1 difiere por una mediana de -3.25.
- Tukey sobre el total: 8.5% de los amarillos; al menos 39% de ellos con tarifa especial.

## Aprendido

- `quantile_cont` es exacto y necesita ordenar: es la consulta mas lenta del cuaderno.
- `unpivot` en DuckDB convierte varias columnas en filas para calcular lo mismo sobre
  todas con un solo `group by`.
- `qualify` filtra por una funcion de ventana (las 8 zonas principales) pero no se puede
  combinar con `group by all` en DuckDB 1.5.5.
- La regla de Tukey en distribuciones con colas largas marca viajes legitimos; antes de
  llamar "atipico" a algo hay que ver que es.
- Cuando dos series de una grafica se cruzan, etiquetar la de arriba encima y la de abajo
  debajo evita que los numeros se encimen.

## Pendientes y dudas

- Si la caida de julio y agosto es de temporada: se puede comparar con 2024 (ejercicio 5).
- `03_viajes_por_mes.sql` y `03_pago_por_mes.sql` agrupan por `mes` sin `anio`; al agregar
  2024 hay que sumar `anio` a la agrupacion.
- Que hace el proveedor 1 con el recargo de congestion y el cargo de la zona central (la
  diferencia de 3.25 dolares): no se puede saber con los datos.

## Registro

- 2026-10-06: vista `viajes_validos`, siete preguntas, quince consultas y cuaderno
  ejecutado en el contenedor `lab`.
