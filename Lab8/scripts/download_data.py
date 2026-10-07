#!/usr/bin/env python3
"""Descarga los archivos Parquet del NYC TLC Trip Record Data.

Soporta multiples anios (2024, 2025 y 2026). Cada archivo existente se omite;
solo se descargan los que faltan.

Fuente oficial de los datos:
    https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

Uso:
    python scripts/download_data.py                    # anios por defecto (2024, 2025, 2026)
    python scripts/download_data.py --anios 2024       # solo 2024
    python scripts/download_data.py --anios 2024 2025  # 2024 y 2025
    python scripts/download_data.py --taxi yellow
    python scripts/download_data.py --taxi green
    python scripts/download_data.py --verificar        # solo revisa, no descarga

Los archivos se guardan en:
    data/raw/<tipo>/<anio>/<nombre-original>.parquet
    data/raw/zonas/taxi_zone_lookup.csv

Comportamiento:
  - La TLC publica cada mes con varias semanas de atraso, por lo que no todos
    los meses existen todavia. El script consulta al servidor que meses estan
    publicados en lugar de suponerlos.
  - Un archivo que ya existe localmente no se vuelve a descargar.
  - La descarga se hace sobre un nombre temporal y solo se renombra al
    terminar, de modo que una interrupcion no deja archivos .parquet a medias.
  - El tamanio descargado se compara con el que anuncia el servidor.
  - Un error de red cuenta como fallo, no como mes no publicado.
  - Las rutas no dependen del directorio desde donde se corre el script.
"""

import argparse
import sys
from pathlib import Path

import requests

ANIOS = (2024, 2025, 2026)
TIPOS_TAXI = ("yellow", "green")
URL_BASE = "https://d37ci6vzurychx.cloudfront.net/trip-data"

# La ruta se resuelve desde este archivo y no desde el directorio de trabajo.
# Con Path("data/raw") el script escribia en notebooks/data/raw si se corria
# desde la carpeta de cuadernos.
RAIZ = Path(__file__).resolve().parent.parent
DIR_DESTINO = RAIZ / "data" / "raw"

# Tabla de zonas de la TLC: traduce PULocationID y DOLocationID a barrio y zona.
URL_ZONAS = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
RUTA_ZONAS = DIR_DESTINO / "zonas" / "taxi_zone_lookup.csv"

# Codigos con los que el servidor responde a un archivo que no existe.
NO_PUBLICADO = (403, 404)

TIEMPO_ESPERA = 60          # segundos por peticion
INTENTOS = 3                # intentos por archivo antes de darse por vencido
BLOQUE = 1024 * 1024        # 1 MiB por bloque de descarga
SUFIJO_TEMPORAL = ".part"


def construir_nombre(tipo: str, anio: int, mes: int) -> str:
    """Nombre del archivo publicado por la TLC, p. ej. yellow_tripdata_2026-01.parquet."""
    return f"{tipo}_tripdata_{anio}-{mes:02d}.parquet"


def construir_url(tipo: str, anio: int, mes: int) -> str:
    """URL completa del archivo Parquet mensual."""
    return f"{URL_BASE}/{construir_nombre(tipo, anio, mes)}"


def ruta_destino(tipo: str, anio: int, mes: int) -> Path:
    """Ruta local donde se guarda el archivo."""
    return DIR_DESTINO / tipo / str(anio) / construir_nombre(tipo, anio, mes)


def tamanio_publicado(url: str) -> int | None:
    """Tamanio en bytes del archivo en el servidor, o None si no esta publicado.

    Antes un error de red se reportaba como "no publicado", y un mes que si
    existe podia quedar fuera sin que nadie lo notara. Ahora solo 403 y 404
    cuentan como no publicado; cualquier otro problema lanza la excepcion.
    """
    respuesta = requests.head(url, timeout=TIEMPO_ESPERA, allow_redirects=True)
    if respuesta.status_code in NO_PUBLICADO:
        return None
    respuesta.raise_for_status()
    return int(respuesta.headers.get("Content-Length", 0))


