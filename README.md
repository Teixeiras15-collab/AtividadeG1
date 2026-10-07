# 🚨 Criminalidade em Grandes Cidades Brasileiras

Projeto de Análise e Visualização de Dados com Python — **Avaliação G1, Tema 15**.

| | |
|---|---|
| **Disciplina** | Linguagens de Programação |
| **Professor** | Alexandre Neves Louzada |
| **Aluno** | João Victor Gomes Teixeira |

## 🔗 Links

- **Repositório:** https://github.com/Teixeiras15-collab/AtividadeG1
- **Página do projeto (GitHub Pages):** https://teixeiras15-collab.github.io/AtividadeG1/
- **Dashboard (Streamlit Cloud):** https://atividadeg1.streamlit.app/
- **Notebook:** [`notebooks/analise_criminalidade.ipynb`](notebooks/analise_criminalidade.ipynb) · [Abrir no Colab](https://colab.research.google.com/github/Teixeiras15-collab/AtividadeG1/blob/main/notebooks/analise_criminalidade.ipynb)

## 📌 Problema

Analisar 4.440 registros mensais de ocorrências criminais em 37 grandes cidades brasileiras (2015–2024) para
entender **onde**, **quando** e **que tipo** de crime ocorre, a **eficiência policial** (prisões por ocorrência)
e a relação entre **renda**, **índice de violência** e volume de crimes. *Base simulada para fins didáticos.*

## 🗂️ Estrutura

```
AtividadeG1/
├── app.py                  # Dashboard Streamlit
├── requirements.txt
├── README.md
├── index.html              # Página do projeto (GitHub Pages)
├── dados/                  # Base CSV original
├── database/
│   ├── banco.py            # Tratamento + modelagem relacional (SQLAlchemy)
│   └── criminalidade.db    # Banco SQLite (tabelas cidades e ocorrencias)
├── notebooks/
│   └── analise_criminalidade.ipynb
└── imagens/                # Gráficos gerados pelo notebook
```

## ⚙️ Funcionalidades

**Intermediárias:** filtros múltiplos, KPIs dinâmicos, gráficos interativos, análise temporal, tratamento de dados,
integração entre tabelas (JOIN), upload de CSV, dashboard organizado em seções (abas), visualizações comparativas
e análise geográfica.

**Avançadas:**
- Persistência em banco — **SQLAlchemy + SQLite**
- Modelagem relacional — `cidades (id, cidade, uf, regiao, lat, lon)` ⟷ `ocorrencias (cidade_id FK, ...)`
- Mapa interativo — **Plotly**
- Correlação estatística — Pearson e Spearman
- Séries temporais — média móvel de 12 meses e sazonalidade

## 📊 Principais resultados

| KPI | Valor |
|---|---|
| Ocorrências | 132.845 |
| Vítimas | 22.220 |
| Prisões | 13.219 |
| Taxa de prisão | 10,0% |
| Índice de violência médio | 64,7 |
| Variação 2015 → 2024 | −0,1% |

- O Sudeste lidera em volume (~35%) por ter mais cidades na amostra; normalizado por cidade/mês, todas as regiões ficam em ~30 ocorrências.
- Roubo e Tráfico são os crimes mais frequentes; Roubo concentra-se na madrugada e Tráfico à tarde.
- A série é estável entre 2015 e 2024, sem tendência nem sazonalidade relevante.
- A taxa de prisão é baixa (~10%).
- Renda e índice de violência não se correlacionam com ocorrências; o nível de risco é inconsistente com o índice de violência.

## ▶️ Como executar

```bash
pip install -r requirements.txt
python database/banco.py      # (re)cria o banco SQLite a partir do CSV
streamlit run app.py
```

O notebook pode ser aberto no VS Code/Jupyter ou no Google Colab (o link acima clona o repositório automaticamente).

## 🛠️ Tecnologias

Python · Pandas · NumPy · Matplotlib · Seaborn · Plotly · SQLAlchemy · SQLite · Streamlit · Jupyter · GitHub Pages
