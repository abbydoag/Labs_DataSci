"""Descarga de las escenas Sentinel-2 con openEO (ejercicios 1 y 2).

Se conecta al backend openEO del Copernicus Data Space Ecosystem y baja, para
cada una de las 22 escenas oficiales, solo las bandas que necesitan el indice de
cianobacteria, el NDVI y el NDWI. No se descargan escenas completas.

Uso desde la terminal, con el entorno del laboratorio:

    .venv/bin/python -m src.descarga            # baja lo que falte
    .venv/bin/python -m src.descarga --estado   # solo reporta que hay

La autenticacion es un flujo de codigo de dispositivo: la primera vez imprime
una URL y un codigo que hay que confirmar en el navegador. openEO guarda un
token de refresco, asi que las corridas siguientes no piden nada.
"""

from __future__ import annotations

import argparse
import random
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import openeo

from .config import (
    AREAS,
    BANDAS,
    COLECCION,
    CRUDO,
    DATOS,
    FECHAS,
    RESOLUCION_M,
    URL_OPENEO,
    ruta_tif,
)


# Cuantas veces se reintenta una escena antes de darla por perdida, y cuantos
# segundos se espera tras el primer fallo (se duplica en cada intento).
REINTENTOS = 4
ESPERA_BASE = 20


def conectar() -> openeo.Connection:
    """Abre la conexion con el API de Sentinel-2 y autentica."""
    conexion = openeo.connect(URL_OPENEO)
    conexion.authenticate_oidc()
    return conexion


def _dia_siguiente(fecha: str) -> str:
    import datetime as dt

    return (dt.date.fromisoformat(fecha) + dt.timedelta(days=1)).isoformat()


def descargar_escena(conexion: openeo.Connection, lago: str, fecha: str) -> Path:
    """Baja una escena y la deja como un unico GeoTIFF multibanda."""
    destino = ruta_tif(lago, fecha)
    destino.parent.mkdir(parents=True, exist_ok=True)

    cubo = conexion.load_collection(
        COLECCION,
        spatial_extent=AREAS[lago],
        # openEO trata el extremo final como abierto, asi que se pide el dia
        # siguiente para quedarse con una sola fecha.
        temporal_extent=[fecha, _dia_siguiente(fecha)],
        bands=BANDAS,
    )

    # Todo a 20 m. Las bandas del borde rojo y del SWIR, que son las que
    # alimentan el indice de cianobacteria, ya son nativas de 20 m. Se usa
    # vecino mas cercano porque promediar mezclaria pixeles de tierra y de agua
    # en la orilla, y ademas SCL es una capa de clases donde promediar no tiene
    # sentido.
    cubo = cubo.resample_spatial(resolution=RESOLUCION_M, method="near")

    trabajo = conexion.create_job(
        cubo.save_result(format="GTiff"),
        title=f"Lab4 {lago} {fecha}",
    )
    trabajo.start_and_wait()

    temporal = destino.parent / f".tmp_{fecha}"
    if temporal.exists():
        shutil.rmtree(temporal)
    temporal.mkdir(parents=True)

    try:
        trabajo.get_results().download_files(temporal)
        tifs = sorted(temporal.glob("*.tif")) + sorted(temporal.glob("*.tiff"))
        if not tifs:
            raise RuntimeError(f"El trabajo no devolvio ningun GeoTIFF: {lago} {fecha}")
        if destino.exists():
            destino.unlink()
        shutil.move(str(tifs[0]), destino)
    finally:
        shutil.rmtree(temporal, ignore_errors=True)

    return destino


def pendientes() -> list[tuple[str, str]]:
    """Escenas oficiales que todavia no estan en disco."""
    faltan = []
    for lago, fechas in FECHAS.items():
        for fecha in fechas:
            if not ruta_tif(lago, fecha).exists():
                faltan.append((lago, fecha))
    return faltan


