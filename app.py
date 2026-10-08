import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st

from database.banco import ler_banco, preparar

st.set_page_config(page_title="Criminalidade em Grandes Cidades Brasileiras", page_icon="🚨", layout="wide")

ORDEM_PERIODO = ["Madrugada", "Manhã", "Tarde", "Noite"]
ORDEM_RISCO = ["Baixo", "Médio", "Alto", "Crítico"]


def fmt(n):
    return f"{n:,.0f}".replace(",", ".")


@st.cache_data
def carregar_banco():
    return ler_banco()


# ---------------- Cabeçalho ----------------
st.title("🚨 Criminalidade em Grandes Cidades Brasileiras")
st.caption("Disciplina: **Linguagens de Programação** · Avaliação G1 — Tema 15")
st.caption("Professor: **Alexandre Neves Louzada**")
st.caption("Aluno: **João Victor Gomes Teixeira**")

with st.expander("📌 Descrição do problema", expanded=True):
    st.markdown("""
A segurança pública é uma das maiores preocupações nas grandes cidades brasileiras. Este dashboard analisa
**4.440 registros mensais (2015–2024) de 37 cidades** para responder: **onde**, **quando** e **que tipo** de crime
ocorre, qual a **eficiência policial** (prisões por ocorrência) e se **renda** e **índice de violência** se
relacionam com o volume de crimes. Os dados são lidos de um banco **SQLite** (via **SQLAlchemy**) com modelagem
relacional (`cidades` ⟷ `ocorrencias`). *Base simulada para fins didáticos.*
""")

# ---------------- Fonte de dados (banco ou upload) ----------------
st.sidebar.header("📂 Fonte de dados")
arquivo = st.sidebar.file_uploader("Enviar outro CSV com o mesmo layout (opcional)", type="csv")
if arquivo:
    try:
        df = preparar(pd.read_csv(arquivo, encoding="utf-8-sig"))
        st.sidebar.success(f"CSV carregado: {len(df)} linhas")
    except Exception as e:
        st.sidebar.error(f"Arquivo inválido: {e}")
        st.stop()
else:
    df = carregar_banco()
    st.sidebar.caption("Usando o banco `database/criminalidade.db`")

# ---------------- Filtros ----------------
st.sidebar.header("🔎 Filtros")
a_min, a_max = int(df["ano"].min()), int(df["ano"].max())
anos = st.sidebar.slider("Período (anos)", a_min, a_max, (a_min, a_max))


def multi(rotulo, col, ordem=None):
    opcoes = ordem if ordem else sorted(df[col].unique())
    return st.sidebar.multiselect(rotulo, opcoes, placeholder="Todos")


regioes = multi("Região", "regiao")
ufs_disp = sorted(df[df["regiao"].isin(regioes)]["uf"].unique()) if regioes else sorted(df["uf"].unique())
ufs = st.sidebar.multiselect("UF", ufs_disp, placeholder="Todas")
cid_base = df[df["uf"].isin(ufs)] if ufs else (df[df["regiao"].isin(regioes)] if regioes else df)
cidades = st.sidebar.multiselect("Cidade", sorted(cid_base["cidade"].unique()), placeholder="Todas")
crimes = multi("Tipo de crime", "tipo_crime")
periodos = multi("Período do dia", "periodo_dia", ORDEM_PERIODO)
bairros = multi("Bairro", "bairro")
riscos = multi("Nível de risco", "nivel_risco", ORDEM_RISCO)

f = df[df["ano"].between(*anos)]
for col, sel in [("regiao", regioes), ("uf", ufs), ("cidade", cidades), ("tipo_crime", crimes),
                 ("periodo_dia", periodos), ("bairro", bairros), ("nivel_risco", riscos)]:
    if sel:
        f = f[f[col].isin(sel)]

if f.empty:
    st.warning("Nenhum registro para os filtros selecionados.")
    st.stop()

# ---------------- KPIs ----------------
st.subheader("📊 Indicadores-chave")
oc, vi, pr = f["ocorrencias"].sum(), f["vitimas"].sum(), f["prisoes"].sum()
taxa, taxa_geral = pr / oc, df["prisoes"].sum() / df["ocorrencias"].sum()
por_ano = f.groupby("ano")["ocorrencias"].sum()
var = (por_ano.iloc[-1] / por_ano.iloc[0] - 1) if len(por_ano) > 1 else 0

k = st.columns(6)
k[0].metric("Ocorrências", fmt(oc))
k[1].metric("Vítimas", fmt(vi))
k[2].metric("Prisões", fmt(pr))
k[3].metric("Taxa de prisão", f"{taxa:.1%}", f"{(taxa - taxa_geral) * 100:+.2f} p.p. vs. geral")
k[4].metric("Índice de violência médio", f"{f['indice_violencia'].mean():.1f}")
k[5].metric(f"Variação {por_ano.index[0]}→{por_ano.index[-1]}", f"{var:+.1%}")

