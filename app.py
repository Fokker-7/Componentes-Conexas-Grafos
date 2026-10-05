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


def generar_aristas_aleatorias(n, p):
    return {(i, j) for i in range(n) for j in range(i + 1, n) if random.random() < p}


def construir_matriz(n, aristas):
    matriz = np.zeros((n, n), dtype=int)
    for (a, b) in aristas:
        matriz[a][b] = 1
        matriz[b][a] = 1
    return matriz


def vecinos_de(matriz, v):
    return [j for j in range(len(matriz)) if matriz[v][j] == 1]


def dfs_paso_a_paso(matriz, orden):
    visitados = set()
    componentes = []
    pasos = []

    def snap(texto, tipo, actual=None, pila=(), comp_actual=(), vecino=None):
        pasos.append({
            "texto": texto,
            "tipo": tipo,
            "actual": actual,
            "vecino": vecino,
            "pila": list(pila),
            "visitados": set(visitados),
            "completas": [list(c) for c in componentes],
            "comp_actual": list(comp_actual),
        })

    snap("Inicio: ningún vértice ha sido visitado todavía.", "inicio")

    for inicio in orden:
        if inicio in visitados:
            continue

        comp = []
        pila = [inicio]
        snap(f"Iniciando desde vértice {nom(inicio)}: comienza una nueva componente "
             f"conexa. Se apila {nom(inicio)}.", "nueva", inicio, pila, comp)

        while pila:
            actual = pila.pop()
            if actual in visitados:
                snap(f"{nom(actual)} ya fue visitado; se descarta de la pila.",
                     "descarta", actual, pila, comp)
                continue

            visitados.add(actual)
            comp.append(actual)
            snap(f"Visitando vértice {nom(actual)}: se marca como visitado y se "
                 f"agrega a la componente actual.", "visita", actual, pila, comp)

            vecinos = vecinos_de(matriz, actual)
            if not vecinos:
                snap(f"{nom(actual)} no tiene vecinos (vértice aislado).",
                     "aislado", actual, pila, comp)
            base = len(pila)
            for v in vecinos:
                if v not in visitados:
                    pila.insert(base, v)
                    snap(f"Vértice {nom(actual)} conecta con {nom(v)}: no visitado, "
                         f"se apila.", "apila", actual, pila, comp, v)
                else:
                    snap(f"Vértice {nom(actual)} conecta con {nom(v)}: ya visitado, "
                         f"se ignora.", "ignora", actual, pila, comp, v)

        componentes.append(sorted(comp))
        nombres = ", ".join(nom(x) for x in sorted(comp))
        snap(f"Pila vacía: la componente {len(componentes)} está completa = "
             f"{{{nombres}}}.", "cierre")

    snap(f"Fin del algoritmo: se encontraron {len(componentes)} componente(s) conexa(s).",
         "fin")
    return componentes, pasos


def pregunta_del_paso(pasos, paso, n):
    if paso + 1 >= len(pasos):
        return None
    siguiente = pasos[paso + 1]
    if siguiente["tipo"] not in ("visita", "nueva") or paso + 1 == 1:
        return None

    if siguiente["tipo"] == "visita" and pasos[paso]["tipo"] == "nueva":
        return None

    correcto = siguiente["actual"]
    opciones = sorted(set(range(n)) - pasos[paso]["visitados"])
    if len(opciones) < 2:
        return None
    if siguiente["tipo"] == "visita":
        enunciado = "¿Qué vértice se visitará en el siguiente paso?"
        explicacion = (f"Se extrae el vértice del tope de la pila, que es {nom(correcto)}.")
    else:
        enunciado = "La pila quedó vacía. ¿Desde qué vértice empezará la siguiente componente?"
        explicacion = (f"El bucle principal toma el siguiente vértice no visitado, que es "
                       f"{nom(correcto)}.")
    return {"enunciado": enunciado, "opciones": opciones, "correcto": correcto,
            "explicacion": explicacion}


st.session_state.setdefault("edges", set())
st.session_state.setdefault("n_anterior", None)
st.session_state.setdefault("paso", 0)
st.session_state.setdefault("firma", None)
st.session_state.setdefault("firma_aleatoria", None)
st.session_state.setdefault("respuestas", {})

titulo("Componentes Conexas de un Grafo", 1)
st.markdown(
    "Define un grafo (aleatorio o manual), revisa su matriz de adyacencia y "
    "recorre paso a paso el algoritmo DFS que identifica sus componentes conexas."
)

