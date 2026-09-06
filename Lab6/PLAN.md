# Laboratorio 6 — estado, reparto y plan de trabajo

Documento de coordinacion. Dice que hay hecho, quien hace que falta y en que
orden se commitea. Fecha de entrega del documento final: **domingo 6 de
septiembre de 2026, 23:59**.

---

## 1. Estado actual

| Ejercicio | Puntos | Estado | Donde | Quien |
|---|---|---|---|---|
| 1. Carga, comprension e integracion | — | Hecho | `Lab6.ipynb` | Abby |
| 2. Calidad, limpieza y preprocesamiento | 18 | Hecho, con huecos | `Lab6.ipynb` | Abby |
| 3. Analisis exploratorio | 18 | Hecho, con huecos | `Lab6.ipynb` | Abby |
| 4. Red bipartita autor-video | 10 | Hecho | `Lab6.ipynb` | Abby |
| 5. Proyecciones de la red | 8 | **Hecho** | `05_Proyecciones.ipynb` | Fabian |
| 6. Topologia y fragmentacion | 12 | **Hecho** | `06_Topologia.ipynb` | Fabian |
| 7. Comunidades | 10 | **Hecho** | `07_Comunidades.ipynb` | Fabian |
| 8. Nodos centrales y participantes puente | 7 | Pendiente | `08_Centralidad.ipynb` | Abby |
| 9. Analisis de contenido y sentimiento | 5 | Pendiente | `09_Sentimiento.ipynb` | Abby |
| 10. Interpretacion, limitaciones y conclusiones | 12 | Pendiente | `10_Conclusiones.ipynb` | Abby |
| Informe en PDF | — | Pendiente | `informe.py` → `Informe_Lab6.pdf` | Abby |
| README del laboratorio | — | Pendiente | `README.md` de la raiz | Abby |

Infraestructura ya lista y compartida (Fabian): entorno `.venv`,
`requirements.txt`, modulo `src/` y las cuatro tablas de `processed/`.

---

## 2. El corte

**Fabian:** ejercicios 5, 6 y 7 (30 puntos) y toda la infraestructura
reproducible. Terminado y subido.

**Abby:** ejercicios 8, 9 y 10 (24 puntos), el informe en PDF, el README y
cerrar los huecos de los ejercicios 2 y 3 que se listan abajo.

Los cuadernos estan separados por ejercicio a proposito: los `.ipynb` son JSON
y resolver un conflicto de merge en uno es horrible. Mientras cada quien toque
solo sus archivos no hay conflictos. `Lab6.ipynb` es de Abby y nadie mas lo
edita.

---

## 3. Que falta, en detalle

### 3.1 Huecos de los ejercicios 2 y 3 (van en `Lab6.ipynb`)

Son arreglos cortos sobre trabajo que ya esta hecho, pero valen puntos de la
rubrica que ahora mismo se estan dejando en la mesa.

