# Notas del cuaderno 05: Benchmark

## Datos usados
- Escenario 1: Solo 2026 (8 archivos, 29.7M filas)
- Escenario 2: 2024 + 2026 (24 archivos, 71M filas)
- Consultas: conteo_por_mes, distancia_mediana, pago_mas_usado, velocidad_por_hora
- Repeticiones: 5 por consulta, se reporta el mínimo

## Decisiones
- Se usó la misma vista/tabla para ambas estrategias
- Se midió el tiempo de carga de la tabla materializada
- Se reportó el menor tiempo de 5 repeticiones para eliminar efecto de cold start

## Hallazgos
- Tabla materializada es 16-20x más rápida en todas las consultas
- Tiempo de carga: 12.34s (29.7M filas), 28.56s (71M filas)
- La brecha se mantiene constante al aumentar el volumen

## Aprendido
- Parquet directo es mejor para exploración (pocas consultas, cambios frecuentes)
- Tabla materializada es mejor para tableros (consultas repetidas)
- El costo de materialización se amortiza con consultas repetidas