titulo("1. Configuración", 2)

col_cfg1, col_cfg2 = st.columns(2)
with col_cfg1:
    n = st.slider("Número de nodos (n)", min_value=4, max_value=12, value=6, step=1)
with col_cfg2:
    modo = st.radio("Modo de creación del grafo", ["Aleatorio", "Manual"], horizontal=True)

if st.session_state.n_anterior != n:
    st.session_state.edges = {
        (a, b) for (a, b) in st.session_state.edges if a < n and b < n
    }
    st.session_state.n_anterior = n

nodos = list(range(n))
etiquetas = [nom(i) for i in nodos]

titulo("2. Construcción del grafo", 2)

if modo == "Aleatorio":
    probabilidad = st.slider(
        "Probabilidad de conexión entre cada par de nodos",
        min_value=0, max_value=100, value=50, step=5, format="%d%%",
    )
    otro = st.button("🎲 Generar otro grafo aleatorio")
    clave_aleatoria = (n, probabilidad)
    if otro or st.session_state.firma_aleatoria != clave_aleatoria:
        st.session_state.edges = generar_aristas_aleatorias(n, probabilidad / 100.0)
        st.session_state.firma_aleatoria = clave_aleatoria
    st.caption("El grafo se genera automáticamente al cambiar el número de nodos o la "
               "probabilidad. Usa el botón para obtener otro grafo con los mismos valores.")

else:
    st.session_state.firma_aleatoria = None
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

aristas = sorted(st.session_state.edges)
matriz = construir_matriz(n, aristas)

G = nx.Graph()
G.add_nodes_from(nodos)
G.add_edges_from(aristas)

PALETA = plt.get_cmap("tab10")
GRIS = "#D9D9D9"
AZUL = "#A7C7E7"
pos = nx.circular_layout(G)


def dibujar(colores_nodos, actual=None, vecino=None):
    fig, ax = plt.subplots(figsize=(5, 5))
    bordes = ["red" if v == actual else "black" for v in G.nodes()]
    anchos = [4 if v == actual else 1.2 for v in G.nodes()]
    color_aristas, ancho_aristas = [], []
    for (a, b) in G.edges():
        if vecino is not None and {a, b} == {actual, vecino}:
            color_aristas.append("red")
            ancho_aristas.append(3.5)
        elif actual is not None and actual in (a, b):
            color_aristas.append("#555555")
            ancho_aristas.append(2.2)
        else:
            color_aristas.append("#B0B0B0")
            ancho_aristas.append(1.2)
    nx.draw(
        G, pos, ax=ax,
        with_labels=True,
        labels={v: nom(v) for v in G.nodes()},
        node_color=colores_nodos,
        node_size=900,
        font_size=10,
        font_weight="bold",
        edge_color=color_aristas,
        width=ancho_aristas,
        edgecolors=bordes,
        linewidths=anchos,
    )
    fig.tight_layout()
    return fig


def mostrar(fig):
    st.pyplot(fig)
    plt.close(fig)


def matriz_resaltada(actual=None, vecino=None):
    df = pd.DataFrame(matriz, index=etiquetas, columns=etiquetas)

    def estilo(datos):
        est = pd.DataFrame("", index=datos.index, columns=datos.columns)
        if actual is not None:
            est.iloc[actual, :] = "background-color: #FFF3B0; color: #000000;"
            if vecino is not None:
                est.iloc[actual, vecino] = ("background-color: #F4A261; color: #000000; "
                                            "font-weight: bold;")
        return est

    return df.style.apply(estilo, axis=None)


def cuadro_color(color_hex):
    return (f"<span style='display:inline-block;width:14px;height:14px;"
            f"background:{color_hex};border:1px solid #333;border-radius:3px;"
            f"margin-right:6px;vertical-align:middle'></span>")


ampliar = st.session_state.get("ampliar", False)
proporciones = [3, 2] if ampliar else [1, 2]

titulo("3. Matriz de Adyacencia", 2)

col_m, col_p = st.columns([3, 2])
with col_m:
    st.table(pd.DataFrame(matriz, index=etiquetas, columns=etiquetas))
    st.caption(f"{n} vértices y {len(aristas)} arista(s). La matriz es simétrica porque el "
               f"grafo es no dirigido.")
with col_p:
    mostrar(dibujar([AZUL] * n))
if not aristas:
    st.info("El grafo no tiene aristas: cada vértice formará su propia componente conexa.")

titulo("4. Ejecución del algoritmo DFS", 2)