def formato_tamanio(n: float) -> str:
    for unidad in ("B", "KiB", "MiB", "GiB"):
        if n < 1024 or unidad == "GiB":
            return f"{n:.1f} {unidad}"
        n /= 1024
    return f"{n:.1f} GiB"


def descargar_archivo(url: str, destino: Path, esperado: int = 0) -> int:
    """Descarga `url` en `destino`. Devuelve la cantidad de bytes escritos.

    Si se conoce el tamanio publicado (`esperado`), un archivo que llega con
    otro tamanio se trata como descarga fallida y se reintenta.
    """
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_name(destino.name + SUFIJO_TEMPORAL)

    ultimo_error = None
    for intento in range(1, INTENTOS + 1):
        try:
            with requests.get(url, stream=True, timeout=TIEMPO_ESPERA) as respuesta:
                respuesta.raise_for_status()
                escritos = 0
                with temporal.open("wb") as archivo:
                    for bloque in respuesta.iter_content(chunk_size=BLOQUE):
                        if bloque:
                            archivo.write(bloque)
                            escritos += len(bloque)
            if escritos == 0:
                raise requests.RequestException("el servidor devolvio un archivo vacio")
            if esperado and escritos != esperado:
                raise requests.RequestException(
                    f"se recibieron {escritos} bytes y el servidor anuncia {esperado}"
                )
            temporal.replace(destino)
            return escritos
        except requests.RequestException as error:
            ultimo_error = error
            temporal.unlink(missing_ok=True)
            if intento < INTENTOS:
                print(f"      intento {intento}/{INTENTOS} fallido ({error}); reintentando")

    raise requests.RequestException(f"no se pudo descargar {url}: {ultimo_error}")


def descargar(tipo: str, anio: int) -> dict:
    """Descarga todos los meses publicados de un tipo de taxi para un anio."""
    print(f"\n=== {tipo.upper()} {anio} ===")
    resumen = {"descargados": 0, "omitidos": 0, "no_publicados": [], "fallidos": []}

    for mes in range(1, 13):
        etiqueta = f"{anio}-{mes:02d}"
        destino = ruta_destino(tipo, anio, mes)

        if destino.exists() and destino.stat().st_size > 0:
            print(f"  {etiqueta}  ya existe, se omite")
            resumen["omitidos"] += 1
            continue

        url = construir_url(tipo, anio, mes)
        try:
            esperado = tamanio_publicado(url)
        except requests.RequestException as error:
            print(f"  {etiqueta}  ERROR al consultar el servidor: {error}")
            resumen["fallidos"].append(etiqueta)
            continue
        if esperado is None:
            print(f"  {etiqueta}  aun no publicado por la TLC")
            resumen["no_publicados"].append(etiqueta)
            continue

        print(f"  {etiqueta}  descargando...")
        try:
            escritos = descargar_archivo(url, destino, esperado)
        except requests.RequestException as error:
            print(f"  {etiqueta}  ERROR: {error}")
            resumen["fallidos"].append(etiqueta)
        else:
            print(f"  {etiqueta}  listo ({formato_tamanio(escritos)}) -> {destino}")
            resumen["descargados"] += 1

    return resumen


def descargar_zonas() -> str:
    """Descarga la tabla de zonas de la TLC si no existe. Devuelve lo que hizo."""
    if RUTA_ZONAS.exists() and RUTA_ZONAS.stat().st_size > 0:
        return "ya existe, se omite"
    escritos = descargar_archivo(URL_ZONAS, RUTA_ZONAS, tamanio_publicado(URL_ZONAS) or 0)
    return f"lista ({formato_tamanio(escritos)}) -> {RUTA_ZONAS}"


