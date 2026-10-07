from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Sabor do Sertão", layout="wide")
st.title("Painel de Vendas: Sabor do Sertão")

ARQUIVO_LOCAL = Path("vendas_sabor_do_sertao.csv")
DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


@st.cache_data
def carregar(arquivo):
    return pd.read_csv(arquivo, parse_dates=["data"])


def brl(valor):
    """Formata número no padrão brasileiro: R$ 1.234,56"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------- carga
arquivo = st.sidebar.file_uploader("Envie o CSV de vendas", type=["csv"])
if arquivo is None and ARQUIVO_LOCAL.exists():
    arquivo = ARQUIVO_LOCAL
    st.sidebar.caption(f"Usando o arquivo local `{ARQUIVO_LOCAL.name}`.")
if arquivo is None:
    st.info("Envie o arquivo para começar.")
    st.stop()

df_bruto = carregar(arquivo)

# ------------------------------------------------- tratamento (nível 1)
ausentes = df_bruto.isna().sum()
mediana = df_bruto["avaliacao"].median()
df = df_bruto.copy()
df["avaliacao"] = df["avaliacao"].fillna(mediana)
df["dia_semana"] = df["data"].dt.dayofweek.map(dict(enumerate(DIAS)))

# ------------------------------------------------------ filtros (nível 3)
st.sidebar.header("Filtros")
cidades = st.sidebar.multiselect(
    "Cidade", sorted(df["cidade"].unique()), default=sorted(df["cidade"].unique())
)
categorias = st.sidebar.multiselect(
    "Categoria", sorted(df["categoria"].unique()),
    default=sorted(df["categoria"].unique()),
)
data_min, data_max = df["data"].min().date(), df["data"].max().date()
periodo = st.sidebar.date_input(
    "Período", value=(data_min, data_max), min_value=data_min, max_value=data_max
)

if not isinstance(periodo, (tuple, list)) or len(periodo) != 2:
    st.warning("Selecione a data inicial e a data final no filtro de período.")
    st.stop()

inicio, fim = pd.to_datetime(periodo[0]), pd.to_datetime(periodo[1])
df_f = df[
    df["cidade"].isin(cidades)
    & df["categoria"].isin(categorias)
    & df["data"].between(inicio, fim)
]

if df_f.empty:
    st.warning("Nenhuma venda encontrada com os filtros atuais.")
    st.stop()

# ----------------------------------------------------- indicadores (nível 2)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Faturamento total", brl(df_f["total"].sum()))
c2.metric("Número de vendas", f"{len(df_f):,}".replace(",", "."))
c3.metric("Ticket médio", brl(df_f["total"].mean()))
c4.metric("Avaliação média", f"{df_f['avaliacao'].mean():.2f} / 5")

aba_dados, aba_graficos, aba_insights, aba_livre = st.tabs(
    ["Exploração", "Gráficos", "Insights e exportação", "Explorador livre"]
)

# ---------------------------------------------------- exploração (nível 1)
with aba_dados:
    st.subheader("Primeiras linhas")
    st.dataframe(df_bruto.head())

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Resumo estatístico")
        st.dataframe(df_bruto.select_dtypes("number").describe())
    with col_b:
        st.subheader("Valores ausentes por coluna")
        st.dataframe(ausentes.rename("ausentes").to_frame())

    pct = ausentes["avaliacao"] / len(df_bruto) * 100
    st.caption(
        f"Tratamento: {ausentes['avaliacao']} avaliações ausentes ({pct:.1f}%) foram "
        f"preenchidas com a mediana ({mediana:.0f}). A nota é um número inteiro de 1 "
        "a 5, então a mediana mantém um valor possível e não distorce a média; "
        "remover as linhas descartaria vendas válidas só por falta da nota."
    )

# -------------------------------------------------------- gráficos (nível 4)
with aba_graficos:
    t1, t2, t3, t4, t5 = st.tabs(
        ["Mensal", "Por cidade", "Top 5 produtos", "Pagamentos", "Mapa de calor"]
    )

    with t1:
        mensal = df_f.groupby(df_f["data"].dt.to_period("M"))["total"].sum()
        mensal.index = mensal.index.astype(str)
        mensal = mensal.reset_index().rename(columns={"data": "mes"})
        fig = px.line(
            mensal, x="mes", y="total", markers=True,
            title="Faturamento mensal",
            labels={"mes": "Mês", "total": "Faturamento (R$)"},
        )
        st.plotly_chart(fig)

    with t2:
        por_cidade = (
            df_f.groupby("cidade")["total"].sum().sort_values(ascending=False)
            .reset_index()
        )
        fig = px.bar(
            por_cidade, x="cidade", y="total", text_auto=".2s",
            title="Faturamento por cidade",
            labels={"cidade": "Cidade", "total": "Faturamento (R$)"},
        )
        st.plotly_chart(fig)

    with t3:
        top5 = (
            df_f.groupby("produto")["quantidade"].sum().nlargest(5)
            .sort_values().reset_index()
        )
        fig = px.bar(
            top5, x="quantidade", y="produto", orientation="h", text_auto=True,
            title="Top 5 produtos mais vendidos (quantidade)",
            labels={"quantidade": "Unidades vendidas", "produto": "Produto"},
        )
        st.plotly_chart(fig)

    with t4:
        pagto = df_f.groupby("pagamento")["total"].sum().reset_index()
        fig = px.pie(
            pagto, names="pagamento", values="total",
            title="Participação das formas de pagamento no faturamento",
        )
        st.plotly_chart(fig)

    with t5:
        fig = px.density_heatmap(
            df_f, x="hora", y="dia_semana", histfunc="count",
            category_orders={"dia_semana": DIAS},
            title="Número de vendas por dia da semana e hora",
            labels={"hora": "Hora do dia", "dia_semana": "Dia da semana",
                    "count": "Vendas"},
            nbinsx=df_f["hora"].nunique(),
        )
        st.plotly_chart(fig)

# --------------------------------------------------------- insights (nível 5)
with aba_insights:
    st.subheader("Três conclusões para o gestor")

    melhor_cidade = df_f.groupby("cidade")["total"].sum().idxmax()
    share_cidade = (
        df_f.groupby("cidade")["total"].sum().max() / df_f["total"].sum() * 100
    )
    hora_pico = df_f.groupby("hora").size().idxmax()
    dia_pico = df_f.groupby("dia_semana").size().idxmax()
    prod_top = df_f.groupby("produto")["quantidade"].sum().idxmax()
    cat_top = df_f.groupby("categoria")["total"].sum().idxmax()
    pagto_top = df_f.groupby("pagamento")["total"].sum().idxmax()
    share_pagto = (
        df_f.groupby("pagamento")["total"].sum().max() / df_f["total"].sum() * 100
    )

    st.markdown(
        f"""
