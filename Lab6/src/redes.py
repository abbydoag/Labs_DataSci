"""Construccion de la red bipartita autor-video y de sus dos proyecciones.

Que representa cada objeto, dicho una sola vez y para todo el laboratorio:

- La red bipartita tiene dos clases de nodo, autores y videos, y una arista
  autor-video existe cuando ese autor publico al menos un comentario en ese
  video. El peso es cuantos comentarios publico ahi.
- La proyeccion autor-autor une a dos autores que comentaron el mismo video, y
  pesa cuantos videos comparten.
- La proyeccion video-video une a dos videos que comparten al menos un autor, y
  pesa cuantos autores comparten.

Lo que ninguna de las tres representa: conversacion. `reply_count` dice cuantas
respuestas recibio un comentario pero no quien las escribio, asi que el
conjunto no permite trazar una arista de un usuario a otro. Una arista aqui es
coincidencia de espacio, no interaccion.

Los identificadores de nodo llevan prefijo (`a:` para autor, `v:` para video)
para que un `author_channel_id` y un `video_id` no puedan chocar en el grafo.
El identificador original viaja como atributo del nodo.
"""

from __future__ import annotations

import itertools
from collections import Counter

import networkx as nx
import pandas as pd

AUTOR = "autor"
VIDEO = "video"


def clave_autor(identificador: str) -> str:
    return f"a:{identificador}"


def clave_video(identificador: str) -> str:
    return f"v:{identificador}"


# --------------------------------------------------------------------------
# Red bipartita
# --------------------------------------------------------------------------


def construir_bipartita(
    comentarios: pd.DataFrame,
    videos: pd.DataFrame | None = None,
) -> nx.Graph:
    """Arma la red bipartita no dirigida autor-video.

    `comentarios` debe traer `author_channel_id`, `video_id` y las columnas
    descriptivas que se usan como atributos. `videos` es opcional y sirve para
    colgar del nodo video los atributos que solo estan en el otro archivo
    (categoria, vistas, fecha).
    """
    G = nx.Graph()

    info_video = {}
    if videos is not None:
        indexado = videos.set_index("video_id")
        info_video = indexado.to_dict("index")

    for _, fila in comentarios.iterrows():
        autor = clave_autor(fila["author_channel_id"])
        video = clave_video(fila["video_id"])

        if autor not in G:
            G.add_node(
                autor,
                tipo=AUTOR,
                bipartite=0,
                id_original=fila["author_channel_id"],
                etiqueta=fila.get("author_name", ""),
                handle=fila.get("author_handle", ""),
            )
        if video not in G:
            datos = info_video.get(fila["video_id"], {})
            G.add_node(
                video,
                tipo=VIDEO,
                bipartite=1,
                id_original=fila["video_id"],
                etiqueta=fila.get("video_title", ""),
                canal=fila.get("channel_name", ""),
                canal_id=fila.get("channel_id", ""),
                categoria=datos.get("category", ""),
                vistas=float(datos.get("vistas", 0) or 0),
                consulta=datos.get("source_query", ""),
                grupo_fuente=datos.get("source_group", ""),
            )

        if G.has_edge(autor, video):
            G[autor][video]["weight"] += 1
        else:
            G.add_edge(autor, video, weight=1)

    return G


def nodos_por_tipo(G: nx.Graph, tipo: str) -> list[str]:
    return [n for n, d in G.nodes(data=True) if d.get("tipo") == tipo]


def tabla_nodos(G: nx.Graph, comentarios: pd.DataFrame) -> pd.DataFrame:
    """Tabla de nodos de la red bipartita, la que pide el ejercicio 4.3.

    Trae el tipo de nodo, el identificador original, una etiqueta legible y los
    atributos que tienen sentido para cada clase. Las columnas que no aplican a
    un tipo quedan vacias, que es lo normal en una tabla de nodos bipartita.
    """
    por_autor = comentarios.groupby("author_channel_id")
    me_gusta_autor = por_autor["me_gusta"].sum()
    respuestas_autor = por_autor["respuestas"].sum()

    por_video = comentarios.groupby("video_id")
    me_gusta_video = por_video["me_gusta"].sum()
    respuestas_video = por_video["respuestas"].sum()

    filas = []
    for nodo, datos in G.nodes(data=True):
        grado = G.degree(nodo)
        peso = G.degree(nodo, weight="weight")
        original = datos["id_original"]
        fila = {
            "nodo_id": nodo,
            "tipo": datos["tipo"],
            "id_original": original,
            "etiqueta": datos.get("etiqueta", ""),
            "grado": grado,
            "grado_ponderado": peso,
        }
        if datos["tipo"] == AUTOR:
            fila.update(
                {
                    "handle": datos.get("handle", ""),
                    "canal": "",
                    "categoria": "",
                    "vistas": pd.NA,
                    "me_gusta": float(me_gusta_autor.get(original, 0)),
                    "respuestas": float(respuestas_autor.get(original, 0)),
                }
            )
        else:
            fila.update(
                {
                    "handle": "",
                    "canal": datos.get("canal", ""),
                    "categoria": datos.get("categoria", ""),
                    "vistas": datos.get("vistas", pd.NA),
                    "me_gusta": float(me_gusta_video.get(original, 0)),
                    "respuestas": float(respuestas_video.get(original, 0)),
                }
            )
        filas.append(fila)

    tabla = pd.DataFrame(filas)
    return tabla.sort_values(["tipo", "grado_ponderado"], ascending=[True, False])


