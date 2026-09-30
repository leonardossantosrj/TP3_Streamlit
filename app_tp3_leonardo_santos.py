
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from io import BytesIO
 
 

st.set_page_config(page_title="Turismo no Rio", layout="wide")
 
 
# --- ITEM 8: CACHE ---------------------------------------------------
# Guarda a planilha na memória para não ler o arquivo a cada clique
 
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
         "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
 
 
@st.cache_data
def carregar_planilha(arquivo, aba):
    bruto = pd.read_excel(arquivo, sheet_name=aba, header=None, usecols="A:N")
    bruto.columns = ["País", "Total"] + MESES
 
    # A planilha tem título e cabeçalho em várias linhas - Ref https://www.data.rio/documents/a6c6c3ff7d1947a99648494e0745046d/about
    inicio = bruto[bruto["País"].astype(str).str.strip() == "Total"].index[0]
    dados = bruto.loc[inicio:].copy()
 
    dados["Total"] = pd.to_numeric(dados["Total"], errors="coerce")
    dados = dados.dropna(subset=["Total"])
 
    # Na planilha, "-" significa zero .
    for mes in MESES:
        dados[mes] = pd.to_numeric(dados[mes], errors="coerce").fillna(0)
    dados[["Total"] + MESES] = dados[["Total"] + MESES].astype(int)
 
    # Tratamento e leitura dos dados de países
    nome = dados["País"].astype(str)
    recuo = nome.str.len() - nome.str.lstrip().str.len()
    dados["País"] = nome.str.strip()
    dados["Continente"] = dados["País"].where(recuo == 0).ffill()
    proximo_recuo = recuo.shift(-1).fillna(0)
    dados = dados[(recuo > 0) & (recuo >= proximo_recuo)]
 
    return dados[["Continente", "País", "Total"] + MESES]
 
 
# --- ITEM 1: OBJETIVO E MOTIVAÇÃO ------------------------------------
 
st.title("Turismo na cidade do Rio de Janeiro")
 
st.markdown("""
**Dataset escolhido:** Chegadas mensais de turistas pelo Rio de Janeiro, segundo os
continentes e países de residência permanente, entre 2006-2019 (Data.Rio, seção Turismo).
 
**Objetivo:** os dados vêm do portal Data.Rio, seção Turismo, que publica as
estatísticas oficiais do setor na cidade.
 
**Motivação:** o turismo é uma das principais atividades econômicas do Rio, mas
os dados do portal ficam em planilhas soltas, difíceis de comparar.
Este dash transforma a planilha em uma interface com filtros, gráficos e
download do recorte escolhido.
 
**O que o painel faz:** upload da planilha, filtros (radio, checkbox e dropdown),
tabela interativa, download em Excel, gráficos de barras, linha, pizza,
histograma e dispersão, e métricas de resumo.
""")
 
 
# --- ITEM 7: COLOR PICKER --------------------------------------------
 
st.sidebar.header("Aparência")
cor_fundo = st.sidebar.color_picker("Cor de fundo", "#FFFFFF")
cor_fonte = st.sidebar.color_picker("Cor da fonte", "#000000")
 
# As cores escolhidas entram na página como um bloco de CSS (pra relembrar meus tempos de ADS).
st.markdown(
    f"""<style>
    .stApp {{ background-color: {cor_fundo}; }}
    [data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3,
    [data-testid="stMain"] p, [data-testid="stMain"] label {{ color: {cor_fonte}; }}
    </style>""",
    unsafe_allow_html=True,
)
 
 
# --- ITEM 2: UPLOAD DO ARQUIVO XLS -----------------------------------
 
st.sidebar.header("Dados")
arquivo = st.sidebar.file_uploader("Envie a planilha", type=["xls", "xlsx"])
 
if arquivo is None:
    st.info("Envie uma planilha de turismo do Data.Rio na barra lateral.")
    st.stop()
 
# A planilha pode ter uma aba por ano.
abas = pd.ExcelFile(arquivo).sheet_names
aba = st.sidebar.selectbox("Aba da planilha", abas, key="aba")
 
 
# --- ITEM 6: BARRA DE PROGRESSO E SPINNER ----------------------------
 
barra = st.progress(0, text="Lendo o arquivo...")
with st.spinner("Processando a planilha..."):
    dados = carregar_planilha(arquivo, aba)
barra.progress(100, text="Pronto!")
 
