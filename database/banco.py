"""Preparação dos dados e persistência em SQLite (SQLAlchemy).

Modelo relacional:
    cidades (id PK, cidade, uf, regiao, lat, lon)
    ocorrencias (id PK, cidade_id FK -> cidades.id, demais atributos)
"""
from pathlib import Path

import pandas as pd
from sqlalchemy import (Column, Date, Float, ForeignKey, Integer, MetaData,
                        String, Table, create_engine)

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "dados" / "simulacao_criminalidade_brasil.csv"
DB = RAIZ / "database" / "criminalidade.db"

# Coordenadas aproximadas das sedes municipais (para o mapa interativo)
COORDENADAS = {
    "Manaus": (-3.119, -60.022), "Belém": (-1.456, -48.490), "Santarém": (-2.443, -54.708),
    "Porto Velho": (-8.761, -63.900), "Palmas": (-10.184, -48.333), "Salvador": (-12.977, -38.501),
    "Feira de Santana": (-12.267, -38.966), "Recife": (-8.047, -34.877),
    "Jaboatão dos Guararapes": (-8.113, -35.015), "Fortaleza": (-3.732, -38.527),
    "Juazeiro do Norte": (-7.213, -39.315), "São Luís": (-2.530, -44.303),
    "João Pessoa": (-7.119, -34.845), "Brasília": (-15.794, -47.882), "Goiânia": (-16.686, -49.265),
    "Aparecida de Goiânia": (-16.823, -49.244), "Cuiabá": (-15.601, -56.097),
    "Campo Grande": (-20.469, -54.620), "São Paulo": (-23.551, -46.633), "Campinas": (-22.906, -47.061),
    "Ribeirão Preto": (-21.178, -47.810), "Rio de Janeiro": (-22.907, -43.173),
    "Niterói": (-22.883, -43.104), "Nova Iguaçu": (-22.759, -43.451), "Petrópolis": (-22.505, -43.179),
    "Belo Horizonte": (-19.917, -43.935), "Uberlândia": (-18.919, -48.277),
    "Juiz de Fora": (-21.764, -43.350), "Vitória": (-20.315, -40.312), "Vila Velha": (-20.330, -40.292),
    "Serra": (-20.128, -40.308), "Curitiba": (-25.429, -49.271), "Londrina": (-23.310, -51.163),
    "Florianópolis": (-27.595, -48.548), "Joinville": (-26.304, -48.846),
    "Porto Alegre": (-30.035, -51.218), "Caxias do Sul": (-29.168, -51.179),
}

TEXTO = ["regiao", "uf", "cidade", "bairro", "tipo_crime", "periodo_dia", "nivel_risco"]

metadata = MetaData()
cidades = Table(
    "cidades", metadata,
    Column("id", Integer, primary_key=True),
    Column("cidade", String, nullable=False),
    Column("uf", String(2), nullable=False),
    Column("regiao", String, nullable=False),
    Column("lat", Float),
    Column("lon", Float),
)
ocorrencias = Table(
    "ocorrencias", metadata,
    Column("id", Integer, primary_key=True),
    Column("cidade_id", Integer, ForeignKey("cidades.id"), nullable=False),
    Column("data", Date, nullable=False),
    Column("ano", Integer), Column("mes", Integer), Column("trimestre", Integer),
    Column("bairro", String), Column("tipo_crime", String), Column("periodo_dia", String),
    Column("ocorrencias", Integer), Column("vitimas", Integer), Column("prisoes", Integer),
    Column("renda_media", Float), Column("indice_violencia", Float), Column("nivel_risco", String),
    Column("taxa_prisao", Float), Column("vitimas_por_ocorrencia", Float), Column("faixa_renda", String),
)


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    """Limpeza, tipagem e engenharia de atributos."""
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    for c in TEXTO:
        df[c] = df[c].astype(str).str.strip()
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df.dropna(subset=["data"]).drop_duplicates()
    # valores negativos não fazem sentido em contagens
    df = df[(df[["ocorrencias", "vitimas", "prisoes"]] >= 0).all(axis=1)]

    df["trimestre"] = df["data"].dt.quarter
    df["taxa_prisao"] = (df["prisoes"] / df["ocorrencias"].replace(0, pd.NA)).astype(float).round(4)
    df["vitimas_por_ocorrencia"] = (df["vitimas"] / df["ocorrencias"].replace(0, pd.NA)).astype(float).round(4)
    df["faixa_renda"] = pd.qcut(df["renda_media"], 4, labels=["Baixa", "Média-baixa", "Média-alta", "Alta"]).astype(str)
    return df.reset_index(drop=True)


def salvar_banco(df: pd.DataFrame, db: Path = DB):
    """Grava o DataFrame preparado no SQLite em duas tabelas relacionadas."""
    engine = create_engine(f"sqlite:///{db}")
    metadata.drop_all(engine)
    metadata.create_all(engine)

    dim = df[["cidade", "uf", "regiao"]].drop_duplicates().sort_values("cidade").reset_index(drop=True)
    dim.insert(0, "id", dim.index + 1)
    dim["lat"] = dim["cidade"].map(lambda c: COORDENADAS.get(c, (None, None))[0])
    dim["lon"] = dim["cidade"].map(lambda c: COORDENADAS.get(c, (None, None))[1])

    fato = df.merge(dim[["id", "cidade"]].rename(columns={"id": "cidade_id"}), on="cidade")
    fato = fato[[c.name for c in ocorrencias.columns if c.name != "id"]].copy()
    fato["data"] = fato["data"].dt.date

    with engine.begin() as con:
        con.execute(cidades.insert(), dim.to_dict("records"))
        con.execute(ocorrencias.insert(), fato.to_dict("records"))
    return engine


def ler_banco(db: Path = DB) -> pd.DataFrame:
    """Lê o banco com JOIN entre as tabelas. Cria o banco a partir do CSV se não existir."""
    if not db.exists():
        salvar_banco(preparar(pd.read_csv(CSV, encoding="utf-8-sig")), db)
    engine = create_engine(f"sqlite:///{db}")
    sql = """
        SELECT o.*, c.cidade, c.uf, c.regiao, c.lat, c.lon
        FROM ocorrencias o JOIN cidades c ON c.id = o.cidade_id
    """
    df = pd.read_sql(sql, engine, parse_dates=["data"])
    return df.drop(columns=["id", "cidade_id"])


if __name__ == "__main__":
    bruto = pd.read_csv(CSV, encoding="utf-8-sig")
    df = preparar(bruto)
    assert len(df) == len(bruto) == 4440
    assert set(df["cidade"]) <= set(COORDENADAS), set(df["cidade"]) - set(COORDENADAS)
    salvar_banco(df)
    lido = ler_banco()
    assert len(lido) == len(df) and lido["ocorrencias"].sum() == df["ocorrencias"].sum()
    print(f"OK: {len(lido)} registros gravados em {DB.name}")
