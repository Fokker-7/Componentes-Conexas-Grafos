import random

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Componentes Conexas de un Grafo", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stElementToolbar"] { display: none; }
    [data-testid="stCheckbox"] { display: flex; justify-content: center; }
    [data-testid="stCheckbox"] label { justify-content: center; margin-right: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


def titulo(texto, nivel=1):
    nivel = max(1, min(nivel, 6))
    st.markdown(f"<h{nivel}>{texto}</h{nivel}>", unsafe_allow_html=True)


def nom(v):
    return chr(65 + v)


st.session_state.setdefault("edges", set())
st.session_state.setdefault("n_anterior", None)
st.session_state.setdefault("paso", 0)
st.session_state.setdefault("firma", None)

titulo("Componentes Conexas de un Grafo", 1)
st.markdown(
    "Define un grafo (aleatorio o manual), revisa su matriz de adyacencia y "
    "recorre paso a paso el algoritmo DFS que identifica sus componentes conexas."
)

# 1 Configuración
titulo("1. Configuración", 2)

col_cfg1, col_cfg2 = st.columns(2)
with col_cfg1:
    n = st.slider("Número de nodos (n)", min_value=4, max_value=12, value=6, step=1)
with col_cfg2:
    modo = st.radio("Modo de creación del grafo", ["Aleatorio", "Manual"], horizontal=True)

# al cambiar n se eliminan aristas de nodos que desaparecen
if st.session_state.n_anterior != n:
    st.session_state.edges = {
        (a, b) for (a, b) in st.session_state.edges if a < n and b < n
    }
    st.session_state.n_anterior = n

nodos = list(range(n))

# 2 Construcción del grafo
titulo("2. Construcción del grafo", 2)

if modo == "Aleatorio":
    probabilidad = st.slider(
        "Probabilidad de conexión entre cada par de nodos",
        min_value=0, max_value=100, value=50, step=5, format="%d%%",
    )
    if st.button("Generar Grafo Aleatorio"):
        p = probabilidad / 100.0
        st.session_state.edges = {
            (i, j) for i in range(n) for j in range(i + 1, n) if random.random() < p
        }

else:
    st.markdown(
        "Marca la casilla donde se cruzan los dos vértices que quieres unir. "
        "Como el grafo es no dirigido, solo se muestra la mitad superior de la "
        "matriz (unir C con F es lo mismo que unir F con C)."
    )

    def alternar_arista(i, j):
        if st.session_state[f"chk_{i}_{j}"]:
            st.session_state.edges.add((i, j))
        else:
            st.session_state.edges.discard((i, j))

    if st.button("Limpiar Conexiones"):
        st.session_state.edges = set()

    col_grid, col_lista = st.columns([3, 1])

    with col_grid:
        ANCHOS = [0.8] + [1] * n
        fila_enc = st.columns(ANCHOS)
        for j in range(n):
            fila_enc[j + 1].markdown(
                f"<div style='text-align:center'><b>{nom(j)}</b></div>",
                unsafe_allow_html=True,
            )
        for i in range(n):
            fila = st.columns(ANCHOS)
            fila[0].markdown(
                f"<div style='padding-top:6px'><b>{nom(i)}</b></div>",
                unsafe_allow_html=True,
            )
            for j in range(n):
                if j > i:
                    clave = f"chk_{i}_{j}"
                    st.session_state[clave] = (i, j) in st.session_state.edges
                    fila[j + 1].checkbox(
                        f"{nom(i)} - {nom(j)}",
                        key=clave,
                        label_visibility="collapsed",
                        on_change=alternar_arista,
                        args=(i, j),
                    )
                else:
                    fila[j + 1].markdown(
                        "<div style='text-align:center;color:#666;padding-top:6px'>·</div>",
                        unsafe_allow_html=True,
                    )

    with col_lista:
        st.markdown("**Conexiones actuales**")
        if st.session_state.edges:
            for (a, b) in sorted(st.session_state.edges):
                st.markdown(f"- {nom(a)} — {nom(b)}")
        else:
            st.caption("Aún no hay conexiones.")

G = nx.Graph()
G.add_nodes_from(nodos)
G.add_edges_from(st.session_state.edges)

# 3 Matriz de adyacencia
titulo("3. Matriz de Adyacencia", 2)

matriz = np.zeros((n, n), dtype=int)
for (a, b) in st.session_state.edges:
    matriz[a][b] = 1
    matriz[b][a] = 1

etiquetas = [nom(i) for i in range(n)]
st.table(pd.DataFrame(matriz, index=etiquetas, columns=etiquetas))


def dfs_paso_a_paso(grafo, nodos):
    visitados = set()
    componentes = []
    pasos = []

    def snap(texto, actual=None, pila=(), comp_actual=()):
        pasos.append({
            "texto": texto,
            "actual": actual,
            "pila": list(pila),
            "visitados": set(visitados),
            "completas": [list(c) for c in componentes],
            "comp_actual": list(comp_actual),
        })

    snap("Inicio: ningún vértice ha sido visitado todavía.")

    for inicio in nodos:
        if inicio in visitados:
            continue

        comp = []
        pila = [inicio]
        snap(f"Iniciando desde vértice {nom(inicio)}: comienza una nueva componente "
             f"conexa. Se apila {nom(inicio)}.", inicio, pila, comp)

        while pila:
            actual = pila.pop()
            if actual in visitados:
                snap(f"{nom(actual)} ya fue visitado; se descarta de la pila.",
                     actual, pila, comp)
                continue

            visitados.add(actual)
            comp.append(actual)
            snap(f"Visitando vértice {nom(actual)}: se marca como visitado y se "
                 f"agrega a la componente actual.", actual, pila, comp)

            vecinos = sorted(grafo.neighbors(actual))
            if not vecinos:
                snap(f"{nom(actual)} no tiene vecinos (vértice aislado).",
                     actual, pila, comp)
            base = len(pila)
            for v in vecinos:
                if v not in visitados:
                    pila.insert(base, v)
                    snap(f"Vértice {nom(actual)} conecta con {nom(v)}: no visitado, "
                         f"se apila.", actual, pila, comp)
                else:
                    snap(f"Vértice {nom(actual)} conecta con {nom(v)}: ya visitado, "
                         f"se ignora.", actual, pila, comp)

        componentes.append(sorted(comp))
        nombres = ", ".join(nom(x) for x in sorted(comp))
        snap(f"Pila vacía: la componente {len(componentes)} está completa = "
             f"{{{nombres}}}.")

    snap(f"Fin del algoritmo: se encontraron {len(componentes)} componente(s) conexa(s).")
    return componentes, pasos


componentes, pasos = dfs_paso_a_paso(G, nodos)

firma = (n, frozenset(st.session_state.edges))
if st.session_state.firma != firma:
    st.session_state.firma = firma
    st.session_state.paso = 0
st.session_state.paso = max(0, min(st.session_state.paso, len(pasos) - 1))

PALETA = plt.get_cmap("tab10")
GRIS = "#D9D9D9"
pos = nx.circular_layout(G)


def dibujar(colores_nodos, actual=None):
    fig, ax = plt.subplots(figsize=(5, 5))
    bordes = ["red" if v == actual else "black" for v in G.nodes()]
    anchos = [4 if v == actual else 1.2 for v in G.nodes()]
    nx.draw(
        G, pos, ax=ax,
        with_labels=True,
        labels={v: nom(v) for v in G.nodes()},
        node_color=colores_nodos,
        node_size=900,
        font_size=10,
        font_weight="bold",
        edge_color="gray",
        edgecolors=bordes,
        linewidths=anchos,
    )
    fig.tight_layout()
    return fig


def mostrar(fig):
    st.pyplot(fig)
    plt.close(fig)


# 4 Ejecución de algoritmo
titulo("4. Ejecución del algoritmo DFS", 2)

ampliar = st.toggle("Ampliar gráfico", value=False, key="ampliar")
proporciones = [3, 2] if ampliar else [1, 2]


def mover(delta):
    st.session_state.paso += delta


def ir_a(destino):
    st.session_state.paso = destino


ultimo = len(pasos) - 1
paso = st.session_state.paso

b1, b2, b3, b4, _ = st.columns([1, 1, 1, 1, 3])
b1.button("⏮ Reiniciar", on_click=ir_a, args=(0,), disabled=paso == 0)
b2.button("◀ Anterior", on_click=mover, args=(-1,), disabled=paso == 0)
b3.button("Siguiente ▶", on_click=mover, args=(1,), disabled=paso == ultimo)
b4.button("Ir al final ⏭", on_click=ir_a, args=(ultimo,), disabled=paso == ultimo)

estado = pasos[paso]
colores = {}
for idx, comp in enumerate(estado["completas"]):
    for v in comp:
        colores[v] = PALETA(idx % 10)
idx_actual = len(estado["completas"])
for v in estado["comp_actual"]:
    colores[v] = PALETA(idx_actual % 10)
colores_nodos = [colores.get(v, GRIS) for v in G.nodes()]

col_g, col_i = st.columns(proporciones)
with col_g:
    mostrar(dibujar(colores_nodos, actual=estado["actual"]))
    st.caption("Gris = no visitado · Color = componente · Borde rojo = vértice en análisis")

with col_i:
    st.markdown(f"**Paso {paso + 1} de {len(pasos)}**")
    st.info(estado["texto"])

    if estado["pila"]:
        pila_txt = ", ".join(nom(v) for v in estado["pila"])
        st.markdown(f"**Pila:** [{pila_txt}] (tope: {nom(estado['pila'][-1])})")
    else:
        st.markdown("**Pila:** vacía")

    vis_txt = ", ".join(nom(v) for v in sorted(estado["visitados"])) or "ninguno"
    st.markdown(f"**Visitados:** {vis_txt}")

    if estado["comp_actual"]:
        act_txt = ", ".join(nom(v) for v in estado["comp_actual"])
        st.markdown(f"**Componente en formación:** {{{act_txt}}}")

    for k, comp in enumerate(estado["completas"], start=1):
        c_txt = ", ".join(nom(v) for v in comp)
        st.markdown(f"**Componente {k} completa:** {{{c_txt}}}")

# 5 solución completa
titulo("5. Solución completa", 2)

colores_final = {}
for idx, comp in enumerate(componentes):
    for v in comp:
        colores_final[v] = PALETA(idx % 10)
colores_final_nodos = [colores_final[v] for v in G.nodes()]

col_g2, col_r = st.columns(proporciones)
with col_g2:
    mostrar(dibujar(colores_final_nodos))

with col_r:
    titulo(f"Componentes conexas encontradas: {len(componentes)}", 3)
    for idx, comp in enumerate(componentes, start=1):
        nombres = ", ".join(nom(x) for x in comp)
        st.markdown(f"- **Componente {idx}** ({len(comp)} nodo(s)): {nombres}")

    with st.expander("Ver registro completo del algoritmo DFS"):
        for k, p_ in enumerate(pasos, start=1):
            st.text(f"{k:>3}. {p_['texto']}")