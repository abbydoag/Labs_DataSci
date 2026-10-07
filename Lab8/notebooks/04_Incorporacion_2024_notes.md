# Notas del cuaderno 04: Incorporación de 2024

## Datos usados
- Archivos de 2024: 12 amarillos + 12 verdes = 24 archivos
- Archivos de 2026: 8 amarillos + 8 verdes = 16 archivos (enero-agosto)
- Total: 40 archivos, ~71M filas

## Decisiones
- Se modificó `download_data.py` para aceptar `--anios 2024 2026` en lugar de solo 2026
- Las vistas existentes no requirieron cambios porque usan glob patterns
- Se crearon consultas específicas para comparar 2024 vs 2026 (04_*.sql)

## Hallazgos
- Los amarillos crecieron +3.6% en promedio (enero-agosto 2026 vs 2024)
- Los verdes cayeron -5.0% en el mismo periodo
- El diseño del sistema permite agregar 2025 sin tocar consultas

## Aprendido
- DuckDB puede consultar múltiples años simultáneamente sin configuración especial
- Los glob patterns en las vistas hacen el sistema incremental
- La separación de datos y análisis facilita la incorporación de nuevos años
