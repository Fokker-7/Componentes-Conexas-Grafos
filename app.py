import random
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.colors import to_hex

st.set_page_config(page_title="Componentes Conexas de un Grafo", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stElementToolbar"] { display: none; }
    
    /* Estilo de tarjeta para los checkboxes */
    [data-testid="stCheckbox"] {
        background-color: #f3f4f6;
        padding: 6px 10px;
        border-radius: 6px;
        border: 1px solid #d1d5db;
        transition: 0.2s;
    }
    [data-testid="stCheckbox"]:hover {
        background-color: #e5e7eb;
        border-color: #9ca3af;
    }
    [data-testid="stCheckbox"] label {
        font-weight: 600 !important;
        color: #1f2937;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def titulo(texto, nivel=1):
    nivel = max(1, min(nivel, 6))
    st.markdown(f"<h{nivel}>{texto}</h{nivel}>", unsafe_allow_html=True)

def nom(v):
    return chr(65 + v)

def construir_matriz(n, aristas, dirigido):
    matriz = np.zeros((n, n), dtype=int)
    for a, b in aristas:
        matriz[a][b] = 1
        if not dirigido:
            matriz[b][a] = 1
    return matriz

def generar_aristas_aleatorias(n, p, dirigido):
    aristas = set()
    if dirigido:
        for i in range(n):
            for j in range(n):
                if random.random() < p:
                    aristas.add((i, j))
    else:
        for i in range(n):
            for j in range(i, n):
                if random.random() < p:
                    aristas.add((i, j))
    return aristas

def dfs_no_dirigido(matriz, n, inicio_elegido):
    orden = [inicio_elegido] + [v for v in range(n) if v != inicio_elegido]
    visitados = set()
    componentes = []
    pasos = []

    def snap(texto, tipo, actual=None, pila=(), comp_actual=(), vecino=None):
        pasos.append({
            "fase": "DFS",
            "texto": texto,
            "tipo": tipo,
            "actual": actual,
            "vecino": vecino,
            "pila": list(pila),
            "visitados": set(visitados),
            "completas": [list(c) for c in componentes],
            "comp_actual": list(comp_actual),
        })

    snap("Inicio: ningún vértice ha sido explorado todavía.", "inicio")

    for inicio in orden:
        if inicio in visitados:
            continue

        comp = []
        pila = [inicio]
        snap(
            f"Iniciando búsqueda desde {nom(inicio)}: se abre una nueva componente y se apila {nom(inicio)}.",
            "nueva", inicio, pila, comp
        )

        while pila:
            actual = pila.pop()
            if actual in visitados:
                snap(f"{nom(actual)} ya fue visitado; se retira de la pila.", "descarta", actual, pila, comp)
                continue

            visitados.add(actual)
            comp.append(actual)
            snap(f"Visitando {nom(actual)}: se marca como explorado y se añade a la componente.", "visita", actual, pila, comp)

            vecinos = [j for j in range(n) if matriz[actual][j] == 1]
            if not vecinos:
                snap(f"{nom(actual)} no tiene vecinos adyacentes.", "aislado", actual, pila, comp)

            base = len(pila)
            for v in vecinos:
                if v not in visitados:
                    pila.insert(base, v)
                    snap(f"Arista {nom(actual)}—{nom(v)}: vecino no visitado, se apila.", "apila", actual, pila, comp, v)
                else:
                    snap(f"Arista {nom(actual)}—{nom(v)}: vecino ya visitado, se omite.", "ignora", actual, pila, comp, v)

        componentes.append(sorted(comp))
        nombres = ", ".join(nom(x) for x in sorted(comp))
        snap(f"Pila vacía: componente {len(componentes)} completada = {{{nombres}}}.", "cierre")

    snap(f"Algoritmo finalizado: se identificaron {len(componentes)} componentes conexas.", "fin")
    return componentes, pasos

def tarjan_dirigido(matriz, n):
    pasos = []
    dfn = [-1] * n
    low = [-1] * n
    en_pila = [False] * n
    pila = []
    tiempo = [0]
    componentes = []
    visitados = set()

    def snap(fase, texto, tipo, actual=None, comp_actual=(), completas=None, vecino=None):
        if completas is None:
            completas = componentes
        pasos.append({
            "fase": fase,
            "texto": texto,
            "tipo": tipo,
            "actual": actual,
            "vecino": vecino,
            "pila": list(pila),
            "visitados": set(visitados),
            "completas": [list(c) for c in completas],
            "comp_actual": list(comp_actual),
        })

    snap("Inicio", "Iniciando algoritmo de Tarjan. Los valores de descubrimiento (dfn) y low-link están reiniciados.", "inicio")

    def dfs(u):
        dfn[u] = low[u] = tiempo[0]
        tiempo[0] += 1
        pila.append(u)
        en_pila[u] = True
        visitados.add(u)
        
        snap("Descubrimiento", f"Visitando {nom(u)}. Se le asigna ID de descubrimiento y low-link = {dfn[u]}. Se apila.", "visita", actual=u)

        vecinos = [j for j in range(n) if matriz[u][j] == 1]
        if not vecinos:
            snap("Exploración", f"{nom(u)} no tiene aristas de salida.", "aislado", actual=u)

        for v in vecinos:
            if dfn[v] == -1:
                snap("Avance", f"Arco {nom(u)} → {nom(v)}: vecino no visitado, se avanza recursivamente.", "apila", actual=u, vecino=v)
                dfs(v)
                low[u] = min(low[u], low[v])
                snap("Retroceso", f"Regreso en {nom(u)} tras explorar {nom(v)}. Se actualiza low[{nom(u)}] = min({low[u]}, {low[v]}).", "actualiza", actual=u, vecino=v)
            elif en_pila[v]:
                low[u] = min(low[u], dfn[v])
                snap("Arco de retroceso", f"Arco {nom(u)} → {nom(v)}: {nom(v)} ya está en la pila (ciclo detectado). low[{nom(u)}] = min({low[u]}, dfn[{nom(v)}]).", "actualiza", actual=u, vecino=v)
            else:
                snap("Cruce", f"Arco {nom(u)} → {nom(v)}: {nom(v)} ya pertenece a una componente cerrada. Se ignora.", "ignora", actual=u, vecino=v)

        if low[u] == dfn[u]:
            comp = []
            snap("Cierre de Componente", f"Raíz de componente detectada en {nom(u)} (ID == low == {dfn[u]}). Extrayendo nodos de la pila...", "cierre_inicio", actual=u)
            while True:
                w = pila.pop()
                en_pila[w] = False
                comp.append(w)
                if w == u:
                    break
            comp_sorted = sorted(comp)
            componentes.append(comp_sorted)
            nombres = ", ".join(nom(x) for x in comp_sorted)
            snap("Componente consolidada", f"Componente extraída: {{{nombres}}}.", "cierre", actual=u, comp_actual=comp_sorted)

    for i in range(n):
        if dfn[i] == -1:
            snap("Nueva Búsqueda", f"Iniciando recorrido DFS desde el vértice no visitado {nom(i)}.", "nueva", actual=i)
            dfs(i)

    snap("Fin", f"Algoritmo de Tarjan finalizado: se identificaron {len(componentes)} componentes.", "fin")
    return componentes, pasos

st.session_state.setdefault("edges", set())
st.session_state.setdefault("n_anterior", None)
st.session_state.setdefault("paso", 0)
st.session_state.setdefault("firma", None)
st.session_state.setdefault("firma_aleatoria", None)

titulo("Componentes Conexas de un Grafo", 1)
st.markdown(
    "Define un grafo (dirigido o no dirigido), visualiza su matriz de adyacencia y "
    "recorre el procedimiento algorítmico paso a paso para la descomposición en componentes conexas."
)

titulo("1. Configuración", 2)
col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
with col_cfg1:
    n = st.slider("Número de nodos (n)", min_value=4, max_value=12, value=6, step=1)
with col_cfg2:
    tipo_grafo = st.radio("Tipo de grafo", ["No dirigido", "Dirigido"], horizontal=True)
with col_cfg3:
    modo = st.radio("Modo de generación", ["Manual", "Aleatorio"], horizontal=True)

es_dirigido = tipo_grafo == "Dirigido"

if st.session_state.n_anterior != n:
    st.session_state.edges = {(a, b) for (a, b) in st.session_state.edges if a < n and b < n}
    st.session_state.n_anterior = n

nodos = list(range(n))
etiquetas = [nom(i) for i in nodos]

titulo("2. Construcción del grafo", 2)

if modo == "Aleatorio":
    probabilidad = st.slider(
        "Probabilidad de conexión entre pares de vértices",
        min_value=0, max_value=100, value=35, step=5, format="%d%%"
    )
    if st.button("🎲 Generar nuevo grafo aleatorio"):
        st.session_state.edges = generar_aristas_aleatorias(n, probabilidad / 100.0, es_dirigido)
    clave_aleatoria = (n, probabilidad, es_dirigido)
    if st.session_state.firma_aleatoria != clave_aleatoria:
        st.session_state.edges = generar_aristas_aleatorias(n, probabilidad / 100.0, es_dirigido)
        st.session_state.firma_aleatoria = clave_aleatoria
else:
    st.session_state.firma_aleatoria = None
    st.markdown(
        "Marca las casillas para crear conexiones. "
        "En modo **No dirigido** la conexión es bidireccional (`A—B`). En modo **Dirigido** "
        "la conexión tiene un sentido específico (`A→B`)."
    )

    def alternar_arista(origen, destino):
        par = (origen, destino)
        if st.session_state[f"chk_{origen}_{destino}"]:
            st.session_state.edges.add(par)
        else:
            st.session_state.edges.discard(par)

    c_btn1, _ = st.columns([1, 4])
    if c_btn1.button("Limpiar todas las conexiones"):
        st.session_state.edges = set()

    anchos = [1] + [1.3] * n
    fila_enc = st.columns(anchos)
    fila_enc[0].markdown("<div style='text-align:center;font-weight:bold'>Origen \\ Destino</div>", unsafe_allow_html=True)
    for j in range(n):
        fila_enc[j + 1].markdown(f"<div style='text-align:center;font-weight:bold;color:#1E3A8A'>{nom(j)}</div>", unsafe_allow_html=True)

    for i in range(n):
        fila = st.columns(anchos)
        fila[0].markdown(f"<div style='padding-top:10px;font-weight:bold;color:#1E3A8A;text-align:center'>{nom(i)}</div>", unsafe_allow_html=True)
        for j in range(n):
            if not es_dirigido and j < i:
                fila[j + 1].markdown("<div style='text-align:center;color:#D1D5DB;padding-top:10px'>·</div>", unsafe_allow_html=True)
            else:
                par = (i, j)
                simbolo = "→" if es_dirigido else "—"
                etiqueta = f"{nom(i)}{simbolo}{nom(j)}"
                
                st.session_state[f"chk_{i}_{j}"] = par in st.session_state.edges
                fila[j + 1].checkbox(
                    etiqueta,
                    key=f"chk_{i}_{j}",
                    on_change=alternar_arista,
                    args=(i, j),
                    label_visibility="visible"
                )

aristas = sorted(st.session_state.edges)
matriz = construir_matriz(n, aristas, es_dirigido)

G = nx.DiGraph() if es_dirigido else nx.Graph()
G.add_nodes_from(nodos)
G.add_edges_from(aristas)

PALETA = plt.get_cmap("tab10")
GRIS = "#E5E7EB"
AZUL = "#93C5FD"
pos = nx.circular_layout(G)

def dibujar_grafo(colores_nodos, actual=None, vecino=None):
    fig, ax = plt.subplots(figsize=(5, 5))
    bordes = ["#DC2626" if v == actual else "#1F2937" for v in G.nodes()]
    anchos = [3.5 if v == actual else 1.2 for v in G.nodes()]

    color_aristas, ancho_aristas = [], []
    for a, b in G.edges():
        if vecino is not None and (a, b) == (actual, vecino):
            color_aristas.append("#DC2626")
            ancho_aristas.append(3.0)
        elif not es_dirigido and vecino is not None and {a, b} == {actual, vecino}:
            color_aristas.append("#DC2626")
            ancho_aristas.append(3.0)
        elif actual is not None and (a == actual or (not es_dirigido and actual in (a, b))):
            color_aristas.append("#4B5563")
            ancho_aristas.append(2.0)
        else:
            color_aristas.append("#9CA3AF")
            ancho_aristas.append(1.2)

    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=colores_nodos, node_size=800, edgecolors=bordes, linewidths=anchos)
    nx.draw_networkx_labels(G, pos, ax=ax, labels={v: nom(v) for v in G.nodes()}, font_size=10, font_weight="bold")

    if es_dirigido:
        nx.draw_networkx_edges(
            G, pos, ax=ax, edge_color=color_aristas, width=ancho_aristas,
            arrows=True, arrowsize=18, arrowstyle="-|>",
            connectionstyle="arc3,rad=0.08"
        )
    else:
        nx.draw_networkx_edges(G, pos, ax=ax, edge_color=color_aristas, width=ancho_aristas)

    ax.set_axis_off()
    fig.tight_layout()
    return fig

def mostrar_figura(fig):
    st.pyplot(fig)
    plt.close(fig)

def estilizar_matriz(actual=None, vecino=None):
    df = pd.DataFrame(matriz, index=etiquetas, columns=etiquetas)
    def colorear(datos):
        estilos = pd.DataFrame("", index=datos.index, columns=datos.columns)
        if actual is not None:
            estilos.iloc[actual, :] = "background-color: #FEF08A; color: black;"
            if vecino is not None:
                estilos.iloc[actual, vecino] = "background-color: #F97316; color: white; font-weight: bold;"
        return estilos
    return df.style.apply(colorear, axis=None)

def indicador_color(color_hex):
    return (
        f"<span style='display:inline-block;width:14px;height:14px;background:{color_hex};"
        f"border:1px solid #374151;border-radius:3px;margin-right:6px;vertical-align:middle'></span>"
    )

titulo("3. Matriz de Adyacencia", 2)
col_m, col_p = st.columns([3, 2])
with col_m:
    st.dataframe(pd.DataFrame(matriz, index=etiquetas, columns=etiquetas), use_container_width=True)
    simetria_txt = "asimétrica (dirigido)" if es_dirigido else "simétrica (no dirigido)"
    st.caption(f"{n} vértices y {len(aristas)} arista(s). Estructura {simetria_txt}.")
with col_p:
    mostrar_figura(dibujar_grafo([AZUL] * n))

titulo("4. Ejecución interactiva del algoritmo", 2)

col_ctrl1, col_ctrl2 = st.columns([2, 2])
with col_ctrl1:
    inicio_elegido = st.selectbox("Vértice inicial del recorrido", nodos, format_func=nom, disabled=es_dirigido)
    if es_dirigido:
        st.caption("En grafos dirigidos, el orden del algoritmo de Tarjan se rige por la secuencia natural de descubrimiento.")

if es_dirigido:
    componentes, pasos = tarjan_dirigido(matriz, n)
else:
    componentes, pasos = dfs_no_dirigido(matriz, n, inicio_elegido)
firma = (n, frozenset(st.session_state.edges), inicio_elegido, es_dirigido)
if st.session_state.firma != firma:
    st.session_state.firma = firma
    st.session_state.paso = 0

st.session_state.paso = max(0, min(st.session_state.paso, len(pasos) - 1))
ultimo = len(pasos) - 1
paso = st.session_state.paso

b1, b2, b3, b4, _ = st.columns([1, 1, 1, 1, 2])
if b1.button("⏮ Inicio", disabled=paso == 0):
    st.session_state.paso = 0
    st.rerun()
if b2.button("◀ Anterior", disabled=paso == 0):
    st.session_state.paso -= 1
    st.rerun()
if b3.button("Siguiente ▶", disabled=paso == ultimo):
    st.session_state.paso += 1
    st.rerun()
if b4.button("Fin ⏭", disabled=paso == ultimo):
    st.session_state.paso = ultimo
    st.rerun()

estado = pasos[paso]
colores = {}
for idx, comp in enumerate(estado["completas"]):
    for v in comp:
        colores[v] = PALETA(idx % 10)
idx_actual = len(estado["completas"])
for v in estado["comp_actual"]:
    colores[v] = PALETA(idx_actual % 10)
colores_nodos = [colores.get(v, GRIS) for v in G.nodes()]

col_g, col_i = st.columns([2, 3])
with col_g:
    mostrar_figura(dibujar_grafo(colores_nodos, actual=estado["actual"], vecino=estado["vecino"]))
    st.caption("Gris = No procesado | Con color = Componente asignada | Borde rojo = Nodo actual")

with col_i:
    st.markdown(f"**Paso {paso + 1} de {len(pasos)}** — *{estado.get('fase', 'Algoritmo DFS')}*")
    st.info(estado["texto"])

    if "pila" in estado and estado["pila"]:
        pila_str = ", ".join(nom(v) for v in estado["pila"])
        st.markdown(f"**Pila activa:** `[{pila_str}]` (tope: **{nom(estado['pila'][-1])}**)")

    if "visitados" in estado:
        vis_str = ", ".join(nom(v) for v in sorted(estado["visitados"])) or "ninguno"
        st.markdown(f"**Visitados:** `{vis_str}`")

    if estado.get("comp_actual"):
        act_str = ", ".join(nom(v) for v in estado["comp_actual"])
        st.markdown(f"**Componente en construcción:** `{{{act_str}}}`")

    if estado.get("actual") is not None:
        st.markdown(f"**Inspección en Matriz (Fila de {nom(estado['actual'])}):**")
        st.dataframe(estilizar_matriz(estado["actual"], estado["vecino"]), use_container_width=True)

titulo("5. Solución completa", 2)
colores_final = {}
for idx, comp in enumerate(componentes):
    for v in comp:
        colores_final[v] = PALETA(idx % 10)
colores_final_nodos = [colores_final[v] for v in G.nodes()]

col_g2, col_r = st.columns([2, 3])
with col_g2:
    mostrar_figura(dibujar_grafo(colores_final_nodos))

with col_r:
    titulo(f"Componentes Conexas encontradas: {len(componentes)}", 3)

    if len(componentes) == 1:
        st.success("El grafo es conexo.")
    else:
        st.warning(f"El grafo no es conexo: está segmentado en {len(componentes)} componentes.")

    for idx, comp in enumerate(componentes, start=1):
        nombres = ", ".join(nom(x) for x in comp)
        color = to_hex(PALETA((idx - 1) % 10))
        st.markdown(
            f"{indicador_color(color)}**Grupo {idx}** ({len(comp)} nodo(s)): `{nombres}`",
            unsafe_allow_html=True,
        )

    with st.expander("Ver bitácora completa de ejecución algorítmica"):
        for k, p_ in enumerate(pasos, start=1):
            st.text(f"{k:>3}. [{p_.get('fase', 'DFS')}] {p_['texto']}")