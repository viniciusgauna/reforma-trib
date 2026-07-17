"""Funções puras (sem dependência do Streamlit) usadas pelo painel de
consulta. Isoladas aqui para poderem ser testadas diretamente, sem
precisar rodar a UI inteira via AppTest.
"""

import unicodedata

import pandas as pd

# Acima de ~500 mil caracteres, o mecanismo de regex usado internamente pelo
# pandas/pyarrow para comparação sem diferenciar maiúsculas/minúsculas falha
# com "pattern too large" em vez de simplesmente não encontrar nada. Nenhuma
# busca legítima precisa de mais que isso; o corte evita que uma entrada
# gigante (colada ou enviada direto, contornando o max_chars do widget)
# derrube a página com uma exceção não tratada.
TAMANHO_MAXIMO_BUSCA = 300


def normalizar(texto: str) -> str:
    """Remove acentos (NFKD + descarte de marcas combinantes) para permitir
    busca tolerante: "saude" deve encontrar "saúde"."""
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")


def contains(series: pd.Series, query: str) -> pd.Series:
    """Busca por substring, sem diferenciar maiúsculas/minúsculas nem acentos."""
    query_normalizada = normalizar(query[:TAMANHO_MAXIMO_BUSCA])
    series_normalizada = series.fillna("").map(normalizar)
    return series_normalizada.str.contains(query_normalizada, case=False, na=False, regex=False)


def resumo_reducao(row: pd.Series) -> str:
    """Resume as 3 colunas de percentual de redução (CBS, IBS-UF, IBS-Mun)
    em um único texto, para caber numa tabela estreita em vez de 3 colunas
    separadas."""
    if not row["possui_reducao"]:
        return "—"
    cbs, ibs_uf, ibs_mun = (
        row["percentual_reducao_cbs"],
        row["percentual_reducao_ibs_uf"],
        row["percentual_reducao_ibs_mun"],
    )
    if cbs == ibs_uf == ibs_mun:
        return f"{cbs:.0f}%"
    return f"CBS {cbs:.0f}% · IBS-UF {ibs_uf:.0f}% · IBS-Mun {ibs_mun:.0f}%"
