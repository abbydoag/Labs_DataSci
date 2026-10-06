# Notas: 01_Ambiente_y_Descarga.ipynb

## Objetivo

El ambiente Docker levanta los servicios del laboratorio y el sistema de descarga obtiene
completos los viajes de taxis amarillos y verdes publicados para 2026?

## Datos usados

| Tabla o archivo | Fuente | Filas x columnas | Fecha de obtencion | Notas |
|---|---|---|---|---|
| `data/raw/yellow/2026/yellow_tripdata_2026-01..08.parquet` | NYC TLC Trip Record Data, `d37ci6vzurychx.cloudfront.net/trip-data` | 29,703,355 x 20 (21 desde junio) | 2026-10-06 | 8 archivos, 487.8 MiB. Septiembre a diciembre responden 403 |
| `data/raw/green/2026/green_tripdata_2026-01..08.parquet` | NYC TLC Trip Record Data | 337,114 x 21 (22 desde junio) | 2026-10-06 | 8 archivos, 7.9 MiB |
| `data/raw/zonas/taxi_zone_lookup.csv` | NYC TLC, `d37ci6vzurychx.cloudfront.net/misc` | 265 x 4 | 2026-10-06 | LocationID, Borough, Zone, service_zone |

## Supuestos

- El `Content-Length` que anuncia el servidor es el tamanio correcto del archivo publicado.
- Un 403 de CloudFront significa que el mes no esta publicado (es lo que devuelve para
  septiembre a diciembre de 2026, que todavia no existen).

## Decisiones

- Copiar el repositorio base sin cambios en un commit propio | el historial muestra que se
  cambio y sustituye al fork | trabajar sobre un fork aparte del repositorio del grupo.
- Rutas del script resueltas desde `__file__` | el script escribia en otra carpeta segun el
  directorio de trabajo | exigir que siempre se corra desde la raiz.
- Solo 403 y 404 cuentan como no publicado | un error de red no debe ocultar un mes |
  tratar cualquier fallo de la consulta HEAD como no publicado (original).
- Completo significa bytes en disco iguales al `Content-Length` | detecta descargas cortadas
  sin bajar nada | revisar solo que el archivo exista.
- El anio queda fijo en 2026 | generalizarlo es el ejercicio 5 del equipo | parametrizarlo ya.
- Figuras en `data/processed/figuras/` | esa carpeta ya esta fuera de Git y las figuras se
  regeneran | una carpeta nueva con su propia regla en `.gitignore`.

## Hallazgos

- 16 de 16 archivos publicados completos (100%), 495.7 MiB, 30,040,469 viajes.
- Los verdes son el 1.1% de los viajes de 2026.
- Agosto es el mes mas bajo de amarillos aun por dia: 107,636 viajes diarios contra 121,424
  en febrero y 131,962 en mayo.
- Desde junio de 2026 los archivos traen la columna nueva `request_source` y los escribe
  `parquet-cpp-arrow 21.0.0` (antes 16.1.0). Abril de amarillos esta escrito con 24.0.0,
  posible regeneracion posterior.
- La primera descarga completa tomo 26 segundos; la segunda corrida no toco ningun archivo.

## Aprendido

- `parquet_file_metadata` da filas, grupos de filas y tamanio de cada archivo leyendo solo
  el pie, sin recorrer los datos.
- Dentro de `docker compose` los servicios se llaman por su nombre (`metabase:3000`); desde
  fuera, por el puerto publicado en localhost.
- Para probar que algo no se volvio a descargar no basta con ver que el archivo existe: hay
  que comparar la marca de modificacion.

## Pendientes y dudas

- Si la TLC republica un mes, el script no lo baja de nuevo por su cuenta; `--verificar`
  lo detecta.

## Registro

- 2026-10-06: repositorio base copiado, script corregido y probado, primera descarga de 2026.
- 2026-10-06: cuaderno ejecutado dentro del contenedor `lab`.
