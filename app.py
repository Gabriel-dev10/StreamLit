import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF
import json

# ========== CONFIGURAÇÃO STREAMLIT ==========
st.set_page_config(page_title="RedNet - Otimização de Rotas", page_icon="🌐", layout="wide")

# ========== INICIALIZAR GRAFO ==========
if "G" not in st.session_state:
    st.session_state.G = nx.Graph()

# ========== UPLOAD DO JSON ==========
st.sidebar.subheader("📤 Upload do Arquivo JSON")
arquivo = st.sidebar.file_uploader("Carregar arquivo de topologia (.json)", type=["json"])

if arquivo is not None:
    dados = json.load(arquivo)
    st.session_state.G.clear()
    for item in dados["edges"]:
        st.session_state.G.add_edge(
            item["source"].upper(),
            item["target"].upper(),
            weight=item["latencia"]
        )
    st.sidebar.success("Arquivo carregado e grafo gerado com sucesso! ✅")

   
    LIMITE_LATENCIA = 30 
    latencia_torres = {}

    for node in st.session_state.G.nodes:
        edges = st.session_state.G.edges(node, data='weight')
        latencias = [peso for _, _, peso in edges]
        if latencias:
            media = sum(latencias) / len(latencias)
            latencia_torres[node] = media

    torres_com_latencia_alta = [t for t, lat in latencia_torres.items() if lat > LIMITE_LATENCIA]
    if torres_com_latencia_alta:
        st.warning(f"⚠️ Torres com latência alta (> {LIMITE_LATENCIA}ms): " + ", ".join(torres_com_latencia_alta))
    else:
        st.success("✅ Nenhuma torre com latência alta detectada.")

# ========== DASHBOARD ==========
st.subheader("📊 Dashboard da Rede")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🗼 Torres", st.session_state.G.number_of_nodes())

with col2:
    st.metric("🔗 Conexões", st.session_state.G.number_of_edges())

with col3:
    latencias = nx.get_edge_attributes(st.session_state.G, 'weight').values()
    media_latencia = round(sum(latencias) / len(latencias), 2) if latencias else 0
    st.metric("⚡ Latência Média", f"{media_latencia}ms")

torres_isoladas = list(nx.isolates(st.session_state.G))
if torres_isoladas:
    st.warning(f"🚨 Torres isoladas detectadas: {', '.join(torres_isoladas)}")
else:
    st.success("✅ Nenhuma torre isolada na rede.")

# ========== VISUALIZAR GRAFO ==========
st.subheader("🌐 Visualização da Rede")

if st.session_state.G.number_of_edges() > 0:
    pos = nx.spring_layout(st.session_state.G)
    plt.figure(figsize=(8, 6))
    nx.draw(
        st.session_state.G, pos,
        with_labels=True, node_color='#1B9AAA',
        node_size=1500, font_weight='bold', font_color='black'
    )
    labels = nx.get_edge_attributes(st.session_state.G, 'weight')
    nx.draw_networkx_edge_labels(st.session_state.G, pos, edge_labels=labels, font_color='black')
    plt.gca().set_facecolor('#0D1B2A')
    plt.title('Grafo de Torres - RedNet', color='black')
    plt.tight_layout()
    st.pyplot(plt)
else:
    st.info("Adicione conexões via JSON para visualizar o grafo.")

# ========== MENOR CAMINHO ==========
st.subheader("🔍 Calcular Menor Caminho")

if st.session_state.G.number_of_edges() > 0:
    col1, col2 = st.columns(2)
    with col1:
        origem = st.selectbox("Torre de Origem", list(st.session_state.G.nodes))
    with col2:
        destino = st.selectbox("Torre de Destino", list(st.session_state.G.nodes))

    if st.button("Calcular Menor Caminho"):
        try:
            caminho = nx.dijkstra_path(st.session_state.G, origem, destino)
            custo = nx.dijkstra_path_length(st.session_state.G, origem, destino)

            st.success(f"🛣️ Menor caminho de {origem} até {destino}: {' ➝ '.join(caminho)} (Latência total: {custo}ms)")

            plt.figure(figsize=(8, 6))
            nx.draw(
                st.session_state.G, pos,
                with_labels=True, node_color='#1B9AAA',
                node_size=1500, font_weight='bold', font_color='black'
            )
            nx.draw_networkx_edge_labels(st.session_state.G, pos, edge_labels=labels, font_color='black')

            path_edges = list(zip(caminho, caminho[1:]))
            nx.draw_networkx_edges(st.session_state.G, pos, edgelist=path_edges, width=4, edge_color='red')

            plt.gca().set_facecolor('#0D1B2A')
            plt.title('Menor Caminho - RedNet', color='black')
            plt.tight_layout()
            st.pyplot(plt)

            # ========== EXPORTAÇÃO ==========
            df = pd.DataFrame({
                'Ordem': list(range(1, len(caminho) + 1)),
                'Torre': caminho
            })

            st.download_button(
                label="⬇️ Baixar Caminho em CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name='relatorio_caminho.csv',
                mime='text/csv'
            )

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Relatório de Menor Caminho - RedNet", ln=True, align="C")
            pdf.ln(10)

            pdf.cell(200, 10, txt=f"Origem: {origem}", ln=True)
            pdf.cell(200, 10, txt=f"Destino: {destino}", ln=True)
            pdf.cell(200, 10, txt=f"Latência Total: {custo}ms", ln=True)
            pdf.ln(5)

            pdf.cell(200, 10, txt="Caminho:", ln=True)
            for idx, torre in enumerate(caminho, start=1):
                pdf.cell(200, 10, txt=f"{idx}. {torre}", ln=True)

            pdf_output = pdf.output(dest='S').encode('latin1')

            st.download_button(
                label="⬇️ Baixar Relatório em PDF",
                data=pdf_output,
                file_name='relatorio_caminho.pdf',
                mime='application/pdf'
            )

        except nx.NetworkXNoPath:
            st.error(f"❌ Não existe caminho entre {origem} e {destino}.")
else:
    st.info("Adicione conexões para ativar o cálculo do menor caminho.")