# ---------------- Seções ----------------
abas = st.tabs(["🗺️ Visão geral", "📈 Análise temporal", "📍 Mapa", "🔗 Correlações", "📋 Dados", "✅ Conclusão"])

with abas[0]:
    c1, c2 = st.columns(2)
    reg = f.groupby("regiao", as_index=False).agg(ocorrencias=("ocorrencias", "sum"),
                                                   media=("ocorrencias", "mean"))
    c1.plotly_chart(px.bar(reg.sort_values("ocorrencias"), x="ocorrencias", y="regiao", orientation="h",
                           color="regiao", title="Ocorrências por região", text_auto=True),
                    width="stretch")
    c2.plotly_chart(px.bar(reg.sort_values("media"), x="media", y="regiao", orientation="h", color="regiao",
                           title="Média mensal por cidade (normalizada)", text_auto=".1f"),
                    width="stretch")

    c3, c4 = st.columns(2)
    tc = f.groupby("tipo_crime", as_index=False)[["ocorrencias", "vitimas", "prisoes"]].sum()
    c3.plotly_chart(px.bar(tc.melt(id_vars="tipo_crime"), x="tipo_crime", y="value", color="variable",
                           barmode="group", title="Ocorrências, vítimas e prisões por tipo de crime",
                           labels={"value": "Quantidade", "tipo_crime": "", "variable": ""}),
                    width="stretch")
    c4.plotly_chart(px.pie(f, names="periodo_dia", values="ocorrencias", hole=0.45,
                           title="Distribuição por período do dia", category_orders={"periodo_dia": ORDEM_PERIODO}),
                    width="stretch")

    top = (f.groupby(["cidade", "uf"], as_index=False)["ocorrencias"].sum()
           .sort_values("ocorrencias", ascending=False).head(10))
    st.plotly_chart(px.bar(top, x="cidade", y="ocorrencias", color="uf", title="Top 10 cidades em ocorrências"),
                    width="stretch")

    st.markdown("**Tipo de crime × período do dia** (Seaborn)")
    pv = f.pivot_table(index="tipo_crime", columns="periodo_dia", values="ocorrencias", aggfunc="sum")
    pv = pv[[p for p in ORDEM_PERIODO if p in pv.columns]]
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.heatmap(pv, annot=True, fmt=",.0f", cmap="Reds", ax=ax)
    ax.set_xlabel(""); ax.set_ylabel("")
    st.pyplot(fig)

    st.info("**Interpretação:** o Sudeste lidera em volume absoluto por ter mais cidades na amostra, mas a média "
            "mensal por cidade é quase igual entre as regiões (~30). Roubo e Tráfico são os crimes mais frequentes; "
            "Roubo se concentra na madrugada e Tráfico à tarde.")

with abas[1]:
    serie = f.groupby("data", as_index=False)["ocorrencias"].sum()
    serie["media_movel_12m"] = serie["ocorrencias"].rolling(12).mean()
    st.plotly_chart(px.line(serie, x="data", y=["ocorrencias", "media_movel_12m"],
                            title="Evolução mensal das ocorrências com média móvel de 12 meses",
                            labels={"value": "Ocorrências", "data": "", "variable": ""}),
                    width="stretch")

    c1, c2 = st.columns(2)
    anual = f.groupby(["ano", "tipo_crime"], as_index=False)["ocorrencias"].sum()
    c1.plotly_chart(px.line(anual, x="ano", y="ocorrencias", color="tipo_crime", markers=True,
                            title="Evolução anual por tipo de crime"), width="stretch")
    saz = f.groupby("mes", as_index=False)["ocorrencias"].mean()
    c2.plotly_chart(px.bar(saz, x="mes", y="ocorrencias", title="Sazonalidade: média por mês do ano",
                           labels={"ocorrencias": "Ocorrências médias", "mes": "Mês"}), width="stretch")

    st.info("**Interpretação:** a série é estável entre 2015 e 2024, sem tendência clara de alta ou queda. "
            "A média móvel de 12 meses varia pouco e não há sazonalidade forte ao longo do ano.")