1. **El bloque de "CONCLUSIONES LIMITADAS" del ejercicio 3.5 esta ilegible.**
   Tiene texto cortado y erratas ("se seleccinarpn por medio de consultas
   eppecificas", "Tamano reudccion muestra: se alcanza un taoal de 293 videos y
   49'6 anuthing", "Sesgo plat"). Es la respuesta a una pregunta obligatoria y
   asi como esta no se entiende. Hay que reescribirlo.

2. **Ejercicio 3.6, pregunta 2, no imprime su resultado.** Se calculan
   `longitud_por_grupo` y `conteo_por_grupo` y nunca se muestran ni se
   interpretan. Falta el `print` y la conclusion.

3. **Faltan hashtags y bigramas frecuentes** (ejercicio 3.1, los pide de forma
   explicita y son parte de los 6 puntos del inciso). Estan resueltos en
   `src/texto.py`: `extraer_hashtags`, `bigramas` y `contar`.

4. **Falta la nube de palabras.** `WordCloud` esta importado en la celda 2 y no
   se usa. El 3.4 la menciona como opcion valida.

5. **Valores atipicos en el 2.1.** El diagnostico cubre dimensiones, tipos,
   faltantes, duplicados y constantes, pero no atipicos. Hay material obvio:
   `view_count` va de 2 a 8,190,449 y un solo video concentra el 39.7 % de los
   comentarios.

6. **Consistencia de IDs, nombres y handles en el 2.1.** Verificar que ningun
   `channel_id` tenga dos `channel_name` y viceversa, y lo mismo con
   `author_channel_id` / `author_name` / `author_handle`. Resuelto en
   `src/datos.py` con `clave_nombre` y `normalizar_handle`. Dato util: los tres
   pares son consistentes al 100 %, y `owner_handle` coincide con
   `channel_handle` en los 293 registros.

7. **Tratamiento de emoji en el 2.6.** La limpieza actual los borra sin decirlo:
   `re.sub(r'[^\w\s]', ' ', texto)` los elimina porque un emoji no es `\w`. Hay
   que documentarlo como decision, sobre todo porque el ejercicio 9 los va a
   necesitar. `src/texto.py` los extrae a una columna aparte antes de limpiar.

8. **Lematizacion en el 2.6.** El enunciado pide evaluarla y documentarla.
   Basta con justificar por que se usa el stemmer Snowball en lugar de un
   lematizador (NLTK no trae lematizador de espanol y spaCy agregaria un modelo
   de cientos de megas al entorno).

9. **Ejercicio 4.5** pide explicar con precision que significa una arista sin
   sobreinterpretarla. Esta construida la red pero falta el parrafo. Hay una
   version larga en la cabecera de `src/redes.py` y en la seccion 5.3 de
   `05_Proyecciones.ipynb`.

### 3.2 Ejercicio 8 — Nodos centrales y participantes puente (7 pts)

- **8.1** Calcular grado, intermediacion, cercania, PageRank y vector propio.
  Justificar cual sirve para que. Ojo con la interpretacion: en una red
  bipartita el grado de un autor y el de un video no son comparables entre si.
- **8.2** Interpretar por separado autores y videos. Para autores, recurrencia
  (grado ponderado) y diversidad (grado). Para videos, alcance y capacidad de
  conectar audiencias.
- **8.3** Participantes recurrentes, autores puente y videos articuladores.
  Aqui hay un resultado servido: `nx.articulation_points` sobre la componente
  mayor. El ejercicio 6 ya mostro que la conectividad de nodos es **1**, o sea
  que existe al menos un nodo cuya eliminacion parte la red. Vale la pena medir
  cuanto se fragmenta al quitar cada uno de los 9 autores puente.

Insumos listos: `processed/nodos_bipartita.csv`, `processed/aristas_*.csv` y
`src/redes.py` (`construir_bipartita`, `proyeccion_autores`,
`proyeccion_videos`, `componente_mayor`, `resumen`, `disposicion`).

### 3.3 Ejercicio 9 — Contenido y sentimiento (5 pts)

- **9.1** Analisis de sentimiento con herramienta adecuada para espanol,
  justificando el metodo. Ya esta implementado en `src/sentimiento.py`: lexico
  de polaridad en espanol al estilo VADER, con negaciones, intensificadores,
  atenuadores, mayusculas, exclamaciones y emoji. La cabecera del modulo trae
  la justificacion escrita (por que no VADER en ingles, por que no un
  transformer). Falta **usarlo, validarlo y explicarlo**: revisar a mano una
  muestra de comentarios y reportar en cuantos acierta.
- **9.2** Comparar sentimiento por video, canal, tema o comunidad. El ejercicio
  7.5 ya deja calculado el sentimiento por comunidad y por canal; se puede
  partir de ahi y extenderlo.
- **9.3** Explicar los hallazgos.

Uso: `sen.agregar_sentimiento(df, "texto_original")` agrega `sentimiento`
(continuo, de -1 a 1) y `sentimiento_etiqueta` (positivo/neutro/negativo).
`sen.palabras_encontradas(texto)` sirve para auditar por que un comentario
recibio su puntaje.

### 3.4 Ejercicio 10 — Interpretacion, limitaciones y conclusiones (12 pts)

Es el ejercicio que mas pesa despues del 2 y el 3, y el que menos codigo
necesita. Las seis limitaciones que el enunciado exige discutir, con la
evidencia que ya esta calculada:

| Limitacion | Evidencia disponible |
|---|---|
| Cobertura de comentarios | 274 de 293 videos (93.5 %) no tienen comentarios recolectados |
| Seleccion por consultas | 21 `source_query`; Quorum aporta 11 de los 19 videos con comentarios |
| Fechas relativas | `published_text` es "hace 2 semanas"; `src/datos.dias_desde` lo aproxima y explica por que es aproximado |
| Conteos al momento de la recoleccion | `view_count` y `view_count_text` discrepan en 53 de 280 videos |
| Falta de relaciones explicitas entre autores | `reply_count` no identifica autores; no hay arista usuario-usuario posible |
| Concentracion en pocos videos | Un video concentra el 39.7 % de los comentarios y el 38.6 % de los autores |

- **10.3** Distinguir descripcion, asociacion e inferencia. El caso concreto
  esta en el 7.5: los canales institucionales tienen comentarios mas positivos
  y los medios criticos mas negativos, pero eso es **asociacion**, no causa.
- **10.4** Conclusiones que integren redes, contenido, sentimiento y
  limitaciones.

### 3.5 Informe en PDF

Seguir el patron de `Lab5/informe.py`: script que recalcula las cifras desde
los datos y arma el PDF con `reportlab`, de modo que el documento no se pueda
desincronizar. Se corre con `.venv/bin/python informe.py`.

### 3.6 README

Agregar la seccion del Lab6 al `README.md` de la raiz, siguiendo el formato de
los laboratorios 4 y 5: estructura de archivos, como armar el entorno, en que
orden se corren los cuadernos y dependencias.

---

## 4. Plan de commits

Hechos (Fabian):

```
chore: entorno propio para el Lab6 con las dependencias de analisis de redes
feat: modulo compartido de datos, texto, sentimiento y redes del Lab6
feat: proyecciones autor-autor y video-video de la red bipartita
feat: topologia, cohesion y fragmentacion de las tres redes
feat: comunidades con Louvain sobre la red bipartita
docs: plan del Lab6 y reparto del trabajo pendiente
```

Pendientes (Abby), en este orden:

```
fix: completar el diagnostico de calidad con atipicos y consistencia de identificadores
feat: hashtags, bigramas y nube de palabras del exploratorio
fix: reescribir las respuestas del inciso 3.5 y cerrar la tercera pregunta adicional
feat: centralidad y participantes puente de la red
feat: analisis de sentimiento en espanol de los comentarios
feat: interpretacion, limitaciones y conclusiones del laboratorio
feat: informe del Lab6 en PDF
docs: documentar el Lab6 en el README
```

---

## 5. Como correr

El entorno vive en `Lab6/.venv` y **no** se versiona. Para armarlo:

```bash
cd Lab6
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Los cuadernos importan de `src/`, asi que se corren con el directorio de
trabajo en `Lab6/`. Orden: `Lab6.ipynb` (ejercicios 1 a 4), despues `05`, `06`,
`07`, y luego los que faltan. Los cuadernos 05 a 07 son independientes entre
si: cada uno reconstruye los grafos desde `src/` y no depende del estado de
otro cuaderno.

Para ejecutar uno completo sin abrir Jupyter:

```bash
.venv/bin/python -m jupyter nbconvert --to notebook --execute --inplace 05_Proyecciones.ipynb
```

`figuras/` no se versiona, se regenera al correr los cuadernos.

---

## 6. Cifras de referencia

Para que las mismas cifras no salgan distintas en dos secciones del informe:

- 293 videos, 97 canales, 406 comentarios, 332 autores.
- Solo **19 videos** tienen comentarios. Los otros 274 no estan en la red.
- Red bipartita: 351 nodos, 343 aristas, densidad bipartita 0.0544, 10
  componentes, la mayor con 286 nodos (81.5 %).
- Proyeccion autor-autor: 332 nodos, 10,732 aristas. Proyeccion video-video:
  19 nodos, 11 aristas, 9 videos aislados.
- 323 de 332 autores (97.3 %) comentaron en un solo video. Solo **9** son
  puente.
- Louvain sobre la bipartita: 17 comunidades, modularidad 0.7774, frente a
  0.7716 de la particion trivial por video.
- Video dominante: "Que rico come tu diputado" (Quorum), 161 comentarios
  (39.7 %) y 128 autores (38.6 %).
- Quorum: 11 de los 19 videos con comentarios y 256 de los 406 comentarios.
