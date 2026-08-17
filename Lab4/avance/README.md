# Avance del Laboratorio 4 (entrega del 13 de agosto)

Esta carpeta guarda la primera version del laboratorio, correspondiente a la
entrega de avance de los ejercicios 1 al 4.

- `Lab4_GeoEspacial.ipynb` — conexion al API, descarga, calculo de NDVI, NDWI y
  NDCI, y analisis temporal. Ejecutado, con sus salidas.
- `01_Conexion_y_Raster.ipynb` — primer esbozo de la conexion.

Se conserva tal cual, sin modificar, porque documenta el avance entregado en su
momento y forma parte del historial de contribuciones del grupo.

La entrega final vive en la carpeta de arriba (`Lab4/`) y cubre los ocho
ejercicios. Se rehizo sobre otra base por tres razones tecnicas que quedaron
documentadas en los cuadernos finales:

1. **Script de cianobacteria.** El avance calcula el NDCI directamente. La
   rubrica pide el indice calculado con el script publicado en
   custom-scripts.sentinel-hub.com, asi que la version final traduce a Python el
   script CyanoLakes Chlorophyll-a completo: mascara de agua, indice de
   vegetacion flotante, NDCI, polinomio de clorofila y rampa de color oficial.

2. **Mascara de agua.** El avance promedia el indice sobre todo el rectangulo
   descargado. Como la vegetacion refleja con fuerza en el borde rojo, la tierra
   alrededor del lago entra en el promedio. La version final restringe cada
   estadistica al espejo de agua.

3. **Producto L1C en vez de L2A.** Sobre agua muy clara la correccion
   atmosferica de L2A deja el rojo y el borde rojo casi en cero, el denominador
   del NDCI se anula y el indice sale de su rango teorico. El detalle, con la
   comparacion numerica, esta en `../01_Descarga_Datos.ipynb`.