with abas[2]:
    mapa = f.groupby(["cidade", "uf", "regiao", "lat", "lon"], as_index=False).agg(
        ocorrencias=("ocorrencias", "sum"), vitimas=("vitimas", "sum"), prisoes=("prisoes", "sum"),
        indice_violencia=("indice_violencia", "mean"))
    if mapa["lat"].isna().all():
        st.warning("O CSV enviado não possui coordenadas conhecidas para as cidades.")
    else:
        fig = px.scatter_map(mapa.dropna(subset=["lat"]), lat="lat", lon="lon", size="ocorrencias",
                             color="indice_violencia", color_continuous_scale="Reds", hover_name="cidade",
                             hover_data={"uf": True, "ocorrencias": True, "vitimas": True, "prisoes": True,
                                         "lat": False, "lon": False}, zoom=3.2, height=600,
                             map_style="carto-positron", title="Ocorrências por cidade (tamanho) e índice de violência (cor)")
        st.plotly_chart(fig, width="stretch")
    uf = f.groupby("uf", as_index=False)["ocorrencias"].sum().sort_values("ocorrencias", ascending=False)
    st.plotly_chart(px.bar(uf, x="uf", y="ocorrencias", title="Ocorrências por UF"), width="stretch")
    st.info("**Interpretação:** as cidades se distribuem pelas cinco regiões com volumes semelhantes; os estados "
            "com mais cidades na amostra (RJ, ES, SP, MG) acumulam mais ocorrências no total.")

with abas[3]:
    cols = ["ocorrencias", "vitimas", "prisoes", "renda_media", "indice_violencia", "taxa_prisao"]
    metodo = st.radio("Método de correlação", ["pearson", "spearman"], horizontal=True)
    corr = f[cols].corr(method=metodo).round(2)
    st.plotly_chart(px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                              title=f"Matriz de correlação ({metodo})"), width="stretch")
    c1, c2 = st.columns(2)
    x = c1.selectbox("Eixo X", cols, index=3)
    y = c2.selectbox("Eixo Y", cols, index=0)
    st.plotly_chart(px.scatter(f, x=x, y=y, color="regiao", opacity=0.5,
                               title=f"{x} × {y} (r = {f[x].corr(f[y]):.3f})"), width="stretch")
    st.plotly_chart(px.box(f, x="nivel_risco", y="indice_violencia", color="nivel_risco",
                           category_orders={"nivel_risco": ORDEM_RISCO},
                           title="Índice de violência por nível de risco"), width="stretch")
    st.info("**Interpretação:** todas as correlações ficam próximas de zero — renda média e índice de violência "
            "não explicam o número de ocorrências nesta base. O nível de risco também não acompanha o índice de "
            "violência (cada nível cobre toda a faixa de 10 a 120), indicando uma classificação inconsistente.")

with abas[4]:
    st.markdown("**Resumo por cidade**")
    resumo = f.groupby(["regiao", "uf", "cidade"], as_index=False).agg(
        ocorrencias=("ocorrencias", "sum"), vitimas=("vitimas", "sum"), prisoes=("prisoes", "sum"),
        indice_violencia=("indice_violencia", "mean"), renda_media=("renda_media", "mean"))
    resumo["taxa_prisao_%"] = 100 * resumo["prisoes"] / resumo["ocorrencias"]
    st.dataframe(resumo.sort_values("ocorrencias", ascending=False).round(2), width="stretch",
                 hide_index=True)
    st.markdown(f"**Registros filtrados** ({len(f)} linhas)")
    st.dataframe(f.drop(columns=["lat", "lon"], errors="ignore"), width="stretch", hide_index=True)
    st.download_button("⬇️ Baixar dados filtrados (CSV)", f.to_csv(index=False).encode("utf-8-sig"),
                       "criminalidade_filtrada.csv", "text/csv")

with abas[5]:
    st.subheader("Conclusão executiva")
    st.markdown(f"""
- No recorte selecionado foram registradas **{fmt(oc)} ocorrências**, com **{fmt(vi)} vítimas** e **{fmt(pr)} prisões**.
- A **taxa de prisão é de {taxa:.1%}** — cerca de 1 prisão a cada 10 ocorrências, um indicador baixo que aponta
  espaço para melhorar a capacidade de resposta policial.
- A criminalidade é **homogênea**: diferenças entre regiões, bairros e períodos se explicam pela quantidade de
  registros, não por intensidade maior. Comparações devem usar **médias normalizadas** (por cidade/mês).
- O volume ficou **estável entre 2015 e 2024**, sem tendência nem sazonalidade relevante.
- **Renda** e **índice de violência** não se correlacionam com o número de ocorrências, e o **nível de risco**
  é inconsistente com o índice — campos que precisam ser revistos antes de orientar decisões.

**Recomendações:** priorizar Roubo (madrugada) e Tráfico (tarde), metas de aumento da taxa de prisão e, com
dados reais, incluir população para calcular taxas por 100 mil habitantes.
""")

st.divider()
st.caption("Linguagens de Programação · Prof. Alexandre Neves Louzada · João Victor Gomes Teixeira · "
           "Python, Pandas, Matplotlib, Seaborn, Plotly, SQLAlchemy, SQLite e Streamlit")