def estado() -> None:
    """Imprime cuantas escenas hay y cuales faltan."""
    total = sum(len(f) for f in FECHAS.values())
    faltan = pendientes()
    print(f"Escenas oficiales: {total}")
    print(f"Descargadas:       {total - len(faltan)}")
    if faltan:
        print(f"Pendientes:        {len(faltan)}")
        for lago, fecha in faltan:
            print(f"  - {lago} {fecha}")
    else:
        print("Pendientes:        0")
    for lago in FECHAS:
        patron = f"{lago.lower()}_*.tif"
        archivos = list(DATOS.glob(patron))
        if archivos:
            peso = sum(p.stat().st_size for p in archivos) / 1e6
            print(f"{lago}: {len(archivos)} archivos, {peso:.0f} MB")


def descargar_todo(trabajadores: int = 1) -> None:
    """Descarga lo que falte.

    Va de una escena a la vez porque la cuenta gratuita del Copernicus Data
    Space admite un solo trabajo por lotes simultaneo: al intentar con dos o
    tres, el backend responde `429 max connections reached: 1`. El parametro
    queda expuesto por si la cuenta llegara a permitir mas.

    Cada escena tarda alrededor de tres minutos, casi todo esperando a que el
    servidor procese el recorte, asi que las 22 toman cerca de una hora.
    """
    faltan = pendientes()
    if not faltan:
        print("Todas las escenas ya estan descargadas.")
        return

    print(f"Faltan {len(faltan)} escenas. Conectando a {URL_OPENEO} ...")
    conectar()  # valida credenciales antes de abrir hilos
    print(f"Autenticado. Descargando con {trabajadores} trabajos en paralelo.\n")

    hilo_local = threading.local()

    def conexion_del_hilo() -> openeo.Connection:
        # Cada hilo mantiene su propia conexion; el cliente de openEO no
        # promete ser seguro para uso concurrente.
        if not hasattr(hilo_local, "conexion"):
            hilo_local.conexion = conectar()
        return hilo_local.conexion

    def tarea(entrada: tuple[str, str]) -> tuple[str, str, str]:
        lago, fecha = entrada
        # El backend limita cuantas peticiones acepta por minuto y responde 429
        # cuando se pasa. Es una condicion pasajera, asi que se reintenta con
        # espera creciente en vez de dar la escena por perdida.
        for intento in range(REINTENTOS):
            try:
                ruta = descargar_escena(conexion_del_hilo(), lago, fecha)
                sufijo = f" (intento {intento + 1})" if intento else ""
                return lago, fecha, f"ok  {ruta.stat().st_size / 1e6:.1f} MB{sufijo}"
            except Exception as err:  # noqa: BLE001 - se reporta y se sigue
                if intento == REINTENTOS - 1:
                    return lago, fecha, f"FALLO: {err}"
                espera = ESPERA_BASE * 2**intento + random.uniform(0, 5)
                time.sleep(espera)
        return lago, fecha, "FALLO: se agotaron los reintentos"

    completadas = 0
    fallidas = []
    with ThreadPoolExecutor(max_workers=trabajadores) as pool:
        futuros = {pool.submit(tarea, e): e for e in faltan}
        for futuro in as_completed(futuros):
            lago, fecha, mensaje = futuro.result()
            completadas += 1
            print(f"[{completadas}/{len(faltan)}] {lago} {fecha}  {mensaje}", flush=True)
            if mensaje.startswith("FALLO"):
                fallidas.append((lago, fecha, mensaje))

    print()
    if fallidas:
        print(f"{len(fallidas)} escenas fallaron:")
        for lago, fecha, err in fallidas:
            print(f"  - {lago} {fecha}: {err}")
        sys.exit(1)
    print("Descarga completa.")


def login() -> None:
    """Solo autentica y deja el token guardado, sin descargar nada.

    Se corre una vez de forma interactiva. openEO imprime una URL y un codigo
    que hay que confirmar en el navegador con la cuenta de Copernicus.
    """
    conexion = conectar()
    print("\nAutenticacion lista. El token quedo guardado.")
    print(f"Backend: {conexion.root_url}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga las escenas del Laboratorio 4")
    parser.add_argument("--estado", action="store_true", help="solo reportar que hay en disco")
    parser.add_argument("--login", action="store_true", help="solo autenticar y guardar el token")
    args = parser.parse_args()

    if args.estado:
        estado()
    elif args.login:
        login()
    else:
        descargar_todo()


if __name__ == "__main__":
    main()