1. **Onde vendemos mais:** {melhor_cidade} concentra {share_cidade:.0f}% do
   faturamento no período filtrado.
2. **Quando vendemos mais:** o pico de vendas é às **{hora_pico}h**, e o dia mais
   movimentado é **{dia_pico}**. É a janela ideal para reforçar a equipe e o estoque.
3. **O que vendemos e como pagam:** o produto mais vendido em unidades é
   **{prod_top}**, a categoria que mais fatura é **{cat_top}**, e **{pagto_top}**
   responde por {share_pagto:.0f}% do faturamento.
        """
    )
    st.caption("Os textos acima se atualizam conforme os filtros da barra lateral.")

    st.download_button(
        "Baixar CSV filtrado",
        data=df_f.drop(columns=["dia_semana"]).to_csv(index=False).encode("utf-8"),
        file_name="vendas_filtradas.csv",
        mime="text/csv",
    )

# ------------------------------------------------------- bônus: explorador livre
with aba_livre:
    st.subheader("Explorador livre")
    st.caption("Envie qualquer CSV (ou use os dados filtrados do painel).")
    outro = st.file_uploader("CSV para explorar", type=["csv"], key="livre")
    base = pd.read_csv(outro) if outro is not None else df_f

    colunas = list(base.columns)
    numericas = base.select_dtypes("number").columns.tolist()
    cx, cy, ct = st.columns(3)
    eixo_x = cx.selectbox("Eixo X", colunas, key="eixo_x")
    eixo_y = cy.selectbox("Eixo Y", numericas or colunas, key="eixo_y")
    tipo = ct.selectbox(
        "Tipo de gráfico",
        ["Barras", "Linha", "Dispersão", "Histograma", "Box plot"],
        key="tipo",
    )

    try:
        if tipo == "Barras":
            dados = base.groupby(eixo_x, as_index=False)[eixo_y].sum()
            fig = px.bar(dados, x=eixo_x, y=eixo_y)
        elif tipo == "Linha":
            dados = base.groupby(eixo_x, as_index=False)[eixo_y].sum()
            fig = px.line(dados.sort_values(eixo_x), x=eixo_x, y=eixo_y)
        elif tipo == "Dispersão":
            fig = px.scatter(base, x=eixo_x, y=eixo_y)
        elif tipo == "Histograma":
            fig = px.histogram(base, x=eixo_x)
        else:
            fig = px.box(base, x=eixo_x, y=eixo_y)
        fig.update_layout(title=f"{tipo}: {eixo_y} por {eixo_x}")
        st.plotly_chart(fig)
    except Exception as erro:  # combinação de colunas inválida para o gráfico
        st.warning(f"Não foi possível gerar esse gráfico com as colunas escolhidas: {erro}")
