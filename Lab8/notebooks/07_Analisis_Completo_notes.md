# Notas del cuaderno 07: Análisis Completo

## Datos usados
- 2024: 12 amarillos + 12 verdes = 24 archivos
- 2025: 12 amarillos + 12 verdes = 24 archivos
- 2026: 8 amarillos + 8 verdes = 16 archivos (enero-agosto)
- Total: 64 archivos, ~100M filas

## Decisiones
- Se actualizó download_data.py para soportar --anios 2024 2025 2026
- Las vistas existentes funcionan sin cambios gracias a glob patterns
- Se crearon consultas específicas para comparar los tres años

## Hallazgos
- Viajes crecieron +3.6% (amarillos) y +3.0% (verdes) de 2024 a 2025
- Ingreso promedio subió +1.3% y +1.6% respectivamente
- La brecha amarillos vs verdes se mantiene constante (13x volumen, 21% precio)

## Aprendido
- El diseño incremental permite agregar años sin tocar consultas
- Los patrones de largo plazo solo son visibles con múltiples años
- La segmentación del mercado (amarillos vs verdes) es estable
