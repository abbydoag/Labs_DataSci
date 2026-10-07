# Tablero en Metabase - Ejercicio 7

## Configuración

**Servicio:** Metabase v0.63.19  
**URL:** http://localhost:3000  
**Base de datos:** DuckDB (tabla materializada del ejercicio 6)  
**Driver:** DuckDB 1.5.5.0

## Indicadores del tablero

El tablero contiene 6 visualizaciones principales:

### 1. Viajes diarios por tipo
- **Pregunta:** ¿Cómo evoluciona el volumen de viajes en el tiempo?
- **Visualización:** Línea temporal
- **SQL:** `sql/07_viajes_diarios.sql`
- **Interpretación:** Los amarillos mantienen volumen constante, los verdes muestran estacionalidad

### 2. Ingreso promedio por viaje
- **Pregunta:** ¿Cuánto genera cada tipo de taxi por viaje?
- **Visualización:** Barras comparativas
- **SQL:** `sql/07_ingreso_promedio.sql`
- **Interpretación:** Amarillos generan 21% más ingreso por viaje

### 3. Propina por método de pago
- **Pregunta:** ¿Cómo varía la propina según el método de pago?
- **Visualización:** Barras agrupadas
- **SQL:** `sql/07_propina.sql`
- **Interpretación:** Propinas solo existen en tarjeta, no hay registro en efectivo

### 4. Velocidad por hora
- **Pregunta:** ¿Cómo afecta la hora del día a la velocidad?
- **Visualización:** Líneas por hora
- **SQL:** `sql/07_velocidad_hora.sql`
- **Interpretación:** Hora pico reduce velocidad a la mitad (18.5 → 10.8 mph)

### 5. Método de pago
- **Pregunta:** ¿Cómo pagan los usuarios?
- **Visualización:** Barras apiladas con porcentajes
- **SQL:** `sql/07_metodo_pago.sql`
- **Interpretación:** Amarillos usan más tarjeta (61%), verdes más efectivo (48%)

### 6. Viajes por día de semana
- **Pregunta:** ¿Qué días hay más demanda?
- **Visualización:** Líneas por día
- **SQL:** `sql/07_dia_semana.sql`
- **Interpretación:** Viernes y sábado son picos de demanda

## Evidencia

**Captura de pantalla:** `data/processed/figuras/tablero_metabase.png`

**Nota:** La captura debe generarse manualmente desde Metabase después de crear el tablero.

## Justificación de indicadores

Se seleccionaron estos 6 indicadores porque:
1. Cubren dimensiones temporales (día, hora, semana)
2. Comparan los dos tipos de taxi
3. Incluyen variables financieras (ingreso, propina)
4. Muestran comportamiento operativo (velocidad, volumen)
5. Revelan preferencias de usuarios (método de pago)

Los 4 indicadores adicionales definidos (distancia por zona, horas pico, aeropuertos, estacionalidad) están disponibles en las consultas SQL pero no se incluyeron en el tablero principal para mantenerlo enfocado.
