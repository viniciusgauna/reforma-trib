"""ETL: carrega e normaliza as planilhas oficiais da Reforma Tributária (IBS/CBS)
e do NFS-e Nacional usadas pelo painel de consulta.
"""

import json
import re
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent

INDOP_PATH = BASE_DIR / "anexovii-indop_ibscbs_v1-02-00.xlsx"
CORRELACAO_PATH = BASE_DIR / "anexoviii-correlacaoitemnbsindopcclasstrib_ibscbs_v1-01-00(1).xlsx"
NFSE_PATH = BASE_DIR / "anexovi-leiautesrn_rtc_ibscbs-v1-04-00-2013-nt009.xlsx"
CCLASSTRIB_DETALHE_PATH = BASE_DIR / "classificacoes_tributarias.json"

# CST (3 primeiros dígitos do cClassTrib) -> descrição do grupo, conforme o
# Portal da Conformidade Fácil (SVRS/gov.br). Permite derivar o agrupamento
# por CST a partir de qualquer cClassTrib sem precisar de outra tabela.
CST_DESCRICOES = {
    "000": "Tributação integral",
    "010": "Tributação com alíquotas uniformes",
    "011": "Tributação com alíquotas uniformes reduzidas",
    "200": "Alíquota reduzida",
    "220": "Alíquota fixa",
    "221": "Alíquota fixa proporcional",
    "222": "Redução de Base de Cálculo",
    "400": "Isenção",
    "410": "Imunidade e não incidência",
    "510": "Diferimento",
    "515": "Diferimento com redução de alíquota",
    "550": "Suspensão",
    "620": "Tributação Monofásica",
    "800": "Transferência de crédito",
    "810": "Ajuste de IBS na ZFM",
    "811": "Ajustes",
    "820": "Tributação em documento específico",
    "830": "Exclusão da Base de Cálculo",
}


def _fix_mojibake(texto: str) -> str:
    """Corrige texto UTF-8 que foi decodificado como Latin-1 e re-salvo
    (ex.: "SituaÃ§Ãµes" em vez de "Situações"). Common em exports do
    Portal da Conformidade Fácil. Se o texto já estiver correto, o
    round-trip falha e o original é preservado.
    """
    try:
        return texto.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return texto


def _restaurar_bytes_invisiveis_perdidos(texto_bruto: str) -> str:
    """Repara ~32 ocorrências no JSON onde bytes invisíveis do mojibake
    original (NBSP antes de "à ", byte de controle antes de "Á") foram
    achatados em caracteres comuns durante a transcrição manual do arquivo,
    o que quebra o round-trip de `_fix_mojibake` para essas strings
    específicas (ex.: "Ãgua" em vez de "Ãgua" com o byte 0x81 antes do "g",
    que deveria virar "Água"). Sem isso só essas ~32 strings ficam com
    mojibake residual; o restante do arquivo já é corrigido normalmente.
    """
    # "Ã" + espaço ASCII -> restaura o NBSP perdido (Ã§ão etc. não é afetado,
    # pois só casa quando o caractere seguinte é um espaço literal).
    texto_bruto = re.sub("Ã(?=[ ])", "Ã ", texto_bruto)
    # "Ã" + letra ASCII -> restaura o byte de controle perdido (0x81) que
    # precede "gua"/"reas" em "Água"/"Áreas".
    texto_bruto = re.sub("Ã(?=[a-zA-Z])", "Ã", texto_bruto)
    return texto_bruto


@st.cache_data
def load_indop() -> pd.DataFrame:
    """Anexo VII: tabela de indicadores de operação (indOp)."""
    df = pd.read_excel(INDOP_PATH, sheet_name="cIndOp Public", engine="openpyxl")
    df = df.rename(columns={
        "Código indOp": "indop",
        "Tipo de operação": "tipo_operacao",
        "Característica do fornecimento": "caracteristica_fornecimento",
        "Local do fornecimento a ser identificado no DFe": "local_fornecimento_dfe",
        "Dispositivo Legal: LC 214/2025": "dispositivo_legal",
        "Observação": "observacao",
        "indNFe": "ind_nfe",
        "indNFSe": "ind_nfse",
    })
    df["indop"] = df["indop"].astype(str).str.zfill(6)
    return df