def verificar(tipo: str, anio: int) -> list[dict]:
    """Compara, mes a mes, lo que publica la TLC con lo que hay en disco.

    Estados:
      completo      el archivo local pesa exactamente lo que anuncia el servidor
      incompleto    existe localmente pero con otro tamanio
      falta         esta publicado y no esta en disco
      no publicado  la TLC todavia no lo publica
    """
    filas = []
    for mes in range(1, 13):
        destino = ruta_destino(tipo, anio, mes)
        local = destino.stat().st_size if destino.exists() else 0
        remoto = tamanio_publicado(construir_url(tipo, anio, mes))
        if remoto is None:
            estado = "no publicado"
        elif local == 0:
            estado = "falta"
        elif local == remoto:
            estado = "completo"
        else:
            estado = "incompleto"
        filas.append({
            "tipo": tipo, "anio": anio, "mes": mes, "archivo": destino.name,
            "bytes_servidor": remoto or 0, "bytes_local": local, "estado": estado,
        })
    return filas


def imprimir_verificacion(tipos: tuple, anios: tuple) -> int:
    """Imprime la verificacion y devuelve 1 si falta algun mes publicado."""
    pendientes = 0
    print(f"{'archivo':<34} {'servidor':>12} {'local':>12}  estado")
    for anio in anios:
        for tipo in tipos:
            for fila in verificar(tipo, anio):
                print(f"{fila['archivo']:<34} {fila['bytes_servidor']:>12,} "
                      f"{fila['bytes_local']:>12,}  {fila['estado']}")
                if fila["estado"] in ("falta", "incompleto"):
                    pendientes += 1
    print(f"\nmeses publicados sin archivo completo en disco: {pendientes}")
    return 1 if pendientes else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Descarga los datos de taxis del NYC TLC."
    )
    parser.add_argument(
        "--taxi", choices=(*TIPOS_TAXI, "all"), default="all",
        help="tipo de taxi a descargar (por defecto: all)",
    )
    parser.add_argument(
        "--anios", type=int, nargs="+", default=list(ANIOS),
        help="anios a descargar (por defecto: 2024 2025 2026)",
    )
    parser.add_argument(
        "--verificar", action="store_true",
        help="no descarga nada; compara lo publicado con lo que hay en disco",
    )
    argumentos = parser.parse_args()

    tipos = TIPOS_TAXI if argumentos.taxi == "all" else (argumentos.taxi,)
    anios = tuple(argumentos.anios)

    if argumentos.verificar:
        return imprimir_verificacion(tipos, anios)

    total = {"descargados": 0, "omitidos": 0, "no_publicados": [], "fallidos": []}
    for anio in anios:
        for tipo in tipos:
            resumen = descargar(tipo, anio)
            total["descargados"] += resumen["descargados"]
            total["omitidos"] += resumen["omitidos"]
            total["no_publicados"] += [f"{tipo} {anio}-{m:02d}" for m in range(1, 13)
                                       if f"{tipo} {anio}-{m:02d}" in resumen["no_publicados"]]
            total["fallidos"] += [f"{tipo} {anio}-{m:02d}" for m in range(1, 13)
                                  if f"{tipo} {anio}-{m:02d}" in resumen["fallidos"]]

    try:
        print(f"\nTabla de zonas: {descargar_zonas()}")
    except requests.RequestException as error:
        print(f"\nTabla de zonas: ERROR {error}")
        total["fallidos"].append("zonas")

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"  descargados   : {total['descargados']}")
    print(f"  ya existian   : {total['omitidos']}")
    print(f"  no publicados : {len(total['no_publicados'])}")
    if total["no_publicados"]:
        print(f"      {', '.join(total['no_publicados'])}")
    print(f"  fallidos      : {len(total['fallidos'])}")
    if total["fallidos"]:
        print(f"      {', '.join(total['fallidos'])}")
    print("=" * 60)

    return 1 if total["fallidos"] else 0


if __name__ == "__main__":
    sys.exit(main())
