import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from io import BytesIO

 
st.set_page_config(page_title="Turismo no Rio", layout="wide")
 
 # --- ITEM 1: OBJETIVO E MOTIVAÇÃO ------------------------------------
 
st.title("Turismo na cidade do Rio de Janeiro")
 
st.markdown("""
**Objetivo:** os dados vêm do portal Data.Rio, seção Turismo, que publica as
estatísticas oficiais do setor na cidade.
 
**Motivação:** o turismo é uma das principais atividades econômicas do Rio, mas
os dados do portal ficam em planilhas soltas, difíceis de comparar. 
Este dash transforma planilha eminterface com filtros, gráficos e
download do recorte escolhido.
""")

# --- ITEM 2: UPLOAD DO ARQUIVO XLS -----------------------------------
 
st.sidebar.header("Dados")
arquivo = st.sidebar.file_uploader("Envie a planilha", type=["xls", "xlsx"])
 
if arquivo is None:
    st.info("Envie uma planilha de turismo do Data.Rio na barra lateral.")
    st.stop()


# --- ITEM 3 e 9 : TRÊS SELETORES (radio, checkbox e dropdown) -------------
# O key= salva a escolha do usuário, então o filtro não se perde
 
st.sidebar.header("Filtros")
 
modo = st.sidebar.radio("O que mostrar",
                        ["Todas as linhas", "Filtrar por categoria"],
                        key="modo")
 
coluna_filtro = st.sidebar.selectbox("Coluna do filtro", colunas_texto,
                                     key="coluna_filtro")
 
valores = st.sidebar.multiselect("Valores",
                                 sorted(dados[coluna_filtro].dropna().unique()),
                                 key="valores")
 
mostrar_tudo = st.sidebar.checkbox("Mostrar todas as colunas", value=True,
                                   key="mostrar_tudo")
 
filtrados = dados
 
if modo == "Filtrar por categoria" and valores:
    filtrados = filtrados[filtrados[coluna_filtro].isin(valores)]
 
if not mostrar_tudo:
    colunas = st.sidebar.multiselect("Colunas", list(dados.columns),
                                     default=list(dados.columns))
    filtrados = filtrados[colunas]


# --- ITEM 4: TABELA INTERATIVA ---------------------------------------
 
st.header("Tabela de dados")
st.caption("Clique no nome da coluna para ordenar.")
st.dataframe(filtrados)


# --- ITEM 5: DOWNLOAD EM XLS -----------------------------------------
# O arquivo Excel é montado na memória com o BytesIO, sem salvar em disco.
 
buffer = BytesIO()
filtrados.to_excel(buffer, index=False)
 
st.download_button("Baixar dados filtrados em Excel",
                   data=buffer.getvalue(),
                   file_name="turismo_filtrado.xlsx")

# --- ITEM 6: BARRA DE PROGRESSO E SPINNER ----------------------------
 
barra = st.progress(0, text="Lendo o arquivo...")
with st.spinner("Processando a planilha..."):
    dados = carregar_planilha(arquivo)
barra.progress(100, text="Pronto!")
 
# Separa as colunas de número das de texto.
colunas_numericas = dados.select_dtypes(include="number").columns.tolist()
colunas_texto = dados.select_dtypes(exclude="number").columns.tolist()

# --- ITEM 7: COLOR PICKER --------------------------------------------
 
st.sidebar.header("Aparência")
cor_fundo = st.sidebar.color_picker("Cor de fundo", "#FFFFFF")
cor_fonte = st.sidebar.color_picker("Cor da fonte", "#000000")
 
# As cores escolhidas entram na página como um bloco de CSS (pra relembrar meus tempos de ADS).
st.markdown(
    f"<style>.stApp {{ background-color: {cor_fundo}; color: {cor_fonte}; }}</style>",
    unsafe_allow_html=True,
)

# --- ITEM 8: CACHE ---------------------------------------------------
# Guarda a planilha na memória para não ler o arquivo a cada clique.
 
@st.cache_data
def carregar_planilha(arquivo):
    return pd.read_excel(arquivo)