@st.cache_data
def load_tabela_geral() -> pd.DataFrame:
    """Anexo VIII: correlação Item LC116 -> NBS -> indOp -> cClassTrib.

    No arquivo original a tabela usa células mescladas para representar a
    hierarquia (um item pode ter vários NBS e/ou cClassTrib). Cada célula
    mesclada só carrega valor na primeira linha do intervalo; como os
    intervalos de mesclagem de cada coluna são independentes entre si, um
    forward-fill coluna a coluna reconstrói exatamente a hierarquia original.
    """
    # dtype=str preserva os códigos textuais (ex.: cClassTrib "000001") sem
    # deixar o pandas reinterpretá-los como número e perder zeros à esquerda.
    df = pd.read_excel(
        CORRELACAO_PATH, sheet_name="tabela geral", engine="openpyxl", dtype=str,
    )
    df = df.rename(columns={
        "Item LC 116": "item_lc116",
        "Descrição Item": "descricao_item",
        "NBS": "nbs",
        "DESCRIÇÃO NBS": "descricao_nbs",
        "PS ONEROSA? (S/N)": "ps_onerosa",
        "ADQ EXTERIOR? (S/N)": "adq_exterior",
        "INDOP": "indop",
        "Local incidência IBS": "local_incidencia_ibs",
        "cClassTrib": "cclasstrib",
        "nome cClassTrib": "nome_cclasstrib",
    })
    fill_cols = [
        "item_lc116", "descricao_item", "nbs", "descricao_nbs",
        "ps_onerosa", "adq_exterior", "indop", "local_incidencia_ibs",
        "cclasstrib", "nome_cclasstrib",
    ]
    df[fill_cols] = df[fill_cols].ffill()
    df["indop"] = df["indop"].str.zfill(6)
    df["cclasstrib"] = df["cclasstrib"].str.zfill(6)
    return df


@st.cache_data
def load_incidencia_issqn() -> pd.DataFrame:
    """Anexo VI, aba MUN.INCID_INFO.SERV.: regras de incidência do ISSQN por
    subitem da lista de serviços (referência complementar).

    O cabeçalho ocupa 4 linhas mescladas; os dados começam na linha 5.
    """
    df = pd.read_excel(
        NFSE_PATH, sheet_name="MUN.INCID_INFO.SERV.",
        header=None, skiprows=4, usecols="A:H", engine="openpyxl",
    )
    df.columns = [
        "codigo_tributacao_nacional",
        "descricao_servico",
        "incidencia_ep",
        "incidencia_lp",
        "incidencia_et",
        "incidencia_edemit",
        "obrigatorio_obra_atvevento",
        "obrigatorio_infocomplem",
    ]
    df = df.dropna(subset=["codigo_tributacao_nacional"]).copy()
    df["codigo_tributacao_nacional"] = (
        df["codigo_tributacao_nacional"].astype(int).astype(str)
    )
    return df


@st.cache_data
def load_classificacoes_tributarias() -> pd.DataFrame:
    """Detalhamento oficial de cada cClassTrib (Portal da Conformidade Fácil
    / SVRS): percentuais de redução de IBS/CBS, indicadores de crédito,
    tipo de alíquota e DFes relacionados.

    Esta é a fonte que falta no Anexo VIII (que só traz código + nome do
    cClassTrib) — o cruzamento das duas é o que dá "lógica e confluência"
    à busca por cClassTrib no painel: o Anexo VIII diz QUAL cClassTrib usar
    para um Item LC116/NBS, esta tabela diz O QUE esse cClassTrib implica
    na prática (redução, crédito, documento fiscal).
    """
    with open(CCLASSTRIB_DETALHE_PATH, "r", encoding="utf-8") as f:
        texto_bruto = f.read()
    registros = json.loads(_restaurar_bytes_invisiveis_perdidos(texto_bruto))

    linhas = []
    for r in registros:
        codigo = r["codigo"]
        dfes = sorted({
            _fix_mojibake(d["sigla"]) for d in r.get("tiposDfeClassificacao", [])
        })
        linhas.append({
            "codigo": codigo,
            "cst": codigo[:3],
            "cst_descricao": CST_DESCRICOES.get(codigo[:3], "Não classificado"),
            "descricao": _fix_mojibake(r["descricao"]),
            "tipo_aliquota": _fix_mojibake(r["tipoAliquota"]),
            "nomenclatura": r["nomenclatura"],
            "tratamento_tributario": _fix_mojibake(r["descricaoTratamentoTributario"]),
            "percentual_reducao_cbs": r["percentualReducaoCbs"],
            "percentual_reducao_ibs_uf": r["percentualReducaoIbsUf"],
            "percentual_reducao_ibs_mun": r["percentualReducaoIbsMun"],
            "possui_reducao": r["possuiPercentualReducao"],
            "incompativel_suspensao": r["incompativelComSuspensao"],
            "exige_grupo_desoneracao": r["exigeGrupoDesoneracao"],
            "credito_cbs_adquirente": r["indicaApropriacaoCreditoAdquirenteCbs"],
            "credito_ibs_adquirente": r["indicaApropriacaoCreditoAdquirenteIbs"],
            "credito_presumido_fornecedor": r["indicaCreditoPresumidoFornecedor"],
            "credito_presumido_adquirente": r["indicaCreditoPresumidoAdquirente"],
            "credito_operacao_antecedente": _fix_mojibake(
                r.get("creditoOperacaoAntecedente") or ""
            ),
            "dfes_relacionados": ", ".join(dfes),
            "data_atualizacao": r["dataAtualizacao"],
        })

    df = pd.DataFrame(linhas)
    df["codigo"] = df["codigo"].astype(str).str.zfill(6)
    return df