def tabla_aristas(G: nx.Graph) -> pd.DataFrame:
    """Tabla de aristas de la red bipartita: autor, video y peso."""
    filas = []
    for u, v, datos in G.edges(data=True):
        autor, video = (u, v) if G.nodes[u]["tipo"] == AUTOR else (v, u)
        filas.append(
            {
                "origen": autor,
                "destino": video,
                "autor_id": G.nodes[autor]["id_original"],
                "video_id": G.nodes[video]["id_original"],
                "autor": G.nodes[autor].get("etiqueta", ""),
                "video": G.nodes[video].get("etiqueta", ""),
                "canal": G.nodes[video].get("canal", ""),
                "peso": datos["weight"],
                "tipo_arista": "autor-video",
            }
        )
    return pd.DataFrame(filas).sort_values("peso", ascending=False)


# --------------------------------------------------------------------------
# Proyecciones
# --------------------------------------------------------------------------


def proyectar(G: nx.Graph, tipo: str) -> nx.Graph:
    """Proyecta la bipartita sobre uno de sus dos conjuntos.

    No se usa `nx.bipartite.weighted_projected_graph` porque su peso es la
    similitud normalizada, y el enunciado pide el conteo crudo: numero de
    videos compartidos entre dos autores, numero de autores compartidos entre
    dos videos. Se cuenta a mano para que el peso signifique exactamente eso.
    """
    lado = nodos_por_tipo(G, tipo)
    P = nx.Graph()
    for nodo in lado:
        P.add_node(nodo, **G.nodes[nodo])

    compartidos: Counter = Counter()
    otro = VIDEO if tipo == AUTOR else AUTOR
    for puente in nodos_por_tipo(G, otro):
        vecinos = sorted(G.neighbors(puente))
        for a, b in itertools.combinations(vecinos, 2):
            compartidos[(a, b)] += 1

    for (a, b), peso in compartidos.items():
        P.add_edge(a, b, weight=peso)

    return P


def proyeccion_autores(G: nx.Graph) -> nx.Graph:
    """Dos autores se conectan si comentaron en el mismo video."""
    return proyectar(G, AUTOR)


def proyeccion_videos(G: nx.Graph) -> nx.Graph:
    """Dos videos se conectan si comparten al menos un autor."""
    return proyectar(G, VIDEO)


def tabla_aristas_proyeccion(P: nx.Graph, etiqueta: str) -> pd.DataFrame:
    filas = []
    for u, v, datos in P.edges(data=True):
        filas.append(
            {
                "origen": u,
                "destino": v,
                "origen_id": P.nodes[u]["id_original"],
                "destino_id": P.nodes[v]["id_original"],
                "origen_etiqueta": P.nodes[u].get("etiqueta", ""),
                "destino_etiqueta": P.nodes[v].get("etiqueta", ""),
                "peso": datos["weight"],
                "tipo_arista": etiqueta,
            }
        )
    if not filas:
        return pd.DataFrame(
            columns=[
                "origen",
                "destino",
                "origen_id",
                "destino_id",
                "origen_etiqueta",
                "destino_etiqueta",
                "peso",
                "tipo_arista",
            ]
        )
    return pd.DataFrame(filas).sort_values("peso", ascending=False)


# --------------------------------------------------------------------------
# Metricas
# --------------------------------------------------------------------------


def resumen(G: nx.Graph, bipartita: bool = False) -> dict[str, float]:
    """Metricas basicas de una red, en un diccionario listo para tabular.

    La densidad de una red bipartita no se calcula igual que la de una red
    normal: el maximo de aristas posibles no es n(n-1)/2 sino el producto de
    los tamanos de los dos conjuntos. `bipartita=True` usa la formula correcta,
    porque la otra subestima la densidad y hace parecer vacia una red que no lo
    esta.
    """
    n = G.number_of_nodes()
    m = G.number_of_edges()
    componentes = list(nx.connected_components(G))
    mayor = max((len(c) for c in componentes), default=0)

    if bipartita:
        autores = nodos_por_tipo(G, AUTOR)
        densidad = nx.bipartite.density(G, autores) if autores else 0.0
    else:
        densidad = nx.density(G)

    grados = [d for _, d in G.degree()]
    return {
        "nodos": n,
        "aristas": m,
        "densidad": densidad,
        "grado_medio": (sum(grados) / n) if n else 0.0,
        "grado_max": max(grados, default=0),
        "aislados": sum(1 for d in grados if d == 0),
        "componentes": len(componentes),
        "componente_mayor": mayor,
        "componente_mayor_prop": (mayor / n) if n else 0.0,
        "transitividad": nx.transitivity(G) if n else 0.0,
        "agrupamiento_medio": nx.average_clustering(G) if n else 0.0,
    }


def componente_mayor(G: nx.Graph) -> nx.Graph:
    if G.number_of_nodes() == 0:
        return G
    mayor = max(nx.connected_components(G), key=len)
    return G.subgraph(mayor).copy()


def distribucion_grados(G: nx.Graph, ponderado: bool = False) -> pd.DataFrame:
    """Distribucion de grados en formato tabla, lista para graficar."""
    peso = "weight" if ponderado else None
    grados = pd.Series([d for _, d in G.degree(weight=peso)])
    tabla = grados.value_counts().sort_index().rename("nodos").reset_index()
    tabla.columns = ["grado", "nodos"]
    tabla["proporcion"] = tabla["nodos"] / tabla["nodos"].sum()
    return tabla


def disposicion(G: nx.Graph, semilla: int = 42, k: float | None = None) -> dict:
    """Posiciones de los nodos con semilla fija.

    Todas las figuras de red del laboratorio usan esta funcion para que un
    mismo nodo caiga en el mismo lugar en todos los cuadernos y las figuras se
    puedan comparar entre secciones.
    """
    return nx.spring_layout(G, seed=semilla, k=k, weight="weight")
