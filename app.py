"""Painel de consulta da classificação tributária IBS/CBS (Reforma Tributária).

Fontes: Anexo VI (NFS-e Nacional / RTC), Anexo VII (indOp) e Anexo VIII
(correlação Item LC116 x NBS x indOp x cClassTrib) do RTC IBS/CBS.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from data import (
    load_classificacoes_tributarias,
    load_incidencia_issqn,
    load_indop,
    load_tabela_geral,
)
from logic import contains as _contains
from logic import resumo_reducao as _resumo_reducao

st.set_page_config(
    page_title="Classificação Tributária IBS/CBS",
    layout="centered",
)

_PLAIN_CSS_PATH = Path(__file__).resolve().parent / "plain.css"
st.markdown(f"<style>{_PLAIN_CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

st.title("Classificação Tributária IBS/CBS")
st.caption(
    "Consulta a partir dos Anexos VI, VII e VIII do RTC IBS/CBS "
    "(NFS-e Nacional / gov.br)."
)

geral = load_tabela_geral()
indop = load_indop()
issqn = load_incidencia_issqn()
cclasstrib_detalhe = load_classificacoes_tributarias()


COLUMN_LABELS = {
    "item_lc116": "Item da LC 116",
    "descricao_item": "Descrição do Item",
    "nbs": "NBS",
    "descricao_nbs": "Descrição NBS",
    "ps_onerosa": "Prestação de Serviço Onerosa?",
    "adq_exterior": "Aquisição do Exterior?",
    "indop": "Indicador de Operação (indOp)",
    "local_incidencia_ibs": "Local de Incidência do IBS",
    "cclasstrib": "cClassTrib",
    "nome_cclasstrib": "Nome do cClassTrib",
    "tipo_operacao": "Tipo de Operação",
    "caracteristica_fornecimento": "Característica do Fornecimento",
    "local_fornecimento_dfe": "Local do Fornecimento no Documento Fiscal",
    "dispositivo_legal": "Dispositivo Legal",
    "observacao": "Observação",
    "ind_nfe": "Indicador de Nota Fiscal Eletrônica (NFe)",
    "ind_nfse": "Indicador de Nota Fiscal de Serviços Eletrônica (NFSe)",
    "codigo_tributacao_nacional": "Código de Tributação Nacional",
    "descricao_servico": "Descrição do Serviço",
    "incidencia_ep": "Estabelecimento do Prestador",
    "incidencia_lp": "Local da Prestação",
    "incidencia_et": "Estabelecimento do Tomador",
    "incidencia_edemit": "Estabelecimento do Emitente",
    "obrigatorio_obra_atvevento": "Obrigatório: Grupo Obra/Atividade de Evento?",
    "obrigatorio_infocomplem": "Obrigatório: Informações Complementares?",
    "codigo": "cClassTrib",
    "cst": "Código de Situação Tributária (CST)",
    "cst_descricao": "Descrição da Situação Tributária",
    "tipo_aliquota": "Tipo de Alíquota",
    "tratamento_tributario": "Tratamento Tributário",
    "percentual_reducao_cbs": "Redução de CBS (%)",
    "percentual_reducao_ibs_uf": "Redução de IBS Estadual (%)",
    "percentual_reducao_ibs_mun": "Redução de IBS Municipal (%)",
    "possui_reducao": "Possui Redução?",
    "incompativel_suspensao": "Incompatível com Suspensão?",
    "exige_grupo_desoneracao": "Exige Grupo de Desoneração?",
    "credito_cbs_adquirente": "Crédito de CBS para o Adquirente?",
    "credito_ibs_adquirente": "Crédito de IBS para o Adquirente?",
    "credito_presumido_fornecedor": "Crédito Presumido para o Fornecedor?",
    "credito_presumido_adquirente": "Crédito Presumido para o Adquirente?",
    "credito_operacao_antecedente": "Crédito da Operação Antecedente",
    "dfes_relacionados": "Documentos Fiscais Eletrônicos Relacionados",
    "data_atualizacao": "Atualizado em",
    "descricao": "Descrição",
}


def show(df: pd.DataFrame, column_config: dict | None = None) -> None:
    """Exibe um DataFrame com nomes de coluna amigáveis em vez das chaves internas."""
    st.dataframe(
        df.rename(columns=COLUMN_LABELS),
        hide_index=True,
        width="stretch",
        column_config=column_config,
    )


def show_cclasstrib_resumo(df: pd.DataFrame) -> None:
    """Tabela enxuta (poucas colunas, todas estreitas) para navegar entre
    vários cClassTrib de uma vez, sem forçar rolagem horizontal."""
    tabela = df.copy()
    tabela["Redução"] = tabela.apply(_resumo_reducao, axis=1)
    show(
        tabela[["codigo", "cst", "descricao", "Redução"]],
        column_config={
            "cClassTrib": st.column_config.TextColumn(width="small"),
            "Código de Situação Tributária (CST)": st.column_config.TextColumn(width="small"),
            "Descrição": st.column_config.TextColumn(width="large"),
            "Redução": st.column_config.TextColumn(width="medium"),
        },
    )


def show_cclasstrib_cartao(row: pd.Series) -> None:
    """Detalhe completo de um único cClassTrib em layout vertical (rótulo
    em cima, valor embaixo), para ler sem precisar rolar para os lados.
    Não repete código/descrição: quem chama já mostrou isso no expander
    ou no seletor.
    """
    st.caption(f"Código de Situação Tributária {row['cst']} · {row['cst_descricao']}")

    st.write(f"**Tipo de alíquota:** {row['tipo_aliquota']}")
    st.write(f"**Aplicável a:** {row['nomenclatura']}")
    st.write(f"**Tratamento tributário:** {row['tratamento_tributario']}")
    st.write(f"**Redução:** {_resumo_reducao(row)}")

    creditos = []
    if row["credito_cbs_adquirente"]:
        creditos.append("crédito de CBS para o adquirente")
    if row["credito_ibs_adquirente"]:
        creditos.append("crédito de IBS para o adquirente")
    if row["credito_presumido_fornecedor"]:
        creditos.append("crédito presumido para o fornecedor")
    if row["credito_presumido_adquirente"]:
        creditos.append("crédito presumido para o adquirente")
    st.write(f"**Créditos:** {', '.join(creditos) if creditos else 'nenhum'}")
    if row["credito_operacao_antecedente"]:
        st.caption(f"Crédito da operação antecedente: {row['credito_operacao_antecedente']}")

    st.write(f"**Documentos fiscais eletrônicos relacionados:** {row['dfes_relacionados'] or '—'}")

    if row["incompativel_suspensao"]:
        st.caption("⚠️ Incompatível com regime de suspensão.")
    if row["exige_grupo_desoneracao"]:
        st.caption("⚠️ Exige preenchimento do grupo de desoneração no documento fiscal.")

    st.caption(f"Atualizado em {row['data_atualizacao']}")


def selecionar_com_detalhe(
    df: pd.DataFrame,
    col_codigo: str,
    col_descricao: str,
    key: str,
    pergunta: str,
    renderizar_detalhe,
    limite: int = 20,
) -> None:
    """Padrão comum às abas avançadas: a partir de uma lista de resultados
    já exibida em tabela, oferece um seletor para escolher um item e mostra
    o detalhe completo dele num cartão vertical. Evita repetir esse bloco
    em cada aba (indOp, cClassTrib, ISSQN)."""
    if len(df) == 0:
        return
    if len(df) > limite:
        st.caption("Muitos resultados — refine a busca para ver o detalhe completo de um item.")
        return
    opcoes = df.apply(lambda r: f"{r[col_codigo]} — {r[col_descricao]}", axis=1).tolist()
    escolha = st.selectbox(pergunta, opcoes, key=key)
    linha = df.iloc[opcoes.index(escolha)]
    with st.container(border=True):
        renderizar_detalhe(linha)


def _detalhe_indop(linha: pd.Series) -> None:
    st.write(f"**Característica do fornecimento:** {linha['caracteristica_fornecimento']}")
    st.write(f"**Local do fornecimento no documento fiscal eletrônico:** {linha['local_fornecimento_dfe']}")
    st.write(f"**Dispositivo legal:** {linha['dispositivo_legal']}")
    if linha.get("observacao"):
        st.caption(f"Observação: {linha['observacao']}")


def _detalhe_issqn(linha: pd.Series) -> None:
    st.write(f"**Estabelecimento do Tomador:** {linha['incidencia_et']}")
    st.write(f"**Estabelecimento do Emitente:** {linha['incidencia_edemit']}")
    st.write(f"**Obrigatório: Grupo Obra/Atividade de Evento?** {linha['obrigatorio_obra_atvevento']}")
    st.write(f"**Obrigatório: Informações Complementares?** {linha['obrigatorio_infocomplem']}")


query = st.text_input(
    "Descreva o serviço ou informe o código do item LC116 (ex.: 01.01)",
    key="query_servico",
    placeholder="Ex.: análise de sistemas, ou 01.01",
    max_chars=200,
)

if not query:
    st.info("Digite uma palavra-chave ou o código do item para ver a classificação tributária completa.")
else:
    mask = _contains(geral["item_lc116"], query) | _contains(
        geral["descricao_item"], query
    )
    matches = geral[mask]

    itens = (
        matches[["item_lc116", "descricao_item"]]
        .drop_duplicates()
        .sort_values("item_lc116")
    )
    st.write(f"{len(itens)} item(ns) encontrado(s).")

    if len(itens) == 0:
        st.warning("Nenhum item LC116 encontrado para essa busca.")
        fallback_cclasstrib = cclasstrib_detalhe[
            _contains(cclasstrib_detalhe["descricao"], query)
            | _contains(cclasstrib_detalhe["cst_descricao"], query)
        ]
        if not fallback_cclasstrib.empty:
            st.info(
                f"Encontrei {len(fallback_cclasstrib)} cClassTrib com esse termo "
                "na descrição (não associado a nenhum Item LC116 diretamente):"
            )
            show_cclasstrib_resumo(fallback_cclasstrib)
    else:
        opcoes = itens.apply(lambda r: f"{r['item_lc116']} — {r['descricao_item']}", axis=1)
        escolha = st.selectbox("Selecione o item", opcoes, key="select_servico")
        item_selecionado = itens.iloc[opcoes.tolist().index(escolha)]["item_lc116"]

        detalhe = geral[geral["item_lc116"] == item_selecionado]
        primeira = detalhe.iloc[0]

        st.write(f"**Prestação de serviço onerosa?** {primeira['ps_onerosa']}")
        st.write(f"**Aquisição do exterior?** {primeira['adq_exterior']}")
        st.write(f"**Local de incidência do IBS:** {primeira['local_incidencia_ibs']}")

        indop_codigos = detalhe["indop"].drop_duplicates()
        indop_detalhe = indop[indop["indop"].isin(indop_codigos)]
        if not indop_detalhe.empty:
            st.markdown("**Indicador(es) de operação (indOp) associado(s):**")
            for _, linha_indop in indop_detalhe.iterrows():
                with st.expander(f"{linha_indop['indop']} — {linha_indop['tipo_operacao']}"):
                    st.write(f"**Característica do fornecimento:** {linha_indop['caracteristica_fornecimento']}")
                    st.write(f"**Local do fornecimento (DFe):** {linha_indop['local_fornecimento_dfe']}")
                    st.write(f"**Dispositivo legal:** {linha_indop['dispositivo_legal']}")

        st.markdown("**Códigos NBS associados a este item:**")
        show(detalhe[["nbs", "descricao_nbs"]].drop_duplicates())

        st.markdown("**Classificação(ões) tributária(s) (cClassTrib):**")
        codigos_do_item = detalhe["cclasstrib"].drop_duplicates()
        cclasstrib_do_item = cclasstrib_detalhe[
            cclasstrib_detalhe["codigo"].isin(codigos_do_item)
        ]
        if cclasstrib_do_item.empty:
            st.caption("Sem detalhamento adicional disponível para esse(s) cClassTrib.")
        else:
            for _, linha in cclasstrib_do_item.iterrows():
                with st.expander(f"{linha['codigo']} — {linha['descricao']}"):
                    show_cclasstrib_cartao(linha)

st.divider()
busca_avancada = st.expander("Busca avançada (NBS, indOp, cClassTrib, ISSQN)")

with busca_avancada:
    tab_nbs, tab_indop, tab_cclasstrib, tab_issqn = st.tabs([
        "Buscar por NBS",
        "Consultar indOp",
        "Consultar cClassTrib",
        "Incidência do ISSQN",
    ])

with tab_nbs:
    st.subheader("Buscar por código ou descrição NBS")
    query_nbs = st.text_input(
        "Código NBS (ex.: 1.1502.10.00) ou palavra-chave", key="query_nbs", max_chars=200
    )
    if query_nbs:
        mask = _contains(geral["nbs"], query_nbs) | _contains(
            geral["descricao_nbs"], query_nbs
        )
        resultado = geral[mask]
        st.write(f"{len(resultado)} resultado(s).")
        show(
            resultado[[
                "nbs", "descricao_nbs", "item_lc116", "cclasstrib",
            ]].drop_duplicates(),
            column_config={
                "NBS": st.column_config.TextColumn(width="small"),
                "Descrição NBS": st.column_config.TextColumn(width="large"),
                "Item da LC 116": st.column_config.TextColumn(width="small"),
                "cClassTrib": st.column_config.TextColumn(width="small"),
            },
        )
    else:
        st.info("Digite um código NBS ou palavra-chave para buscar.")

with tab_indop:
    st.subheader("Tabela de indicadores de operação (Anexo VII)")
    query_indop = st.text_input(
        "Código indOp ou palavra-chave", key="query_indop", max_chars=200
    )
    if query_indop:
        mask = (
            _contains(indop["indop"], query_indop)
            | _contains(indop["tipo_operacao"], query_indop)
            | _contains(indop["caracteristica_fornecimento"], query_indop)
        )
        resultado_indop = indop[mask]
    else:
        resultado_indop = indop
    st.write(f"{len(resultado_indop)} código(s) indOp.")
    show(resultado_indop[["indop", "tipo_operacao"]])
    selecionar_com_detalhe(
        resultado_indop, "indop", "tipo_operacao", "select_indop_detalhe",
        "Ver detalhes completos de qual indOp?", _detalhe_indop,
    )

with tab_cclasstrib:
    st.subheader("Busca reversa por cClassTrib")
    st.caption(
        "Cruza o detalhamento oficial de cada cClassTrib (Portal da "
        "Conformidade Fácil / SVRS: percentuais de redução, indicadores de "
        "crédito e DFes relacionados) com o Anexo VIII, que mostra em quais "
        "Itens LC116/NBS cada cClassTrib é utilizado."
    )
    query_cclasstrib = st.text_input(
        "Código cClassTrib (ex.: 000001), código CST (ex.: 200) ou palavra-chave na descrição",
        key="query_cclasstrib",
        max_chars=200,
    )
    if query_cclasstrib:
        mask_detalhe = (
            _contains(cclasstrib_detalhe["codigo"], query_cclasstrib)
            | _contains(cclasstrib_detalhe["cst"], query_cclasstrib)
            | _contains(cclasstrib_detalhe["descricao"], query_cclasstrib)
            | _contains(cclasstrib_detalhe["cst_descricao"], query_cclasstrib)
        )
        resultado_detalhe = cclasstrib_detalhe[mask_detalhe]
    else:
        resultado_detalhe = cclasstrib_detalhe

    st.write(f"{len(resultado_detalhe)} código(s) cClassTrib.")
    show_cclasstrib_resumo(resultado_detalhe)
    selecionar_com_detalhe(
        resultado_detalhe, "codigo", "descricao", "select_cclasstrib_detalhe",
        "Ver detalhes completos de qual cClassTrib?", show_cclasstrib_cartao,
    )

    if query_cclasstrib:
        codigos_encontrados = resultado_detalhe["codigo"]
        mask_geral = geral["cclasstrib"].isin(codigos_encontrados) | _contains(
            geral["nome_cclasstrib"], query_cclasstrib
        )
        resultado_geral = geral[mask_geral]
        if resultado_geral.empty:
            st.caption(
                "Nenhum Item LC116/NBS do Anexo VIII usa esse(s) cClassTrib "
                "(pode ser um código de uso restrito a DFe/regime específico)."
            )
        else:
            st.markdown("**Itens LC116 / NBS que usam esse(s) cClassTrib (Anexo VIII):**")
            show(
                resultado_geral[[
                    "item_lc116", "descricao_item", "nbs", "cclasstrib",
                ]].drop_duplicates(),
                column_config={
                    "Item da LC 116": st.column_config.TextColumn(width="small"),
                    "Descrição do Item": st.column_config.TextColumn(width="large"),
                    "NBS": st.column_config.TextColumn(width="small"),
                    "cClassTrib": st.column_config.TextColumn(width="small"),
                },
            )
    else:
        st.info("Digite um código, CST ou palavra-chave para ver o cruzamento com os Itens LC116/NBS.")

with tab_issqn:
    st.subheader("Regras de incidência do ISSQN por subitem (Anexo VI, referência)")
    st.caption(
        "Tabela de referência complementar (não vinculada automaticamente ao "
        "item LC116 acima, pois usa uma codificação própria de tributação "
        "nacional)."
    )
    query_issqn = st.text_input(
        "Código de tributação nacional (ex.: 10101) ou palavra-chave",
        key="query_issqn",
        max_chars=200,
    )
    if query_issqn:
        mask = _contains(
            issqn["codigo_tributacao_nacional"], query_issqn
        ) | _contains(issqn["descricao_servico"], query_issqn)
        resultado_issqn = issqn[mask]
    else:
        resultado_issqn = issqn
    st.write(f"{len(resultado_issqn)} subitem(ns).")
    show(
        resultado_issqn[[
            "codigo_tributacao_nacional", "descricao_servico",
            "incidencia_ep", "incidencia_lp",
        ]],
        column_config={
            "Código de Tributação Nacional": st.column_config.TextColumn(width="small"),
            "Descrição do Serviço": st.column_config.TextColumn(width="large"),
            "Estabelecimento do Prestador": st.column_config.TextColumn(width="medium"),
            "Local da Prestação": st.column_config.TextColumn(width="medium"),
        },
    )

    selecionar_com_detalhe(
        resultado_issqn, "codigo_tributacao_nacional", "descricao_servico", "select_issqn_detalhe",
        "Ver incidências completas de qual subitem?", _detalhe_issqn,
    )

st.divider()
st.caption(
    "Feito por um consultor de SAP MM, com apoio do Claude Code. "
    "Dúvidas, sugestões ou erro encontrado: [LinkedIn](https://www.linkedin.com/in/vgsnts/)."
)