# Separa as colunas de número das de texto.
colunas_numericas = dados.select_dtypes(include="number").columns.tolist()
colunas_texto = dados.select_dtypes(exclude="number").columns.tolist()
 
 
# --- ITEM 3 e 9: TRÊS SELETORES (radio, checkbox e dropdown) ---------
# O key= salva a escolha do usuário no session state, então o filtro não se perde
 
st.sidebar.header("Filtros")
 
modo = st.sidebar.radio("O que mostrar",
                        ["Todas as linhas", "Filtrar por categoria"],
                        key="modo")
 
coluna_filtro = st.sidebar.selectbox("Coluna do filtro", colunas_texto,
                                     key="coluna_filtro")
 
valores = st.sidebar.multiselect("Valores",
                                 sorted(dados[coluna_filtro].dropna().astype(str).unique()),
                                 key="valores")
 
mostrar_tudo = st.sidebar.checkbox("Mostrar todas as colunas", value=True,
                                   key="mostrar_tudo")
 
filtrados = dados
 
if modo == "Filtrar por categoria" and valores:
    filtrados = filtrados[filtrados[coluna_filtro].astype(str).isin(valores)]
 
if not mostrar_tudo:
    colunas = st.sidebar.multiselect("Colunas", list(dados.columns),
                                     default=list(dados.columns),
                                     key="colunas")
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
 
 
# Os gráficos e as métricas precisam de pelo menos uma coluna de número.
numericas_filtradas = filtrados.select_dtypes(include="number").columns.tolist()
 
if filtrados.empty or not numericas_filtradas:
    st.warning("Os gráficos precisam de linhas e de pelo menos uma coluna numérica.")
    st.stop()
 
 
# --- ITEM 10: GRÁFICOS SIMPLES (barras, linha e pizza) ---------------
 
st.header("Gráficos simples")
 
c1, c2 = st.columns(2)
categoria = c1.selectbox("Agrupar por", list(filtrados.columns), key="categoria")
valor = c2.selectbox("Valor", numericas_filtradas, key="valor")
 
agrupado = filtrados.groupby(categoria)[valor].sum()
 
g1, g2, g3 = st.columns(3)
 
g1.subheader("Barras")
g1.bar_chart(agrupado)
 
g2.subheader("Linha: turistas por mês")
meses_visiveis = [m for m in MESES if m in filtrados.columns]
por_mes = filtrados[meses_visiveis].sum()
# O número na frente mantém os meses em ordem no eixo.
por_mes.index = [f"{MESES.index(m) + 1:02d}-{m[:3]}" for m in meses_visiveis]
g2.line_chart(por_mes)
 
# O Streamlit não tem pizza nativa, então usei o matplotlib.
# Só as 10 maiores fatias, senão a pizza fica ilegível.
g3.subheader("Pizza")
top10 = agrupado.nlargest(10)
figura_pizza, eixo_pizza = plt.subplots()
eixo_pizza.pie(top10, labels=top10.index, autopct="%1.0f%%")
g3.pyplot(figura_pizza)
 
 
# --- ITEM 11: GRÁFICOS AVANÇADOS (histograma e dispersão) ------------
 
st.header("Gráficos avançados")
 
a1, a2 = st.columns(2)
 
a1.subheader(f"Histograma de {valor}")
figura_hist, eixo_hist = plt.subplots()
eixo_hist.hist(filtrados[valor].dropna(), bins=20)
eixo_hist.set_xlabel(valor)
eixo_hist.set_ylabel("Frequência")
a1.pyplot(figura_hist)
 
a2.subheader("Dispersão")
eixo_x = a2.selectbox("Eixo X", numericas_filtradas, key="eixo_x")
eixo_y = a2.selectbox("Eixo Y", numericas_filtradas,
                      index=min(1, len(numericas_filtradas) - 1), key="eixo_y")
figura_disp, eixo_disp = plt.subplots()
eixo_disp.scatter(filtrados[eixo_x], filtrados[eixo_y])
eixo_disp.set_xlabel(eixo_x)
eixo_disp.set_ylabel(eixo_y)
a2.pyplot(figura_disp)
 
 
# --- ITEM 12: MÉTRICAS BÁSICAS ---------------------------------------
 
st.header("Resumo")
 
m1, m2, m3 = st.columns(3)
m1.metric("Registros", len(filtrados))
m2.metric(f"Soma de {valor}", f"{filtrados[valor].sum():,.0f}")
m3.metric(f"Média de {valor}", f"{filtrados[valor].mean():,.2f}")


#Para esse caso usei esse - https://www.data.rio/documents/a6c6c3ff7d1947a99648494e0745046d/about