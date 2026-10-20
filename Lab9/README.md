# Lab 9: Visualización estática

Infografía de una página que sintetiza el Lab 1 (series de tiempo de la Base de
Migración 2009-2026, INGUAT/IGM) para un directivo no técnico. Este folder
contiene el código y los textos de los incisos 7, 8 y 9 (bloques 4 y 5).

## Cómo correr

```
~/.venvs/base-ds/bin/python Lab9/pronostico.py
```

Lee `Lab 1/df/Base_Migracion_2009-2026jun.csv` y genera
`Lab9/figuras/07_pronostico_intervalo.png` (2400x1200 px). Las figuras no se
versionan: el laboratorio pide no publicar la infografía abiertamente.

Salida esperada, igual a la del Lab 1:

```
Entrenamiento: 2009-01 a 2021-03 (147 meses)
Prueba: 2021-04 a 2026-06 (63 meses)
MAE=156,000  RMSE=170,738  RMSE/promedio=70.7%
Meses reales dentro del intervalo 95%: 100%
```

## Inciso 7: proyección del modelo ganador

El script reconstruye la serie total (turistas + excursionistas), la división
70/30 y el ARIMA(0,1,1) sobre log1p que ganó en el Lab 1 por menor RMSE. El
intervalo del 95% se calcula con `get_forecast().conf_int()` en escala log y se
regresa a viajeros.

Hallazgo: el modelo se entrenó hasta marzo de 2021, en plena pandemia, y
proyecta un nivel plano de 88,319 viajeros al mes. La serie real se recuperó a
200-400 mil. El intervalo crece de forma exponencial al volver de la escala log
y llega a 20.6 millones en junio de 2026, por eso el eje se corta en 600 mil y
el corte se rotula en la figura en lugar de ocultarlo.

## Inciso 8: recomendaciones para INGUAT

1. **Preparar diciembre desde antes.** Diciembre recibe 37% más visitantes que
   un mes promedio y el patrón sobrevivió a la pandemia (fuerza estacional 0.80
   antes de 2020 y 0.52 después). Reforzar promoción, personal fronterizo y
   capacidad aeroportuaria antes del pico de fin de año, y usar febrero y
   septiembre (14% a 16% bajo el promedio) para campañas de temporada baja.
2. **La frontera terrestre es la puerta principal.** El 64.5% de los visitantes
   de 2025 entró por tierra. Valle Nuevo, San Cristóbal y Pedro de Alvarado
   suman 43% de los ingresos, casi lo mismo que La Aurora (35.5%). Invertir en
   la experiencia en esos puestos: tiempos de espera, señalización e información
   turística.
3. **Recuperar al viajero centroamericano.** América del Centro es el mercado
   más grande y el que menos se recuperó: en 2025 sigue 34% bajo 2019, mientras
   América del Norte ya está 39% arriba y Europa 25% arriba. Dirigir esfuerzos
   de recuperación a la región sin descuidar los mercados que ya crecen.
4. **Planificar con rangos, no con una sola cifra.** El mejor modelo del
   laboratorio se equivocó en promedio por 156 mil viajeros al mes porque
   aprendió durante la pandemia y no previó la recuperación. Presupuestos y metas
   deben usar escenarios y el modelo debe reentrenarse con datos de 2022 a 2026.

Nota sobre estacionalidad: la fuerza estacional del Lab 1 sale débil (0.05)
cuando se mide sobre toda la serie, porque la caída de 2020 queda en el residuo
de la descomposición STL. Medida antes (2009-2019) y después (2022-2026) de la
pandemia es fuerte (0.80 y 0.52).

## Inciso 9: pie de infografía

**Fuente:** Base de Migración 2009-2026, Instituto Guatemalteco de Turismo
(INGUAT) e Instituto Guatemalteco de Migración (IGM). Datos compartidos con
fines estrictamente académicos.

**Ficha técnica:** ingresos mensuales de enero 2009 a junio 2026 (210 meses).
Se usan solo turistas y excursionistas para que la serie sea comparable en todo
el período (la definición de "viajero" cambió entre 2022 y 2023). Modelos
evaluados: ARIMA, Holt-Winters, suavizamiento exponencial y Prophet, con 70%
de los meses para entrenar y 30% para probar. Ganador por menor RMSE:
ARIMA(0,1,1). La estimación se muestra con intervalo de confianza del 95%.
Herramientas: Python (pandas, statsmodels, Prophet, matplotlib) y Canva.

**Autores:** [nombre completo de Abby], Hansel López, Fabian Prado. CC3084 Data
Science, Universidad del Valle de Guatemala, Semestre II 2026.

## Decisiones de diseño (incisos 7 a 9)

**Tipo de gráfico.** El pronóstico es una serie temporal continua, por eso se
usa una gráfica de líneas: el eje x es el tiempo y la pendiente muestra la
dirección. Lo observado va en línea sólida y la estimación en línea discontinua,
una convención que distingue un dato medido de uno calculado sin depender del
color. El intervalo va como banda sombreada porque representa un rango de
valores posibles, no un valor. Se muestra desde 2018 para dar contexto antes de
la pandemia sin repetir la línea de tiempo completa del bloque 2.

**Honestidad de la escala.** El eje y empieza en cero. El intervalo supera los
20 millones, lo que aplastaría la serie real contra el eje, así que el eje se
corta en 600 mil (apenas sobre el máximo histórico de 449 mil) y el corte se
declara con texto en la figura. Se eligió esto sobre una escala logarítmica
porque un directivo lee mejor cantidades directas.

**Color.** Se sigue la paleta de la infografía: azul para lo observado y naranja
como acento para la estimación. Azul y naranja son complementarios en el círculo
cromático, así que el contraste entre lo real y lo estimado es máximo sin
agregar colores nuevos. El azul transmite estabilidad y sirve para el dato
confirmado; el naranja llama la atención sobre lo incierto. La historia de
entrenamiento va en gris azulado para que quede en segundo plano. Los tonos se
oscurecieron lo necesario para cumplir contraste WCAG sobre el fondo del lienzo
(4.5:1 en texto pequeño y 3:1 en líneas y texto grande en negrita).

**Etiquetas directas.** No hay leyenda: cada serie se rotula al final de su
línea ("Real", "Estimación") para que el lector no tenga que buscar a qué
corresponde cada color. El título dice la conclusión, no el método.

**Orden.** El bloque 4 va después de la estacionalidad y los mercados porque
primero se muestra qué pasó y luego qué se puede anticipar. Las recomendaciones
cierran la infografía porque son la acción que se deriva de todo lo anterior, y
el pie con la fuente va al final con el menor peso visual.