col_o1, col_o2, col_o3 = st.columns(3)
with col_o1:
    st.toggle("Ampliar gráfico", value=False, key="ampliar")
with col_o2:
    inicio_elegido = st.selectbox("Vértice inicial del recorrido", nodos, format_func=nom)
with col_o3:
    practica = st.toggle("Modo práctica: predice el siguiente vértice", key="practica")

orden = [inicio_elegido] + [v for v in nodos if v != inicio_elegido]
componentes, pasos = dfs_paso_a_paso(matriz, orden)

firma = (n, frozenset(st.session_state.edges), inicio_elegido)
if st.session_state.firma != firma:
    st.session_state.firma = firma
    st.session_state.paso = 0
    st.session_state.respuestas = {}
st.session_state.paso = max(0, min(st.session_state.paso, len(pasos) - 1))


def mover(delta):
    st.session_state.paso += delta


def ir_a(destino):
    st.session_state.paso = destino


def reiniciar():
    st.session_state.paso = 0
    st.session_state.respuestas = {}


def responder(paso_preg, correcto):
    elegido = st.session_state.get(f"preg_{paso_preg}")
    if elegido is not None:
        st.session_state.respuestas[paso_preg] = (elegido, elegido == correcto)


ultimo = len(pasos) - 1
paso = st.session_state.paso
pregunta = pregunta_del_paso(pasos, paso, n) if practica else None
pendiente = pregunta is not None and paso not in st.session_state.respuestas

b1, b2, b3, b4, _ = st.columns([1, 1, 1, 1, 3])
b1.button("⏮ Reiniciar", on_click=reiniciar, disabled=paso == 0)
b2.button("◀ Anterior", on_click=mover, args=(-1,), disabled=paso == 0)
b3.button("Siguiente ▶", on_click=mover, args=(1,), disabled=paso == ultimo or pendiente)
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
    mostrar(dibujar(colores_nodos, actual=estado["actual"], vecino=estado["vecino"]))
    st.caption("Gris = no visitado · Color = componente · Borde rojo = vértice en análisis · "
               "Arista roja = conexión que se está revisando")

with col_i:
    st.markdown(f"**Paso {paso + 1} de {len(pasos)}**")
    st.info(estado["texto"])

    if pregunta:
        with st.container(border=True):
            st.markdown(f"🧠 **Modo práctica:** {pregunta['enunciado']}")
            respuesta = st.session_state.respuestas.get(paso)
            if respuesta is None:
                st.radio("Tu respuesta", pregunta["opciones"], format_func=nom,
                         horizontal=True, index=None, key=f"preg_{paso}")
                st.button("Comprobar respuesta", on_click=responder,
                          args=(paso, pregunta["correcto"]))
            else:
                elegido, acierto = respuesta
                if acierto:
                    st.success(f"¡Correcto! {pregunta['explicacion']}")
                else:
                    st.error(f"Elegiste {nom(elegido)}, pero no es correcto. "
                             f"{pregunta['explicacion']}")

    if practica and st.session_state.respuestas:
        aciertos = sum(1 for _, ok in st.session_state.respuestas.values() if ok)
        st.caption(f"Aciertos en el modo práctica: {aciertos} de "
                   f"{len(st.session_state.respuestas)}")

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

    if estado["actual"] is not None:
        st.markdown(f"**Matriz de adyacencia** (fila de {nom(estado['actual'])} resaltada; "
                    f"sus vecinos son las columnas con 1)")
        st.table(matriz_resaltada(estado["actual"], estado["vecino"]))

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
    if len(componentes) == 1:
        st.success("El grafo es conexo: todos sus vértices están unidos por algún camino.")
    else:
        st.warning(f"El grafo no es conexo: está dividido en {len(componentes)} componentes.")

    for idx, comp in enumerate(componentes, start=1):
        nombres = ", ".join(nom(x) for x in comp)
        color = to_hex(PALETA((idx - 1) % 10))
        st.markdown(
            f"{cuadro_color(color)}**Componente {idx}** ({len(comp)} nodo(s)): {nombres}",
            unsafe_allow_html=True,
        )

    aislados = [nom(c[0]) for c in componentes if len(c) == 1]
    if aislados:
        st.caption(f"Vértices aislados (sin aristas): {', '.join(aislados)}")

    with st.expander("Ver registro completo del algoritmo DFS"):
        for k, p_ in enumerate(pasos, start=1):
            st.text(f"{k:>3}. {p_['texto']}")
